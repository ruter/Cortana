from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

try:
    from memu import MemuClient as SyncMemuClient
    from memu.sdk.python.exceptions import (
        MemuAPIException,
        MemuConnectionException,
        MemuSDKException,
        MemuValidationException,
    )
except ImportError as import_exc:
    raise ImportError(
        "memu-py must be installed. Run 'pip install cortana-discord-assistant[memu]' or 'pip install memu-py'."
    ) from import_exc


logger = logging.getLogger(__name__)


class MemUError(Exception):
    """Raised when MemU API interactions fail."""


@dataclass(slots=True)
class MemoryRecord:
    role: str
    content: str
    metadata: dict[str, Any]


@dataclass(slots=True)
class RetrievedMemories:
    default_categories: list[str]
    related_memories: list[str]


class MemUClient:
    """Async client for MemU memory operations."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        agent_id: str,
        agent_name: str,
        user_name_fallback: str,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._client = SyncMemuClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._agent_id = agent_id
        self._agent_name = agent_name
        self._user_name_fallback = user_name_fallback

    async def aclose(self) -> None:
        await asyncio.to_thread(self._client.close)

    async def retrieve_memories(
        self,
        *,
        user_id: str,
        query: str,
        limit: int = 20,
    ) -> RetrievedMemories:
        search_query = query.strip() or "general conversation context"
        try:
            default_categories, response = await asyncio.gather(
                asyncio.to_thread(
                    self._client.retrieve_default_categories,
                    user_id=user_id,
                    agent_id=self._agent_id,
                ),
                asyncio.to_thread(
                    self._client.retrieve_related_memory_items,
                    user_id=user_id,
                    agent_id=self._agent_id,
                    query=search_query,
                    top_k=limit,
                ),
            )
        except (MemuValidationException, MemuAPIException, MemuConnectionException, MemuSDKException) as exc:
            logger.error("MemU retrieval failed for user %s: %s", user_id, exc)
            raise MemUError(str(exc)) from exc

        default_texts = [category.content for category in default_categories.categories]
        related_texts = [item.memory.content for item in response.related_memories]
        logger.debug(
            "Retrieved %d categories and %d related memories for user %s",
            len(default_texts),
            len(related_texts),
            user_id,
        )
        return RetrievedMemories(default_categories=default_texts, related_memories=related_texts)

    async def batch_memorize(
        self,
        *,
        user_id: str,
        user_name: str | None,
        messages: list[MemoryRecord],
    ) -> None:
        if not messages:
            return
        conversation = [
            {"role": entry.role, "content": entry.content}
            for entry in messages
            if entry.content.strip()
        ]
        if not conversation:
            return

        safe_user_name = (user_name or self._user_name_fallback).strip() or self._user_name_fallback

        try:
            await asyncio.to_thread(
                self._client.memorize_conversation,
                conversation,
                user_id=user_id,
                user_name=safe_user_name,
                agent_id=self._agent_id,
                agent_name=self._agent_name,
            )
        except (MemuValidationException, MemuAPIException, MemuConnectionException, MemuSDKException) as exc:
            logger.error("MemU memorization failed for user %s: %s", user_id, exc)
            raise MemUError(str(exc)) from exc

        logger.debug("Memorized %d messages for user %s", len(conversation), user_id)
