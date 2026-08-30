from __future__ import annotations

from typing import Any

import httpx

from .provider import ModelProvider


class OllamaProvider(ModelProvider):
    """Talks to a local Ollama daemon. No network calls leave localhost."""

    def __init__(self, host: str, model: str, timeout_seconds: int = 120):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(f"{self.host}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.host}/api/tags")
                resp.raise_for_status()
                tags = [m["name"] for m in resp.json().get("models", [])]
                return {
                    "reachable": True,
                    "host": self.host,
                    "configured_model": self.model,
                    "available_models": tags,
                    "configured_model_pulled": self.model in tags,
                }
        except Exception as exc:  # noqa: BLE001
            return {"reachable": False, "host": self.host, "error": str(exc)}
