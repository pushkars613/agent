"""
Phase 3: permission engine.

Level 0 Read       — may execute automatically
Level 1 Safe       — may auto-execute, or optionally ask (config-driven)
Level 2 Sensitive  — always require confirmation
Level 3 Dangerous  — always require explicit confirmation

Every tool declares its own level in `Tool.permission_level`. This engine is
the single choke point: nothing in app/tools/*.py should ever run without
going through PermissionEngine.check() first — enforced by ToolRegistry.
"""
from __future__ import annotations

from app.config import settings
from app.models.schemas import PermissionLevel


class PermissionDenied(Exception):
    """Raised when a call is blocked pending approval."""


class PermissionEngine:
    def __init__(self, auto_approve_safe: bool | None = None):
        self.auto_approve_safe = (
            settings.auto_approve_safe if auto_approve_safe is None else auto_approve_safe
        )
        # Approvals granted for this process's lifetime, keyed by tool_call id.
        self._approved: set[str] = set()

    def grant(self, tool_call_id: str) -> None:
        self._approved.add(tool_call_id)

    def requires_approval(self, level: PermissionLevel, tool_call_id: str) -> bool:
        if tool_call_id in self._approved:
            return False
        if level == PermissionLevel.READ:
            return False
        if level == PermissionLevel.SAFE:
            return not self.auto_approve_safe
        # SENSITIVE and DANGEROUS always require approval unless already granted.
        return True

    def describe(self, level: PermissionLevel) -> str:
        return {
            PermissionLevel.READ: "read-only",
            PermissionLevel.SAFE: "safe / reversible",
            PermissionLevel.SENSITIVE: "sensitive — requires confirmation",
            PermissionLevel.DANGEROUS: "dangerous — requires explicit confirmation",
        }[level]
