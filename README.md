# Cortana Discord Assistant

Production-oriented Discord bot that blends MemU's agentic memory system with OpenRouter models via PydanticAI. The bot retrieves core memories and contextual recalls before every conversation, builds token-aware prompts, generates replies through PydanticAI, and batches new exchanges back into MemU.

## Features
- **MemU SDK Integration** – Uses `retrieve_default_categories` plus `retrieve_related_memory_items` to gather memories before the first response of a session.
- **PydanticAI on OpenRouter** – Delegates prompt construction to a PydanticAI agent configured for OpenRouter-compatible models.
- **Session Management** – Maintains per-channel/user context with TTL-based resets and token-aware trimming.
- **Batch Memorization** – Stores conversations in MemU every 2–4 exchanges (configurable) using the SDK.
- **Graceful Error Handling** – Logs external API issues and keeps the bot responsive.

## Prerequisites
- Python 3.10+
- Discord application with bot token and **Message Content Intent** enabled
- OpenRouter API key and target model name (e.g. `openrouter/anthropic/claude-3.5-sonnet`)
- MemU API key (cloud or self-hosted) and optional custom base URL
- (Recommended) Virtual environment such as `venv` or `uv`

## Installation
```bash
python -m pip install -e ".[dev]"
# Install MemU SDK extra if not already present
python -m pip install -e ".[memu]"
```

If you prefer separate commands:
```bash
python -m pip install memu-py
```

## Configuration
Create a `.env` file in the project root. All variables support overrides via the environment.

```env
# Discord
DISCORD_TOKEN=your_discord_token

# OpenRouter / PydanticAI
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openrouter/model
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_TEMPERATURE=0.2
OPENROUTER_MAX_OUTPUT_TOKENS=800

# MemU
MEMU_API_KEY=your_memu_key
MEMU_BASE_URL=https://api.memu.ai/v1
MEMU_AGENT_ID=discord-assistant
MEMU_AGENT_NAME=Cortana
MEMU_RETRIEVE_TOP_K=20
MEMU_USER_NAME_FALLBACK=User

# Session / Context
CONTEXT_MAX_TOKENS=3000
SESSION_TTL_SECONDS=900
MEMORIZATION_BATCH_SIZE=3

# Logging
LOG_LEVEL=INFO
```

Unset values fall back to sensible defaults defined in `assistant_bot.config.Settings`.

## Running the Bot
```bash
python -m assistant_bot.bot
```

### Lifecycle
1. **Startup** – Loads configuration, initializes MemU SDK client, PydanticAI agent, and conversation manager.
2. **Message Handling** – On the first message of a session, retrieves default categories and related memories from MemU before sending any LLM requests.
3. **Prompt Generation** – Assembles memories, trimmed history, and the user message into a single prompt passed to PydanticAI.
4. **Response** – Sends the generated reply to Discord.
5. **Batch Memorization** – Buffers exchanges and pushes them to MemU every N interactions (configurable) or on shutdown.

## Testing
Run unit tests (mocked MemU/PydanticAI interactions):
```bash
pytest
```

## Project Structure
```
src/assistant_bot/
├── bot.py                 # Discord entrypoint and dependency wiring
├── config.py              # Pydantic settings loader
├── conversation_manager.py# Session, context, and batching logic
├── llm_adapter.py         # PydanticAI agent wrapper for OpenRouter
├── memu_client.py         # Async wrappers over MemU SDK
└── handlers/
    └── message_handler.py # Discord message orchestration
tests/
└── test_conversation_manager.py
```

## Troubleshooting
- **MemU SDK ImportError** – Ensure `memu-py` is installed (`pip install .[memu]`).
- **HTTPX Version Conflicts** – MemU currently requires `httpx < 0.28`; if pip upgrades it (e.g. via OpenRouter), reinstall `memu-py` which pins a compatible version.
- **Discord Missing Intent** – Enable the **Message Content Intent** on your bot’s application page.
- **OpenRouter Errors** – Verify your API key has access to the selected model and that rate limits are not exceeded.

## Additional Notes
- Conversation flushing occurs on shutdown to avoid losing pending batches; ensure the process exits gracefully (Ctrl+C).
- The prompt remains concise by estimating tokens locally—adjust `CONTEXT_MAX_TOKENS` if using larger models.
- Extend memory metadata in `conversation_manager.py` if you need richer MemU storage schemas.
