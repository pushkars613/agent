# Phase 0 — Architecture Rules (non-negotiable)

These constraints are enforced in code, not just documentation:

1. **Local-first AI.** `app/brain/provider.py` defines the interface; the only
   implementation shipped is `OllamaProvider`, which talks to a local Ollama
   daemon. No cloud AI API keys are read or required anywhere in this repo.
2. **Self-hosted backend.** FastAPI app runs on your own machine/server. No
   external hosting dependency.
3. **Tool-based architecture.** The agent never acts directly — every effect
   on the world (file write, shell command, git push) goes through a `Tool`
   object registered in `app/tools/registry.py`, so new capabilities (email,
   calendar, browser) are added as tools/agents, not core rewrites.
4. **Human approval for sensitive actions.** `PermissionEngine`
   (`app/tools/permissions.py`) classifies every tool call into levels 0–3
   and blocks levels 2–3 until an explicit approval is received via
   `/approve` or the WebSocket approval flow.
5. **Multi-device access.** The API is transport-agnostic HTTP/WebSocket so
   any client (Mac CLI, web, iPhone PWA later) can drive it.
6. **Persistent memory.** `app/memory/store.py` defines the interface now,
   backed by SQLite today, Postgres+Qdrant in Phase 5 — same interface.
7. **Modular model support.** Swapping models/providers should never require
   touching `app/agent/` — only `app/brain/`.
