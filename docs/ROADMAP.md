# Roadmap & Status

| Phase | Name | Status |
|---|---|---|
| 0 | Architecture & Rules | ✅ Done — this repo |
| 1 | JARVIS Brain (local model via Ollama) | ✅ Done |
| 2 | Agent Engine (planner/executor/observer/verifier) | ✅ Done |
| 3 | Computer Control (files/terminal/git + permissions) | ✅ Done |
| 4 | Coding Agent (repo indexing, test-fix loop) | ⏳ Not started |
| 5 | Memory (Postgres + Qdrant) | 🟡 Interface stubbed, SQLite fallback only |
| 6 | Email Agent | ⏳ Not started |
| 7 | Calendar + Tasks | ⏳ Not started |
| 8 | Web / Research Agent | ⏳ Not started |
| 9 | Browser Automation | ⏳ Not started |
| 10 | JARVIS UI (Next.js) | ⏳ Not started |
| 11 | iPhone PWA | ⏳ Not started |
| 12 | Remote Infra (Tailscale) | ⏳ Not started |
| 13 | Voice JARVIS | ⏳ Not started |
| 14 | Multi-Agent System | ⏳ Not started |
| 15 | Proactive JARVIS | ⏳ Not started |
| 16 | Learning System | ⏳ Not started |
| 17 | Train YOUR JARVIS Model | ⏳ Not started |
| 18 | JARVIS Intelligence Loop | ⏳ Not started |

## Immediate next steps (recommended)

1. Run the foundation locally against a real repo and a real coding task —
   this is the plan's "First Concrete Milestone."
2. Harden `Verifier` — right now it does one LLM-judged pass; add a real
   test-runner check (`pytest` exit code) before declaring success once
   Phase 4 lands.
3. Build Phase 4 (Coding Agent) directly on top of the existing
   `terminal_tools`/`git_tools` — mostly prompt + orchestration work, little
   new plumbing.
4. Only after the coding agent is reliable, start Phase 5 (swap SQLite memory
   for Postgres+Qdrant) and Phase 6+ integrations, one at a time.
