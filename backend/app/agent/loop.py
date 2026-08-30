from __future__ import annotations

import uuid

from app.brain.provider import ModelProvider
from app.config import settings
from app.models.schemas import ChatResponse, ToolCall
from app.tools.base import ToolRegistry
from app.tools.permissions import PermissionEngine

from .context_manager import ContextManager
from .executor import ApprovalRequired, Executor
from .observer import Observer
from .planner import Planner, PlannerError
from .verifier import Verifier


class AgentLoop:
    """Implements: understand -> plan -> tool -> observe -> reason -> tool ->
    verify -> respond, bounded by settings.max_iterations."""

    def __init__(
        self,
        brain: ModelProvider,
        registry: ToolRegistry,
        context: ContextManager,
        permissions: PermissionEngine | None = None,
    ):
        self.brain = brain
        self.registry = registry
        self.context = context
        self.permissions = permissions or PermissionEngine()
        self.planner = Planner(brain)
        self.executor = Executor(registry, self.permissions)
        self.observer = Observer()
        self.verifier = Verifier(brain)
        # Per-conversation pending approvals, so /approve can resume the right loop.
        self._pending: dict[str, tuple[ToolCall, list[dict[str, str]], str]] = {}

    async def run(self, user_message: str, conversation_id: str | None = None) -> ChatResponse:
        conversation_id = conversation_id or str(uuid.uuid4())
        await self.context.remember_turn(conversation_id, "user", user_message)

        system_prompt = await self.context.system_prompt()
        messages = await self.context.load_messages(conversation_id)

        return await self._drive(conversation_id, system_prompt, messages, user_message)

    async def resume_after_approval(
        self, conversation_id: str, tool_call_id: str, approved: bool
    ) -> ChatResponse:
        pending = self._pending.pop(conversation_id, None)
        if pending is None:
            raise ValueError("No pending approval for this conversation.")
        call, messages, original_request = pending
        if call.id != tool_call_id:
            raise ValueError("tool_call_id does not match the pending approval.")

        system_prompt = await self.context.system_prompt()

        if not approved:
            messages.append(
                {
                    "role": "user",
                    "content": self.observer.format_results(
                        [self._denied_result(call)]
                    ),
                }
            )
            return await self._drive(conversation_id, system_prompt, messages, original_request)

        result = await self.executor.run_single_approved(call)
        messages.append({"role": "user", "content": self.observer.format_results([result])})
        return await self._drive(conversation_id, system_prompt, messages, original_request)

    def _denied_result(self, call: ToolCall):
        from app.models.schemas import ToolResult

        return ToolResult(id=call.id, tool=call.tool, ok=False, error="User denied this action.")

    async def _drive(
        self,
        conversation_id: str,
        system_prompt: str,
        messages: list[dict[str, str]],
        original_request: str,
    ) -> ChatResponse:
        iterations = 0
        while iterations < settings.max_iterations:
            iterations += 1
            try:
                decision = await self.planner.decide(system_prompt, messages)
            except PlannerError as exc:
                # Give the model one chance to self-correct with the error shown back.
                messages.append({"role": "user", "content": f"Your last response was invalid: {exc}. Respond again with valid JSON."})
                continue

            if decision["action"] == "call_tools":
                messages.append(
                    {"role": "assistant", "content": decision.get("thought", "") + " " + str(decision["tool_calls"])}
                )
                try:
                    results = await self.executor.run_batch(decision["tool_calls"])
                except ApprovalRequired as approval:
                    self._pending[conversation_id] = (approval.tool_call, messages, original_request)
                    await self.context.remember_turn(conversation_id, "assistant", "[waiting for approval]")
                    return ChatResponse(
                        conversation_id=conversation_id,
                        reply=f"Waiting for approval to run '{approval.tool_call.tool}' "
                        f"with arguments {approval.tool_call.arguments}.",
                        tool_calls=[],
                        iterations=iterations,
                        status="needs_approval",
                        pending_approval=approval.tool_call,
                    )
                messages.append({"role": "user", "content": self.observer.format_results(results)})
                continue

            # action == "final_answer"
            answer = decision["answer"]
            satisfied, reason = await self.verifier.check(original_request, answer, messages)
            if satisfied or iterations >= settings.max_iterations:
                await self.context.remember_turn(conversation_id, "assistant", answer)
                await self.context.remember_outcome(
                    conversation_id, f"Request: {original_request!r} -> {answer[:200]!r}"
                )
                return ChatResponse(
                    conversation_id=conversation_id,
                    reply=answer,
                    tool_calls=[],
                    iterations=iterations,
                    status="completed",
                )
            messages.append(
                {
                    "role": "user",
                    "content": f"Verifier rejected that answer: {reason}. Try again, "
                    "using more tool calls if needed.",
                }
            )

        return ChatResponse(
            conversation_id=conversation_id,
            reply="I couldn't complete this within the iteration limit. Here's what I found so far — "
            "consider narrowing the request.",
            tool_calls=[],
            iterations=iterations,
            status="max_iterations_reached",
        )
