from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.schemas import PermissionLevel


class Tool(ABC):
    name: str
    description: str
    permission_level: PermissionLevel
    # JSON-schema-ish parameter description shown to the model in the prompt.
    parameters: dict[str, Any] = {}

    @abstractmethod
    async def run(self, **kwargs: Any) -> str:
        """Execute the tool and return a string result (or raise)."""
        raise NotImplementedError

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "permission_level": int(self.permission_level),
            "parameters": self.parameters,
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def schemas(self) -> list[dict[str, Any]]:
        return [t.schema() for t in self._tools.values()]
