from __future__ import annotations

from enum import IntEnum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class PermissionLevel(IntEnum):
    READ = 0
    SAFE = 1
    SENSITIVE = 2
    DANGEROUS = 3


class ToolCall(BaseModel):
    id: str
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    id: str
    tool: str
    ok: bool
    output: str = ""
    error: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    tool_calls: list[ToolResult] = Field(default_factory=list)
    iterations: int
    status: Literal["completed", "needs_approval", "max_iterations_reached"]
    pending_approval: Optional[ToolCall] = None


class ApprovalDecision(BaseModel):
    conversation_id: str
    tool_call_id: str
    approved: bool
