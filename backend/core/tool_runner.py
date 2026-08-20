# Master peon - Penetration & AI Navigator
# Copyright (C) 2026 UWAZIE DANIEL CHIDUBEM 
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
from pathlib import Path

SCANS_DIR = Path("/app/data/scans")

class ToolRunner:
    async def run(self, request_id: int, command: list[str], timeout: int = 600) -> str:
        SCANS_DIR.mkdir(parents=True, exist_ok=True)
        proc = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            stdout, _ = await proc.communicate()
            stdout += b"\n[KILLED: timed out]"
        out_file = SCANS_DIR / f"request_{request_id}.log"
        out_file.write_bytes(stdout)
        return stdout.decode(errors="replace")

runner = ToolRunner()
