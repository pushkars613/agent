# Architecture

```
Client (curl / web / iPhone PWA later)
        │  HTTP or WebSocket
        ▼
  FastAPI app (app/main.py)
        │
        ▼
  AgentLoop (app/agent/loop.py)
   ┌──────────────────────────────────────────────┐
   │ ContextManager  → assembles conversation +    │
   │                    memory + tool schemas      │
   │ Planner         → asks Brain for a plan        │
   │                    (list of tool calls or a    │
   │                    direct answer)              │
   │ Executor        → runs each tool call through  │
   │                    PermissionEngine            │
   │ Observer        → records tool results,        │
   │                    detects errors               │
   │ Verifier        → asks Brain "did this satisfy  │
   │                    the request?" and either     │
   │                    finishes or loops with a     │
   │                    corrected plan               │
   └──────────────────────────────────────────────┘
        │
        ▼
  Brain (app/brain/) ── ModelProvider interface ── OllamaProvider (local)
        │
        ▼
  Tools (app/tools/) ── file_tools, terminal_tools, git_tools
        │  every call passes through
        ▼
  PermissionEngine (Level 0 Read / 1 Safe / 2 Sensitive / 3 Dangerous)
        │  levels 2-3 block on:
        ▼
  Approval queue → client responds via /approve or ws message
```

## Request lifecycle

1. Client sends a message (`/chat` or over the WebSocket).
2. `ContextManager` loads recent conversation + relevant memory entries and
   builds a system prompt including the tool schemas.
3. `Planner` calls the Brain with the context and gets back either:
   - a final natural-language answer, or
   - one or more tool calls (JSON) to run next.
4. `Executor` runs each tool call. Every tool call first passes through
   `PermissionEngine.check()`. Level 0/1 calls run immediately; level 2/3
   calls are queued and the loop pauses, emitting an `approval_required`
   event to the client.
5. `Observer` appends results (or errors) to the running transcript.
6. `Verifier` asks the Brain whether the original request has been
   satisfied. If not, it feeds the failure back to `Planner` for another
   iteration (bounded by `MAX_ITERATIONS` in config).
7. Once verified (or iterations exhausted), the loop returns the final
   answer and `ContextManager` writes a memory entry summarizing the
   outcome.

## Extension points for later phases

- **Phase 4 (Coding Agent)**: add `tools/code_tools.py` (repo indexing, test
  running, diff generation) — reuses the existing `terminal_tools` and
  `git_tools` underneath.
- **Phase 5 (Memory)**: implement `PostgresQdrantStore` against the same
  `MemoryStore` interface in `app/memory/store.py`; swap it in via config.
- **Phase 6-9 (Email/Calendar/Web/Browser)**: each becomes a new file in
  `app/tools/` registered with the tool registry, plus new permission rules.
- **Phase 10-11 (UI/iPhone)**: pure clients of the existing HTTP/WebSocket
  API — no backend changes needed.
- **Phase 14 (Multi-agent)**: `AgentLoop` becomes one of several agents
  behind an `Orchestrator` that routes by intent; the loop's interface
  (`run(message) -> Response`) is already orchestrator-ready.
