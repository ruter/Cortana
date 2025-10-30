from __future__ import annotations

import logging
from typing import Optional

import discord
from discord.ext import commands

from .config import Settings, get_settings
from .conversation_manager import ConversationManager
from .handlers.message_handler import MessageHandler
from .llm_adapter import LlmAdapter
from .memu_client import MemUClient


class AssistantBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or("!"), intents=intents)
        self.settings = settings

        self.memu_client = MemUClient(
            base_url=settings.memu_base_url,
            api_key=settings.memu_api_key,
            agent_id=settings.memu_agent_id,
            agent_name=settings.memu_agent_name,
            user_name_fallback=settings.memu_user_name_fallback,
        )

        self.llm_adapter = LlmAdapter(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            temperature=settings.openrouter_temperature,
            max_output_tokens=settings.openrouter_max_output_tokens,
            system_prompt="You are Cortana, a concise AI assistant for Discord.",
        )

        self.conversation_manager = ConversationManager(
            self.memu_client,
            context_max_tokens=settings.context_max_tokens,
            session_ttl_seconds=settings.session_ttl_seconds,
            memorization_batch_size=settings.memorization_batch_size,
            retrieval_top_k=settings.memu_retrieve_top_k,
            user_name_fallback=settings.memu_user_name_fallback,
        )

        self._message_handler: Optional[MessageHandler] = None

    async def setup_hook(self) -> None:
        self._message_handler = MessageHandler(self, self.conversation_manager, self.llm_adapter)
        self.add_listener(self._message_handler.on_message)

    async def close(self) -> None:
        await self.conversation_manager.flush_all()
        await self.memu_client.aclose()
        await super().close()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def run_bot() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    bot = AssistantBot(settings)
    bot.run(settings.discord_token)


if __name__ == "__main__":
    run_bot()
