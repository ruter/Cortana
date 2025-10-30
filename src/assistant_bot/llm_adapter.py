from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings


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
    """Wraps a PydanticAI agent configured for OpenRouter."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float,
        max_output_tokens: int,
        system_prompt: str,
        max_retries: int = 3,
    ) -> None:
        provider = OpenAIProvider(api_key=api_key, base_url=base_url)
        self._agent = Agent(
            OpenAIChatModel(model, provider=provider),
            system_prompt=system_prompt,
        )
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._max_retries = max_retries

    async def generate_reply(self, prompt: str) -> str:
        backoff = 0.5
        for attempt in range(1, self._max_retries + 1):
            try:
                result = await self._agent.run(
                    prompt,
                    model_settings=ModelSettings(temperature=self._temperature, max_output_tokens=self._max_output_tokens),
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
