from __future__ import annotations

import asyncio

from app.config import settings
from app.models.schemas import PermissionLevel
from .base import Tool


async def _git(*args: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "git",
        *args,
        cwd=str(settings.workspace_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    text = stdout.decode(errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{text}")
    return text


class GitStatus(Tool):
    name = "git_status"
    description = "Show git status of the workspace repo."
    permission_level = PermissionLevel.READ
    parameters = {}

    async def run(self, **_: object) -> str:
        return await _git("status", "--short", "--branch")


class GitDiff(Tool):
    name = "git_diff"
    description = "Show unstaged (or staged, if staged=true) git diff."
    permission_level = PermissionLevel.READ
    parameters = {"staged": "bool, optional, default false"}

    async def run(self, staged: bool = False, **_: object) -> str:
        args = ["diff"] + (["--staged"] if staged else [])
        return await _git(*args) or "No differences."


class GitLog(Tool):
    name = "git_log"
    description = "Show recent commit log."
    permission_level = PermissionLevel.READ
    parameters = {"count": "int, optional, default 10"}

    async def run(self, count: int = 10, **_: object) -> str:
        return await _git("log", f"-{count}", "--oneline")


class GitBranch(Tool):
    name = "git_branch"
    description = "Create (and switch to) a new git branch."
    permission_level = PermissionLevel.SAFE
    parameters = {"branch_name": "string"}

    async def run(self, branch_name: str, **_: object) -> str:
        return await _git("checkout", "-b", branch_name)


class GitCommit(Tool):
    name = "git_commit"
    description = "Stage all changes and commit with a message."
    permission_level = PermissionLevel.SENSITIVE
    parameters = {"message": "string"}

    async def run(self, message: str, **_: object) -> str:
        await _git("add", "-A")
        return await _git("commit", "-m", message)


class GitPush(Tool):
    name = "git_push"
    description = "Push the current branch to its remote."
    permission_level = PermissionLevel.DANGEROUS
    parameters = {"remote": "string, optional, default origin", "branch": "string, optional"}

    async def run(self, remote: str = "origin", branch: str | None = None, **_: object) -> str:
        args = ["push", remote]
        if branch:
            args.append(branch)
        return await _git(*args)
