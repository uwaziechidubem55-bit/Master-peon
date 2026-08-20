# Master peon - Penetration & AI Navigator
# Terminal Router — Full real shell execution with tool tier enforcement
# Copyright (C) 2026 UWAZIE DANIEL CHIDUBEM
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import json
import os
import shlex
import subprocess
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

# Working directory for terminal sessions
WORK_DIR = Path("/app/data/terminal")
SCANS_DIR = Path("/app/data/scans")

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
    "burp": [
        {"label": "Launch Burp Suite",           "cmd": "burpsuite"},
    ],
    "rsf": [
        {"label": "Launch RouterSploit",         "cmd": "rsf"},
    ],
    "pspy": [
        {"label": "Run pspy process monitor",    "cmd": "pspy"},
    ],
    "winpeas": [
        {"label": "Run WinPEAS",                 "cmd": "winpeas"},
    ],
}


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


def get_tool_name(cmd_line: str):
    """Extract the base tool name if it matches a known pentesting tool."""
    first_word = cmd_line.strip().split()[0].lower() if cmd_line.strip() else ""
    if first_word in TOOL_COMMANDS:
        return first_word
    return None


@router.post("/run")
async def run_terminal(
    body: TerminalCommand,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute ANY command in a real bash shell.
    
    - If the command is a known pentesting tool → checked against tier permission
    - Everything else → runs unrestricted (git, apt, pip, curl, python3, etc.)
    """
    cmd_line = body.command.strip()
    if not cmd_line:
        raise HTTPException(400, "Empty command")

    # Ensure working directory exists
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    # Check if this is a known pentesting tool
    tool_name = get_tool_name(cmd_line)
    is_tool = tool_name is not None

    if is_tool:
        # Tier permission check
        allowed_tools = get_user_tools(user)
        if tool_name not in allowed_tools:
            raise HTTPException(
                403, 
                f"❌ '{tool_name}' is not available on your tier ({user.tier}).\n"
                f"Your tier allows: {', '.join(sorted(allowed_tools)) or 'none'}\n"
                "Upgrade your plan to unlock more pentesting tools."
            )

        # Tool call limit check
        t = settings.tier_limits.get(user.tier, {})
        tlimit = t.get("tool_calls", 0)
        if tlimit and user.tool_calls_today >= tlimit:
            raise HTTPException(
                429, 
                f"❌ Daily tool-call limit ({tlimit}) reached for {user.tier} tier."
            )

        # Build the tool command using the executor
        parts = shlex.split(cmd_line)
        full_cmd = build_command(tool_name, parts[1:])

        # Increment tool counter
        user.tool_calls_today += 1
        db.commit()

        # Execute
        out_file = SCANS_DIR / f"terminal_{user.id}_{tool_name}_{os.urandom(4).hex()}.log"
        SCANS_DIR.mkdir(parents=True, exist_ok=True)

        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(WORK_DIR),
        )

        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=600)
        except asyncio.TimeoutError:
            proc.kill()
            stdout, _ = await proc.communicate()
            stdout += b"\n\n[!] Command timed out after 600s — process killed."

        out_file.write_bytes(stdout)
        output = stdout.decode(errors="replace")

        return {
            "ok": True,
            "tool": tool_name,
            "command": cmd_line,
            "output": output[-100000:],
            "exit_code": proc.returncode or 0,
            "log_file": str(out_file),
        }

    # ===== GENERAL / UNRESTRICTED COMMAND =====
    # ANY bash command runs here: git clone, apt install, pip install, 
    # curl, wget, python3, bash scripts, pipes, redirects, variables, etc.
    # The command is executed via `/bin/sh -c` for full shell support.

    if user.tier == "free":
        # Free tier: general commands only, no destructive ones
        free_denied = {"apt", "apt-get", "dpkg", "pip", "pip3", "npm", "git"}
        first_word = cmd_line.strip().split()[0].lower() if cmd_line.strip() else ""
        if first_word in free_denied:
            raise HTTPException(
                403,
                f"❌ '{first_word}' requires at least Pro tier.\n"
                "Free tier is limited to basic read-only commands (ls, cat, pwd, etc.)."
            )

    # Execute via /bin/sh -c for full shell feature support (pipes, redirects, vars)
    proc = await asyncio.create_subprocess_exec(
        "/bin/sh", "-c", cmd_line,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(WORK_DIR),
        env={**os.environ, "HOME": str(WORK_DIR)},
    )

    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
    except asyncio.TimeoutError:
        proc.kill()
        stdout, _ = await proc.communicate()
        stdout += b"\n\n[!] Command timed out after 300s — process killed."

    output = stdout.decode(errors="replace")

    return {
        "ok": True,
        "tool": None,
        "command": cmd_line,
        "output": output[-100000:],
        "exit_code": proc.returncode or 0,
    }


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
        "tool_count": len(result),
        "tools": result,
    }


@router.get("/help")
def help_text():
    """Return full help info for the terminal."""
    return {
        "info": "Master Peon Real Terminal — executes any command via /bin/sh",
        "tool_count": len(TOOL_COMMANDS),
        "tools_with_generators": list(TOOL_COMMAND_GENERATORS.keys()),
        "builtin_commands": [
            {"cmd": "clear",     "desc": "Clear the terminal screen"},
            {"cmd": "help",      "desc": "Show this help message"},
            {"cmd": "history",   "desc": "Show command history"},
            {"cmd": "tools",     "desc": "List available security tools for your tier"},
            {"cmd": "generate <tool>",  "desc": "Show command templates for a tool"},
        ],
    }