from __future__ import annotations

from .base import ToolRegistry
from .file_tools import (
    EditFile,
    ListFiles,
    ReadFile,
    SearchFiles,
    WriteFile,
)
from .git_tools import (
    GitBranch,
    GitCommit,
    GitDiff,
    GitLog,
    GitPush,
    GitStatus,
)
from .terminal_tools import RunCommand


def build_default_registry() -> ToolRegistry:

    registry = ToolRegistry()

    tools = (
        # Files
        ListFiles,
        ReadFile,
        SearchFiles,
        WriteFile,
        EditFile,

        # Terminal
        RunCommand,

        # Git
        GitStatus,
        GitDiff,
        GitLog,
        GitBranch,
        GitCommit,
        GitPush,
    )

    for tool_cls in tools:
        registry.register(tool_cls())

    return registry


default_registry = build_default_registry()