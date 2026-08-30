from __future__ import annotations

import json

from app.models.schemas import ToolResult


class Observer:
    """Turns tool results into a message the model can reason over next turn."""

    def format_results(self, results: list[ToolResult]) -> str:
        payload = [
            {
                "tool": r.tool,
                "ok": r.ok,
                "output": r.output if r.ok else None,
                "error": r.error if not r.ok else None,
            }
            for r in results
        ]
        return "Tool results:\n" + json.dumps(payload, indent=2)

    def any_errors(self, results: list[ToolResult]) -> bool:
        return any(not r.ok for r in results)
