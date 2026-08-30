from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.agent.context_manager import ContextManager
from app.agent.loop import AgentLoop
from app.brain.ollama_provider import OllamaProvider
from app.config import settings
from app.memory.store import default_store
from app.models.schemas import ApprovalDecision, ChatRequest, ChatResponse
from app.tools.registry import default_registry

app = FastAPI(title="JARVIS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten once the UI (Phase 10) is deployed
    allow_methods=["*"],
    allow_headers=["*"],
)

brain = OllamaProvider(settings.ollama_host, settings.ollama_model, settings.request_timeout_seconds)
context = ContextManager(default_store, default_registry)
loop = AgentLoop(brain, default_registry, context)


@app.get("/health")
async def health() -> dict:
    brain_health = await brain.health()
    return {
        "status": "ok" if brain_health.get("reachable") else "degraded",
        "brain": brain_health,
        "workspace": str(settings.workspace_path),
        "tools": [t.name for t in default_registry.all()],
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await loop.run(request.message, request.conversation_id)


@app.post("/approve", response_model=ChatResponse)
async def approve(decision: ApprovalDecision) -> ChatResponse:
    return await loop.resume_after_approval(
        decision.conversation_id, decision.tool_call_id, decision.approved
    )


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    conversation_id: str | None = None
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "message":
                response = await loop.run(data["message"], conversation_id or data.get("conversation_id"))
            elif msg_type == "approval":
                response = await loop.resume_after_approval(
                    data["conversation_id"], data["tool_call_id"], data["approved"]
                )
            else:
                await websocket.send_json({"error": f"Unknown message type '{msg_type}'"})
                continue

            conversation_id = response.conversation_id
            await websocket.send_json(response.model_dump())
    except WebSocketDisconnect:
        pass
