# Master peon - Penetration & AI Navigator
# Terminal Router — Real shell execution with tier enforcement
# Copyright (C) 2026 UWAZIE DANIEL CHIDUBEM
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import json
import shlex
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config.database import get_db
from config.settings import settings
from backend import models
from backend.auth import get_current_user
from backend.tool_modules.executor import TOOL_COMMANDS, build_command

router = APIRouter(prefix="/api/terminal", tags=["terminal"])

# General Linux commands allowed for all users (non-tool)
ALLOWED_GENERAL_COMMANDS = {
    "ls", "cat", "head", "tail", "less", "more", "echo", "pwd", "whoami",
    "id", "date", "cal", "df", "du", "free", "uptime", "uname", "hostname",
    "ip", "ss", "ps", "top", "which", "whereis", "find", "grep", "sort",
    "wc", "cut", "tr", "base64", "md5sum", "sha256sum", "clear", "help",
    "history", "env", "printenv", "lsblk", "lscpu", "lsusb", "lspci",
    "dmesg", "who", "w", "last", "finger", "file", "stat", "tree",
    "mkdir", "touch", "cp", "mv", "rm", "ln", "chmod", "chown",
    "tar", "gzip", "gunzip", "zip", "unzip", "diff", "cmp",
}

# Tools available per tier
TIER_TOOL_MAP = {
    "free":   {"nmap", "nikto", "tcpdump"},
    "pro":    {"nmap", "nikto", "tcpdump", "hydra", "john"},
    "advance": {"nmap", "nikto", "tcpdump", "hydra", "john", "sqlmap", "dirb", "ffuf"},
    "master":  "ALL",
}

# Custom command generators per tool
TOOL_COMMAND_GENERATORS = {
    "nmap": [
        {"label": "Quick scan (top ports)",      "cmd": "nmap -sV {target}"},
        {"label": "Default scripts",             "cmd": "nmap -sC {target}"},
        {"label": "All ports scan",              "cmd": "nmap -p- {target}"},
        {"label": "Aggressive scan",             "cmd": "nmap -A {target}"},
        {"label": "OS detection",                "cmd": "nmap -O {target}"},
        {"label": "Ping sweep (subnet)",         "cmd": "nmap -sn {subnet}"},
        {"label": "UDP scan",                    "cmd": "nmap -sU {target}"},
        {"label": "Vulnerability scripts",       "cmd": "nmap --script vuln {target}"},
    ],
    "nikto": [
        {"label": "Basic web scan",              "cmd": "nikto -h {target}"},
        {"label": "SSL web scan",                "cmd": "nikto -h {target} -ssl"},
        {"label": "Specific port",               "cmd": "nikto -h {target} -port {port}"},
    ],
    "sqlmap": [
        {"label": "Basic injection test",        "cmd": "sqlmap -u {url}"},
        {"label": "List databases",              "cmd": "sqlmap -u {url} --dbs"},
        {"label": "List tables",                 "cmd": "sqlmap -u {url} -D {database} --tables"},
        {"label": "Dump table",                  "cmd": "sqlmap -u {url} -D {database} -T {table} --dump"},
    ],
    "hydra": [
        {"label": "SSH brute force",             "cmd": "hydra -l {username} -P {wordlist} {target} ssh"},
        {"label": "FTP brute force",             "cmd": "hydra -L {userlist} -P {wordlist} {target} ftp"},
        {"label": "HTTP POST form",              "cmd": "hydra -L {userlist} -P {wordlist} {target} http-post-form {path}"},
        {"label": "RDP brute force",             "cmd": "hydra -l {username} -P {wordlist} rdp://{target}"},
    ],
    "john": [
        {"label": "Crack hash (auto-detect)",    "cmd": "john {hashfile}"},
        {"label": "Crack with wordlist",         "cmd": "john --wordlist={wordlist} {hashfile}"},
        {"label": "Show cracked passwords",      "cmd": "john --show {hashfile}"},
        {"label": "Incremental mode",            "cmd": "john --incremental {hashfile}"},
    ],
    "hashcat": [
        {"label": "MD5 crack",                   "cmd": "hashcat -m 0 -a 0 {hashfile} {wordlist}"},
        {"label": "SHA256 crack",                "cmd": "hashcat -m 1400 -a 0 {hashfile} {wordlist}"},
        {"label": "NTLM crack",                  "cmd": "hashcat -m 1000 -a 0 {hashfile} {wordlist}"},
        {"label": "Brute force (all chars)",     "cmd": "hashcat -a 3 {hashfile} ?a?a?a?a?a?a?a?a"},
    ],
    "tcpdump": [
        {"label": "Capture all on interface",    "cmd": "tcpdump -i {interface}"},
        {"label": "Capture HTTP traffic",        "cmd": "tcpdump -i {interface} port 80"},
        {"label": "Capture with output file",    "cmd": "tcpdump -i {interface} -w {output}.pcap"},
        {"label": "Read pcap file",              "cmd": "tcpdump -r {file}.pcap"},
    ],
    "dirb": [
        {"label": "Basic directory scan",        "cmd": "dirb {url}"},
        {"label": "Custom wordlist",             "cmd": "dirb {url} {wordlist}"},
    ],
    "ffuf": [
        {"label": "Directory fuzzing",           "cmd": "ffuf -u {url}/FUZZ -w {wordlist}"},
        {"label": "Subdomain fuzzing",           "cmd": "ffuf -u https://FUZZ.{domain} -w {wordlist}"},
        {"label": "Parameter fuzzing (POST)",    "cmd": "ffuf -u {url} -X POST -d 'FUZZ=test' -w {wordlist}"},
    ],
    "whatweb": [
        {"label": "Basic fingerprint",           "cmd": "whatweb {url}"},
        {"label": "Aggressive detection",        "cmd": "whatweb -a 3 {url}"},
    ],
    "sublist3r": [
        {"label": "Enumerate subdomains",        "cmd": "sublist3r -d {domain}"},
        {"label": "Bruteforce subdomains",       "cmd": "sublist3r -d {domain} -b"},
    ],
    "netcat": [
        {"label": "Port scan",                   "cmd": "nc -zv {target} {ports}"},
        {"label": "Listen on port",              "cmd": "nc -lvnp {port}"},
        {"label": "Send file",                   "cmd": "nc -w 3 {target} {port} < {file}"},
    ],
    "tshark": [
        {"label": "Capture live",                "cmd": "tshark -i {interface}"},
        {"label": "Filter HTTP",                 "cmd": "tshark -i {interface} -Y http"},
        {"label": "Read pcap",                   "cmd": "tshark -r {file}.pcap"},
    ],
    "whois": [
        {"label": "Domain lookup",               "cmd": "whois {domain}"},
        {"label": "IP lookup",                   "cmd": "whois {ip}"},
    ],
    "medusa": [
        {"label": "SSH brute",                   "cmd": "medusa -h {target} -u {username} -P {wordlist} -M ssh"},
        {"label": "FTP brute",                   "cmd": "medusa -h {target} -U {userlist} -P {wordlist} -M ftp"},
    ],
    "crunch": [
        {"label": "Generate wordlist (min max)", "cmd": "crunch {min} {max} {charset} -o {output}"},
        {"label": "Crack pattern",               "cmd": "crunch {min} {max} -t {pattern} -o {output}"},
    ],
    "chisel": [
        {"label": "Client tunnel",               "cmd": "chisel client {server}:{port} {remote}"},
        {"label": "Server (reverse)",            "cmd": "chisel server -p {port} --reverse"},
    ],
    "ligolo": [
        {"label": "Agent connect",               "cmd": "ligolo -connect {server}:{port}"},
    ],
    "linpeas": [
        {"label": "Run linpeas",                 "cmd": "linpeas"},
        {"label": "Run with extras",             "cmd": "linpeas -a"},
    ],
    "msf": [
        {"label": "Console (interactive)",       "cmd": "msfconsole"},
        {"label": "Run resource script",         "cmd": "msfconsole -q -r {script}.rc"},
    ],
    "netdiscover": [
        {"label": "ARP scan subnet",             "cmd": "netdiscover -r {subnet}"},
        {"label": "Passive discovery",           "cmd": "netdiscover -p"},
    ],
}

SCANS_DIR = Path("/app/data/scans")
WORK_DIR = Path("/tmp/terminal-sessions")


class TerminalCommand(BaseModel):
    command: str
    cwd: str = ""


def get_user_tools(user: models.User) -> set:
    """Return the set of tool names the user's tier allows."""
    t = settings.tier_limits.get(user.tier, {})
    tools = t.get("tools", [])
    if isinstance(tools, list) and tools == ["ALL"]:
        return set(TOOL_COMMANDS.keys())
    return set(tools)


def is_general_command(cmd: str) -> bool:
    """Check if a command is a known general Linux command."""
    parts = cmd.strip().split()
    if not parts:
        return False
    base = parts[0].lstrip("./")
    # Allow full paths
    if "/" in base:
        return True
    return base in ALLOWED_GENERAL_COMMANDS


@router.post("/run")
async def run_terminal(
    body: TerminalCommand,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cmd_line = body.command.strip()
    if not cmd_line:
        raise HTTPException(400, "Empty command")

    parts = shlex.split(cmd_line)
    base_cmd = parts[0].lower()

    # --- Check if it's a known pentesting tool ---
    if base_cmd in TOOL_COMMANDS:
        # Check tier permission
        allowed_tools = get_user_tools(user)
        if base_cmd not in allowed_tools:
            raise HTTPException(403, f"Tool '{base_cmd}' not allowed on your tier ({user.tier}). Upgrade to access it.")

        # Check tool call limit
        t = settings.tier_limits.get(user.tier, {})
        tlimit = t.get("tool_calls", 0)
        if tlimit and user.tool_calls_today >= tlimit:
            raise HTTPException(429, "Daily tool-call limit reached for your tier")

        # Build the command
        full_cmd = build_command(base_cmd, parts[1:])

        # Execute
        user.tool_calls_today += 1
        db.commit()

        out_file = SCANS_DIR / f"terminal_{user.id}_{base_cmd}.log"
        SCANS_DIR.mkdir(parents=True, exist_ok=True)

        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(WORK_DIR) if WORK_DIR.exists() else "/tmp",
        )

        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=600)
        except asyncio.TimeoutError:
            proc.kill()
            stdout, _ = await proc.communicate()
            stdout += b"\n\n[!] Command timed out after 600s — killed."

        out_file.write_bytes(stdout)
        output = stdout.decode(errors="replace")
        return {
            "ok": True,
            "tool": base_cmd,
            "command": cmd_line,
            "output": output[-50000:],  # last 50KB
            "exit_code": proc.returncode or 0,
        }

    # --- Check if it's an allowed general command ---
    elif is_general_command(cmd_line):
        # Execute the raw shell command with a safe allowlist
        # Master tier gets full shell; others get restricted
        SAFE_GENERAL = {"cp", "mv", "rm", "mkdir", "touch", "chmod", "chown",
                        "tar", "gzip", "gunzip", "zip", "unzip"}

        if user.tier != "master" and base_cmd in SAFE_GENERAL:
            # Destructive commands only for master
            raise HTTPException(403, f"Command '{base_cmd}' requires Master tier")
        
        if user.tier != "master" and base_cmd in ("rm", "mv") and any(
            "/" in p or ".." in p for p in parts[1:]
        ):
            raise HTTPException(403, "Path traversal not allowed — upgrade to Master for full access")

        proc = await asyncio.create_subprocess_exec(
            *parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(WORK_DIR) if WORK_DIR.exists() else "/tmp",
        )

        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            proc.kill()
            stdout, _ = await proc.communicate()
            stdout += b"\n\n[!] Command timed out after 120s — killed."

        output = stdout.decode(errors="replace")
        return {
            "ok": True,
            "tool": base_cmd,
            "command": cmd_line,
            "output": output[-50000:],
            "exit_code": proc.returncode or 0,
        }

    else:
        # Unknown command
        from difflib import get_close_matches
        all_tools = list(TOOL_COMMANDS.keys()) + list(ALLOWED_GENERAL_COMMANDS)
        suggestions = get_close_matches(base_cmd, all_tools, n=5, cutoff=0.4)
        msg = f"Unknown command: '{base_cmd}'."
        if suggestions:
            msg += f" Did you mean: {', '.join(suggestions)}?"
        msg += "\nType 'help' for available commands."
        raise HTTPException(400, msg)


@router.get("/tools")
def list_tools(user=Depends(get_current_user)):
    """Return tools available to the user + their command generators."""
    allowed_tools = get_user_tools(user)
    result = {}
    for tool in sorted(allowed_tools):
        info = {"name": tool}
        if tool in TOOL_COMMAND_GENERATORS:
            info["generators"] = TOOL_COMMAND_GENERATORS[tool]
        else:
            info["generators"] = []
        result[tool] = info
    return {
        "tier": user.tier,
        "tools": result,
    }


@router.get("/help")
def help_text():
    """Return full help info for the terminal."""
    return {
        "general_commands": sorted(ALLOWED_GENERAL_COMMANDS),
        "tool_commands": {
            tool: {
                "description": f"{tool} — Kali Linux security tool",
                "generators": TOOL_COMMAND_GENERATORS.get(tool, []),
            }
            for tool in sorted(TOOL_COMMANDS.keys())
        },
        "builtin_commands": [
            {"cmd": "clear",     "desc": "Clear the terminal screen"},
            {"cmd": "help",      "desc": "Show this help message"},
            {"cmd": "history",   "desc": "Show command history"},
            {"cmd": "tools",     "desc": "List available security tools"},
            {"cmd": "generate",  "desc": "Show command generators for a tool: generate <toolname>"},
        ],
    }