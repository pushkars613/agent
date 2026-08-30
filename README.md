# JARVIS

A private, self-hosted personal AI agent. This repo is the **foundation build**
(Phases 0–3 of the Master Development Plan): local model brain, agent loop
(plan → execute → observe → verify), and computer-control tools (files,
terminal, git) behind a permission engine. Everything else in the plan
(memory store, email, calendar, web research, browser automation, UI, iPhone,
voice, multi-agent, training) is designed to plug into this core as new
"tools" and "agents" — it is intentionally not built yet so the foundation
stays solid.

## Why this order

Per the plan's own recommended build order: build a reliable local coding
agent first, then add integrations as tools, rather than building everything
at once.

## Quickstart

### 1. Install Ollama and pull a model

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:7b   # or any model you prefer
```

### 2. Install backend deps

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
```

### 3. Run JARVIS

```bash
uvicorn app.main:app --reload --port 8765
```

### 4. Talk to it

```bash
curl -s http://localhost:8765/health

curl -s -X POST http://localhost:8765/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List the files in the current project and tell me what this repo does."}'
```

Or connect a WebSocket client to `ws://localhost:8765/ws/chat` for streaming
+ approval prompts on sensitive actions.

## What's actually implemented

- **Brain** (`app/brain/`): a `ModelProvider` interface with an `OllamaProvider`
  implementation. Swappable — Phase 17's fine-tuned model just becomes a new
  provider.
- **Agent loop** (`app/agent/`): `Planner`, `Executor`, `Observer`, `Verifier`,
  `ContextManager`, wired together in `loop.py` implementing
  `understand → plan → tool → observe → reason → tool → verify → respond`.
- **Tools** (`app/tools/`): file read/write/edit/search, terminal exec, git
  status/diff/branch/commit/log — all routed through a `PermissionEngine`
  with the plan's four levels (Read / Safe / Sensitive / Dangerous).
- **Memory** (`app/memory/`): a minimal SQLite-backed store implementing the
  same interface Postgres+Qdrant will later implement, so Phase 5 is a
  drop-in swap, not a rewrite.
- **API** (`app/main.py`): FastAPI app with `/chat`, `/ws/chat`, `/approve`,
  `/health`.

## What's intentionally NOT built yet

Email, calendar, web research, browser automation, the React/Next.js UI, the
iPhone PWA, Tailscale remote access, voice, multi-agent orchestration, the
proactive layer, and model fine-tuning. See `docs/ROADMAP.md` — these slot in
as new tools/agents once the core loop above is trustworthy on real coding
tasks.

## Repo layout

```
jarvis/
  backend/
    app/
      main.py            FastAPI app, WebSocket, routes
      config.py          settings (.env driven)
      brain/             model provider abstraction (Ollama)
      agent/             planner, executor, observer, verifier, context, loop
      tools/             file/terminal/git tools + permission engine
      memory/            SQLite-backed structured + episodic memory
      models/            pydantic schemas
      api/               request/response route handlers
    requirements.txt
  docs/
    ARCHITECTURE.md
    RULES.md             Phase 0 non-negotiables
    ROADMAP.md           full 18-phase plan + status
  docker-compose.yml      postgres + qdrant, ready for Phase 5
  .env.example
```
