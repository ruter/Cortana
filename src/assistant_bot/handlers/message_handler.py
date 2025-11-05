from __future__ import annotations

import logging
from typing import Optional

import discord

from ..conversation_manager import ConversationManager
from ..llm_adapter import LlmAdapter, LlmError


logger = logging.getLogger(__name__)


class MessageHandler:
    def __init__(
        self,
        bot: discord.Client,
        conversation_manager: ConversationManager,
        llm_adapter: LlmAdapter,
    ) -> None:
        self._bot = bot
        self._conversation_manager = conversation_manager
        self._llm_adapter = llm_adapter

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if not self._should_respond(message):
            return

        guild_id = message.guild.id if message.guild else None
        channel_id = message.channel.id
        user_id = message.author.id
        cleaned_content = self._strip_bot_mention(message)
        user_display_name = getattr(message.author, "display_name", None) or message.author.name
        agent_name = None
        if self._bot.user:
            agent_name = getattr(self._bot.user, "display_name", None) or self._bot.user.name

        thinking_message: Optional[discord.Message] = None
        error_reply = "I ran into an error while thinking. Please try again."
        try:
            thinking_message = await message.channel.send("I am thinking, wait a moument...")
            prompt = await self._conversation_manager.prepare_prompt(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                user_message=cleaned_content,
                user_name=user_display_name,
                agent_name=agent_name,
            )
            reply = await self._llm_adapter.generate_reply(prompt)
        except LlmError as exc:
            logger.error("LLM error: %s", exc)
            if thinking_message:
                await thinking_message.edit(content=error_reply)
            else:
                await message.channel.send(error_reply)
            return
        except Exception:
            logger.exception("Unexpected error while handling message")
            if thinking_message:
                await thinking_message.edit(content=error_reply)
            else:
                await message.channel.send(error_reply)
            return

        if thinking_message:
            await thinking_message.edit(content=reply)
        else:
            await message.channel.send(reply)
        await self._conversation_manager.record_exchange(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            user_message=cleaned_content,
            assistant_message=reply,
            user_name=user_display_name,
            agent_name=agent_name,
        )

    def _should_respond(self, message: discord.Message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return True
        if not message.guild:
            return True
        if self._bot.user and self._bot.user in message.mentions:
            return True
        return False

    def _strip_bot_mention(self, message: discord.Message) -> str:
        content = message.content
        if self._bot.user:
            bot_mention = self._bot.user.mention
            content = content.replace(bot_mention, "").strip()
            for mention in message.mentions:
                if mention == self._bot.user:
                    content = content.replace(mention.mention, "").strip()
        return content or message.content
