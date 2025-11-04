from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from google.genai import Client
from google.genai.types import HttpOptions
from typing import Any, Protocol

from pydantic_ai import Agent, UrlContextTool, WebSearchTool
from pydantic_ai.mcp import load_mcp_servers
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google import GoogleProvider


logger = logging.getLogger(__name__)


class LlmError(Exception):
    """Raised when the LLM provider fails."""


class PromptFormatter(Protocol):
    def __call__(self, *, memories: list[str], history: list[tuple[str, str]], user_message: str) -> str:
        ...


@dataclass(slots=True)
class ConversationContext:
    prompt: str
    history: list[tuple[str, str]]
    memories: list[str]


class LlmAdapter:
    """Wraps a PydanticAI agent configured for Google."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        settings: dict[str, Any],
        system_prompt: str,
        max_retries: int = 3,
        one_balance_auth_key: str | None = None,
    ) -> None:
        # servers = load_mcp_servers('mcp_servers.json')
        # logger.info("Loaded %d servers: %s", len(servers), servers)
        if one_balance_auth_key:
            client = Client(
                api_key=api_key,
                http_options=HttpOptions(
                    base_url=base_url,
                    headers={"x-goog-api-key": one_balance_auth_key}
                )
            )
            provider = GoogleProvider(client=client)
        else:
            provider = GoogleProvider(api_key=api_key)
        self._agent = Agent(
            GoogleModel(model, provider=provider),
            system_prompt=system_prompt,
            builtin_tools=[UrlContextTool(), WebSearchTool()],
            # toolsets=servers,
        )
        self._max_retries = max_retries
        self._settings = GoogleModelSettings(
            temperature=settings.get("temperature"),
            max_tokens=settings.get("max_tokens"),
            google_thinking_config={"thinking_budget": settings.get("llm_thinking_budget")},
        )

    async def generate_reply(self, prompt: str) -> str:
        backoff = 0.5
        for attempt in range(1, self._max_retries + 1):
            try:
                result = await self._agent.run(
                    prompt,
                    model_settings=self._settings,
                )
                return str(result.output)
            except Exception as exc:  # pragma: no cover - logging path
                logger.warning(
                    "LLM request failed (attempt %d/%d): %s", attempt, self._max_retries, exc
                )
                if attempt == self._max_retries:
                    raise LlmError(str(exc)) from exc
                await asyncio.sleep(backoff)
                backoff *= 2

        raise LlmError("Failed to generate reply")
