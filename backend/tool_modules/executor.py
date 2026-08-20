from backend.core.tool_runner import runner

TOOL_COMMANDS = {
    "nmap":      ["nmap"],
    "nikto":     ["nikto"],
    "sqlmap":    ["sqlmap"],
    "hydra":     ["hydra"],
    "john":      ["john"],
    "hashcat":   ["hashcat", "--force"],
    "tcpdump":   ["tcpdump"],
    "dirb":      ["dirb"],
    "ffuf":      ["ffuf"],
    "whatweb":   ["whatweb"],
    "sublist3r": ["sublist3r"],
    "netcat":    ["nc"],
    "tshark":    ["tshark"],
    "whois":     ["whois"],
    "medusa":    ["medusa"],
    "crunch":    ["crunch"],
    "rsf":       ["python3", "/opt/routersploit/rsf.py"],
    "burp":      ["burpsuite"],
    "msf":       ["msfconsole", "-q", "-x"],
    "netdiscover": ["netdiscover", "-P"]
}

def build_command(tool: str, args: list[str]) -> list[str]:
    base = list(TOOL_COMMANDS[tool])
    if tool == "msf" and args:
        return base + [" ".join(args)]
    return base + [a for a in args if a]

async def execute(request_id: int, tool: str, args: list[str]) -> str:
    return await runner.run(request_id, build_command(tool, args))
