from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional

from .memu_client import MemUClient, MemoryRecord, MemUError, RetrievedMemories
from .utils.token_counter import estimate_tokens


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ConversationTurn:
    role: str
    content: str


@dataclass(slots=True)
class SessionState:
    user_name: str
    agent_name: Optional[str]
    default_memories: list[str]
    related_memories: list[str]
    history: Deque[ConversationTurn] = field(default_factory=deque)
    pending_batch: list[MemoryRecord] = field(default_factory=list)
    last_active: float = field(default_factory=lambda: time.time())
    exchanges_since_batch: int = 0


class ConversationManager:
    """Tracks per-channel sessions and coordinates MemU interactions."""

    def __init__(
        self,
        memu_client: MemUClient,
        *,
        context_max_tokens: int,
        session_ttl_seconds: int,
        memorization_batch_size: int,
        retrieval_top_k: int,
        user_name_fallback: str,
        history_max_turns: int = 20,
    ) -> None:
        self._memu_client = memu_client
        self._sessions: dict[tuple[int | None, int, int], SessionState] = {}
        self._lock = asyncio.Lock()
        self._context_max_tokens = context_max_tokens
        self._session_ttl_seconds = session_ttl_seconds
        self._memorization_batch_size = memorization_batch_size
        self._retrieval_top_k = retrieval_top_k
        self._user_name_fallback = user_name_fallback
        self._history_max_turns = history_max_turns

    async def prepare_prompt(
        self,
        *,
        guild_id: Optional[int],
        channel_id: int,
        user_id: int,
        user_message: str,
        user_name: Optional[str],
        agent_name: Optional[str],
    ) -> str:
        async with self._lock:
            session = await self._get_or_create_session(
                guild_id,
                channel_id,
                user_id,
                user_name=user_name,
                agent_name=agent_name,
                query=user_message,
            )
            session.last_active = time.time()

            prompt_sections: list[str] = []

            if session.default_memories:
                prompt_sections.append(
                    "Core context from MemU:\n" + "\n".join(f"- {m}" for m in session.default_memories)
                )

            if session.related_memories:
                prompt_sections.append(
                    "Additional relevant memories:\n" + "\n".join(f"- {m}" for m in session.related_memories)
                )

            turns: list[str] = []
            total_tokens = estimate_tokens("\n".join(prompt_sections))

            history_iter = list(session.history)[-self._history_max_turns :]
            for turn in history_iter:
                formatted = f"{turn.role.capitalize()}: {turn.content}"
                turn_tokens = estimate_tokens(formatted)
                if total_tokens + turn_tokens > self._context_max_tokens:
                    break
                turns.append(formatted)
                total_tokens += turn_tokens

            user_fragment = f"User: {user_message}"
            if total_tokens + estimate_tokens(user_fragment) > self._context_max_tokens:
                turns = turns[-5:]
                total_tokens = estimate_tokens("\n".join(prompt_sections + turns))

            turns.append(user_fragment)
            prompt_sections.append("Conversation history:\n" + "\n".join(turns))

            prompt_sections.append(
                "Instructions: You are a helpful assistant responding succinctly and accurately to the user while leveraging provided memories."
            )

            prompt = "\n\n".join(section for section in prompt_sections if section)
            return prompt

    async def record_exchange(
        self,
        *,
        guild_id: Optional[int],
        channel_id: int,
        user_id: int,
        user_message: str,
        assistant_message: str,
        user_name: Optional[str],
        agent_name: Optional[str],
    ) -> None:
        async with self._lock:
            key = self._session_key(guild_id, channel_id, user_id)
            session = self._sessions.get(key)
            if not session:
                session = await self._get_or_create_session(
                    guild_id,
                    channel_id,
                    user_id,
                    user_name=user_name,
                    agent_name=agent_name,
                    query=user_message,
                )
            else:
                if user_name:
                    session.user_name = user_name
                if agent_name:
                    session.agent_name = agent_name

            session.history.append(ConversationTurn(role="user", content=user_message))
            session.history.append(ConversationTurn(role="assistant", content=assistant_message))
            while len(session.history) > self._history_max_turns:
                session.history.popleft()

            session.pending_batch.extend(
                [
                    MemoryRecord(
                        role="user",
                        content=user_message,
                        metadata={
                            "guild_id": guild_id,
                            "channel_id": channel_id,
                            "user_id": user_id,
                            "user_name": user_name,
                            "agent_name": agent_name,
                        },
                    ),
                    MemoryRecord(
                        role="assistant",
                        content=assistant_message,
                        metadata={
                            "guild_id": guild_id,
                            "channel_id": channel_id,
                            "user_id": user_id,
                            "user_name": user_name,
                            "agent_name": agent_name,
                        },
                    ),
                ]
            )
            session.exchanges_since_batch += 1

            if session.exchanges_since_batch >= self._memorization_batch_size:
                await self._flush_session_batch(key, session)

    async def flush_all(self) -> None:
        async with self._lock:
            for key, session in list(self._sessions.items()):
                await self._flush_session_batch(key, session)

    async def _get_or_create_session(
        self,
        guild_id: Optional[int],
        channel_id: int,
        user_id: int,
        *,
        user_name: Optional[str],
        agent_name: Optional[str],
        query: str,
    ) -> SessionState:
        key = self._session_key(guild_id, channel_id, user_id)
        session = self._sessions.get(key)
        now = time.time()
        if session and now - session.last_active <= self._session_ttl_seconds:
            if user_name:
                session.user_name = user_name
            if agent_name:
                session.agent_name = agent_name
            return session

        retrieved: RetrievedMemories | None = None
        try:
            retrieved = await self._memu_client.retrieve_memories(
                user_id=str(user_id),
                query=query,
                limit=self._retrieval_top_k,
            )
            logger.debug(
                "Retrieved memories for session %s (default=%d, related=%d)",
                key,
                len(retrieved.default_categories),
                len(retrieved.related_memories),
            )
        except MemUError as exc:
            logger.error("Failed to retrieve memories for %s: %s", key, exc)

        resolved_user_name = user_name or self._user_name_fallback
        session = SessionState(
            user_name=resolved_user_name,
            agent_name=agent_name,
            default_memories=retrieved.default_categories if retrieved else [],
            related_memories=retrieved.related_memories if retrieved else [],
        )
        self._sessions[key] = session
        return session

    async def _flush_session_batch(self, key: tuple[int | None, int, int], session: SessionState) -> None:
        if not session.pending_batch:
            session.exchanges_since_batch = 0
            return
        payload = list(session.pending_batch)
        try:
            await self._memu_client.batch_memorize(
                user_id=str(key[2]),
                user_name=session.user_name,
                messages=payload,
            )
        except MemUError as exc:
            logger.error("Failed to batch memorize for %s: %s", key, exc)
            return
        session.pending_batch.clear()
        session.exchanges_since_batch = 0

    @staticmethod
    def _session_key(guild_id: Optional[int], channel_id: int, user_id: int) -> tuple[int | None, int, int]:
        return (guild_id, channel_id, user_id)
