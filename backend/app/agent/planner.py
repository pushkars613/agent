from __future__ import annotations

import json
from typing import Any

from app.brain.provider import ModelProvider


class PlannerError(Exception):
    pass


class Planner:
    """Turns conversation context into a structured agent decision.

    The planner enforces a tool-first workflow for workspace-related
    requests. This prevents the model from answering from memory or
    hallucinating project information.
    """

    def __init__(self, brain: ModelProvider):
        self.brain = brain

    async def decide(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:

        raw = await self.brain.complete(
            system_prompt,
            messages,
            json_mode=True,
        )

        try:
            decision = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PlannerError(
                f"Model did not return valid JSON: {raw!r}"
            ) from exc

        if not isinstance(decision, dict):
            raise PlannerError(
                f"Model response must be a JSON object: {decision!r}"
            )

        action = decision.get("action")

        if action not in ("call_tools", "final_answer"):
            raise PlannerError(
                f"Unknown or missing action: {decision!r}"
            )

        if action == "call_tools":
            tool_calls = decision.get("tool_calls")

            if not isinstance(tool_calls, list) or not tool_calls:
                raise PlannerError(
                    "action=call_tools but no tool_calls were provided"
                )

            for call in tool_calls:
                if not isinstance(call, dict):
                    raise PlannerError(
                        f"Invalid tool call: {call!r}"
                    )

                if not call.get("tool"):
                    raise PlannerError(
                        f"Tool call is missing 'tool': {call!r}"
                    )

                if "arguments" not in call:
                    call["arguments"] = {}

            return decision

        answer = decision.get("answer")

        if not isinstance(answer, str):
            raise PlannerError(
                f"action=final_answer but answer is missing: {decision!r}"
            )

        return decision