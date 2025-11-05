# Cortana Discord Assistant

Production-oriented Discord bot that blends MemU's agentic memory system with Google Gemini models via PydanticAI. The bot retrieves core memories and contextual recalls before every conversation, builds token-aware prompts, generates replies through PydanticAI, and batches new exchanges back into MemU.

## Features
- **MemU SDK Integration** – Uses `retrieve_default_categories` plus `retrieve_related_memory_items` to gather memories before the first response of a session.
- **PydanticAI on Google Gemini** – Delegates prompt construction to a PydanticAI agent configured for Google Gemini 2.5-flash with built-in tool calling support.
- **Tool Integration** – Supports URL context analysis and web search via PydanticAI tools.
- **MCP Server Support** – Extensible architecture for Model Context Protocol servers (currently configured but not active).
- **Session Management** – Maintains per-channel/user context with TTL-based resets and token-aware trimming.
- **Batch Memorization** – Stores conversations in MemU every 2–4 exchanges (configurable) using the SDK.
- **Graceful Error Handling** – Logs external API issues and keeps the bot responsive.
- **Thinking Placeholder Replies** – Immediately acknowledges new conversations with "I am thinking, wait a moment..." and edits the message to the final LLM response.

## Prerequisites
- Python 3.10+
- Discord application with bot token and **Message Content Intent** enabled
- Google Gemini API key (via Google AI Studio)
- MemU API key (cloud or self-hosted) and optional custom base URL
- (Optional) One Balance auth key for enhanced Gemini API access
- (Recommended) Virtual environment such as `venv` or `uv`

## Installation
```bash
python -m pip install -e ".[dev]"
```

The MemU SDK is included in the main requirements. If you encounter import errors, you can install it separately:
```bash
python -m pip install memu-py
```

## Configuration
Create a `.env` file in the project root. All variables support overrides via the environment.

```env
# Discord
DISCORD_TOKEN=your_discord_token

# Google Gemini / PydanticAI
GOOGLE_API_KEY=your_google_api_key
GOOGLE_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GOOGLE_MODEL=gemini-2.5-flash
ONE_BALANCE_AUTH_KEY=your_one_balance_key  # Optional

# MemU
MEMU_API_KEY=your_memu_key
MEMU_BASE_URL=https://api.memu.so
MEMU_AGENT_ID=discord-assistant
MEMU_AGENT_NAME=Cortana
MEMU_RETRIEVE_TOP_K=20
MEMU_USER_NAME_FALLBACK=User

# Session / Context
CONTEXT_MAX_TOKENS=40960
LLM_TEMPERATURE=0.5
LLM_THINKING_BUDGET=1024
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
4. **Response** – Sends a placeholder message, then edits it in place with the generated reply.
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
├── llm_adapter.py         # PydanticAI agent wrapper for Google Gemini
├── memu_client.py         # Async wrappers over MemU SDK
├── handlers/
│   └── message_handler.py # Discord message orchestration
└── utils/
    └── token_counter.py   # Token estimation utilities
tests/
└── test_conversation_manager.py
```

## Troubleshooting
- **MemU SDK ImportError** – Ensure `memu-py` is installed (`pip install .[memu]`).
- **Google API Errors** – Verify your Google API key is valid and has access to Gemini models.
- **Discord Missing Intent** – Enable the **Message Content Intent** on your bot’s application page.
- **Rate Limiting** – Google Gemini has rate limits; monitor usage in Google AI Studio.
- **Notion Integration** – Notion API is mentioned in system prompts but not currently implemented.

## Additional Notes
- Conversation flushing occurs on shutdown to avoid losing pending batches; ensure the process exits gracefully (Ctrl+C).
- The prompt remains concise by estimating tokens locally—adjust `CONTEXT_MAX_TOKENS` if using larger models.
- Extend memory metadata in `conversation_manager.py` if you need richer MemU storage schemas.
- The bot responds to @mentions in servers and all messages in DMs.
- MCP servers can be configured in `mcp_servers.json` for additional tool integrations.
- Docker deployment is supported with automated builds via GitHub Actions.
