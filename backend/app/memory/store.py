"""
Phase 5 (stub): a minimal but real memory store.

The interface here is deliberately the one Postgres+Qdrant will eventually
implement: structured conversation turns + free-text "outcomes" that can
later be embedded and searched semantically. Today it's plain SQLite so the
whole system runs with zero extra infra; swapping in `PostgresQdrantStore`
later means implementing this same `MemoryStore` ABC.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import aiosqlite

from app.config import settings


@dataclass
class Turn:
    conversation_id: str
    role: str
    content: str
    ts: float


class MemoryStore(ABC):
    @abstractmethod
    async def append_turn(self, conversation_id: str, role: str, content: str) -> None: ...

    @abstractmethod
    async def get_conversation(self, conversation_id: str, limit: int = 20) -> list[Turn]: ...

    @abstractmethod
    async def save_outcome(self, conversation_id: str, summary: str) -> None: ...

    @abstractmethod
    async def recent_outcomes(self, limit: int = 5) -> list[str]: ...


class SQLiteMemoryStore(MemoryStore):
    def __init__(self, path: str | None = None):
        self.path = path or settings.sqlite_path
        self._initialized = False

    async def _ensure(self) -> None:
        if self._initialized:
            return
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS turns (
                    conversation_id TEXT, role TEXT, content TEXT, ts REAL
                )"""
            )
            await db.execute(
                """CREATE TABLE IF NOT EXISTS outcomes (
                    conversation_id TEXT, summary TEXT, ts REAL
                )"""
            )
            await db.commit()
        self._initialized = True

    async def append_turn(self, conversation_id: str, role: str, content: str) -> None:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO turns VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, time.time()),
            )
            await db.commit()

    async def get_conversation(self, conversation_id: str, limit: int = 20) -> list[Turn]:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT conversation_id, role, content, ts FROM turns "
                "WHERE conversation_id = ? ORDER BY ts DESC LIMIT ?",
                (conversation_id, limit),
            )
            rows = await cursor.fetchall()
        return [Turn(*row) for row in reversed(rows)]

    async def save_outcome(self, conversation_id: str, summary: str) -> None:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO outcomes VALUES (?, ?, ?)",
                (conversation_id, summary, time.time()),
            )
            await db.commit()

    async def recent_outcomes(self, limit: int = 5) -> list[str]:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT summary FROM outcomes ORDER BY ts DESC LIMIT ?", (limit,)
            )
            rows = await cursor.fetchall()
        return [r[0] for r in rows]


default_store: MemoryStore = SQLiteMemoryStore()
