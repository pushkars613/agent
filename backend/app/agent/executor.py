from __future__ import annotations

import uuid
from typing import Any

from app.models.schemas import ToolCall, ToolResult
from app.tools.base import ToolRegistry
from app.tools.permissions import PermissionEngine


class ApprovalRequired(Exception):
    def __init__(self, tool_call: ToolCall):
        self.tool_call = tool_call
        super().__init__(f"Approval required for {tool_call.tool}")


class Executor:
    def __init__(self, registry: ToolRegistry, permissions: PermissionEngine):
        self.registry = registry
        self.permissions = permissions

    async def run_batch(self, raw_calls: list[dict[str, Any]]) -> list[ToolResult]:
        """Run each requested tool call in order. Raises ApprovalRequired on the
        first call that needs sign-off, so the caller can pause the loop."""
        results: list[ToolResult] = []
        for raw in raw_calls:
            call = ToolCall(id=str(uuid.uuid4()), tool=raw["tool"], arguments=raw.get("arguments", {}))
            tool = self.registry.get(call.tool)
            if tool is None:
                results.append(
                    ToolResult(id=call.id, tool=call.tool, ok=False, error=f"Unknown tool '{call.tool}'")
                )
                continue

            if self.permissions.requires_approval(tool.permission_level, call.id):
                raise ApprovalRequired(call)

            try:
                output = await tool.run(**call.arguments)
                results.append(ToolResult(id=call.id, tool=call.tool, ok=True, output=output))
            except Exception as exc:  # noqa: BLE001
                results.append(ToolResult(id=call.id, tool=call.tool, ok=False, error=str(exc)))
        return results

    async def run_single_approved(self, call: ToolCall) -> ToolResult:
        self.permissions.grant(call.id)
        tool = self.registry.get(call.tool)
        if tool is None:
            return ToolResult(id=call.id, tool=call.tool, ok=False, error=f"Unknown tool '{call.tool}'")
        try:
            output = await tool.run(**call.arguments)
            return ToolResult(id=call.id, tool=call.tool, ok=True, output=output)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(id=call.id, tool=call.tool, ok=False, error=str(exc))
