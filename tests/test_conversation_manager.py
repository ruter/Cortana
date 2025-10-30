from __future__ import annotations

import asyncio

import pytest

from assistant_bot.conversation_manager import ConversationManager
from assistant_bot.memu_client import RetrievedMemories


class DummyMemUClient:
    def __init__(self) -> None:
        self.retrieve_calls: list[tuple[str, str, int]] = []
        self.batch_calls: list[dict] = []

    async def retrieve_memories(self, *, user_id: str, query: str, limit: int = 20):
        self.retrieve_calls.append((user_id, query, limit))
        return RetrievedMemories(default_categories=["core-memory"], related_memories=["memory-1", "memory-2"])

    async def batch_memorize(self, *, user_id: str, user_name: str | None, messages):
        self.batch_calls.append({"user_id": user_id, "user_name": user_name, "messages": messages})


@pytest.mark.asyncio
async def test_prepare_prompt_triggers_memory_retrieval():
    memu = DummyMemUClient()
    manager = ConversationManager(
        memu,
        context_max_tokens=500,
        session_ttl_seconds=60,
        memorization_batch_size=3,
        retrieval_top_k=5,
        user_name_fallback="User",
    )

    prompt = await manager.prepare_prompt(
        guild_id=None,
        channel_id=1,
        user_id=2,
        user_message="Hello there",
        user_name="Alex",
        agent_name="Cortana",
    )

    assert memu.retrieve_calls == [("2", "Hello there", 5)]
    assert "core-memory" in prompt
    assert "memory-1" in prompt


@pytest.mark.asyncio
async def test_batch_memorization_after_threshold():
    memu = DummyMemUClient()
    manager = ConversationManager(
        memu,
        context_max_tokens=500,
        session_ttl_seconds=60,
        memorization_batch_size=2,
        retrieval_top_k=5,
        user_name_fallback="User",
    )

    await manager.prepare_prompt(
        guild_id=None,
        channel_id=1,
        user_id=2,
        user_message="Hi",
        user_name="Alex",
        agent_name="Cortana",
    )

    await manager.record_exchange(
        guild_id=None,
        channel_id=1,
        user_id=2,
        user_message="Hi",
        assistant_message="Hello",
        user_name="Alex",
        agent_name="Cortana",
    )
    assert not memu.batch_calls

    await manager.record_exchange(
        guild_id=None,
        channel_id=1,
        user_id=2,
        user_message="How are you?",
        assistant_message="Doing well!",
        user_name="Alex",
        agent_name="Cortana",
    )

    assert len(memu.batch_calls) == 1
    assert len(memu.batch_calls[0]["messages"]) == 4


@pytest.mark.asyncio
async def test_session_expiration_triggers_new_retrieval():
    memu = DummyMemUClient()
    manager = ConversationManager(
        memu,
        context_max_tokens=500,
        session_ttl_seconds=0,
        memorization_batch_size=3,
        retrieval_top_k=5,
        user_name_fallback="User",
    )

    await manager.prepare_prompt(
        guild_id=None,
        channel_id=1,
        user_id=2,
        user_message="Ping",
        user_name="Alex",
        agent_name="Cortana",
    )
    await asyncio.sleep(0.01)
    await manager.prepare_prompt(
        guild_id=None,
        channel_id=1,
        user_id=2,
        user_message="Ping again",
        user_name="Alex",
        agent_name="Cortana",
    )

    assert len(memu.retrieve_calls) == 2
