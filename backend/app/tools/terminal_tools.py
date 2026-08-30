from __future__ import annotations

import asyncio
import shlex

from app.config import settings
from app.models.schemas import PermissionLevel
from .base import Tool

# Commands that are always treated as Dangerous regardless of level checks
# elsewhere, as a defense-in-depth belt-and-suspenders check.
_DANGEROUS_PREFIXES = ("rm -rf", "sudo", "mkfs", "dd if=", ":(){", "shutdown", "reboot")


class RunCommand(Tool):
    name = "run_command"
    description = (
        "Run a shell command inside the workspace directory (e.g. npm test, "
        "pytest, python script.py). Long-running/interactive commands are not supported."
    )
    permission_level = PermissionLevel.SENSITIVE
    parameters = {"command": "string", "timeout_seconds": "int, optional, default 60"}

    async def run(self, command: str, timeout_seconds: int = 60, **_: object) -> str:
        lowered = command.strip().lower()
        if any(lowered.startswith(p) for p in _DANGEROUS_PREFIXES):
            raise PermissionError(
                f"Command '{command}' matches a Dangerous pattern and is blocked "
                "by this build. Dangerous-tier execution is not enabled."
            )
        try:
            shlex.split(command)
        except ValueError as exc:
            raise ValueError(f"Could not parse command: {exc}") from exc

        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(settings.workspace_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            proc.kill()
            raise TimeoutError(f"Command timed out after {timeout_seconds}s") from None

        output = stdout.decode(errors="replace")
        status = "OK" if proc.returncode == 0 else f"EXIT {proc.returncode}"
        return f"[{status}]\n{output[-8000:]}"
