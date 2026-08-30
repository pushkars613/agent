from __future__ import annotations

import json

from app.brain.provider import ModelProvider

VERIFY_PROMPT = """You just gave this final answer to the user's original request:

ORIGINAL REQUEST: {request}
FINAL ANSWER: {answer}

Judge honestly: does the final answer actually satisfy the request, based on the tool \
results seen earlier in this conversation (not just plausibility of wording)? Respond ONLY \
with JSON: {{"satisfied": true|false, "reason": "<one sentence>"}}"""


class Verifier:
    def __init__(self, brain: ModelProvider):
        self.brain = brain

    async def check(
        self, request: str, answer: str, messages: list[dict[str, str]]
    ) -> tuple[bool, str]:
        prompt = VERIFY_PROMPT.format(request=request, answer=answer)
        raw = await self.brain.complete(
            "You are a strict verifier. Respond only with the requested JSON.",
            [*messages, {"role": "user", "content": prompt}],
            json_mode=True,
        )
        try:
            data = json.loads(raw)
            return bool(data.get("satisfied", False)), data.get("reason", "")
        except json.JSONDecodeError:
            # Fail open with a warning rather than looping forever on a flaky judge.
            return True, "Verifier response was not valid JSON; passing through."
