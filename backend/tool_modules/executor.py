from backend.core.tool_runner import runner

TOOL_COMMANDS = {
    "nmap":    ["nmap"],
    "nikto":   ["perl", "/opt/nikto/program/nikto.pl"],
    "tcpdump": ["tcpdump"],
    "sqlmap":  ["python3", "/opt/sqlmap/sqlmap.py"],
    "hydra":   ["hydra"],
    "john":    ["john"],
    "hashcat": ["hashcat", "--force"],
    "rsf":     ["python3", "/opt/routersploit/rsf.py"],
    "burp":    ["xvfb-run", "-a", "java", "-jar", "/opt/BurpSuiteCommunity.jar"],
    "msf":     ["msfconsole", "-q", "-x"],
}

def build_command(tool: str, args: list[str]) -> list[str]:
    base = list(TOOL_COMMANDS[tool])
    if tool == "msf" and args:
        return base + [" ".join(args)]
    return base + [a for a in args if a]

async def execute(request_id: int, tool: str, args: list[str]) -> str:
    return await runner.run(request_id, build_command(tool, args))
