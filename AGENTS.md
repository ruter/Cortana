# Cortana Discord Assistant - Agent Guidelines

## Build/Lint/Test Commands
- **Install**: `pip install -e .[dev]`
- **Run bot**: `python -m assistant_bot.bot`
- **Run all tests**: `pytest`
- **Run single test**: `pytest tests/test_file.py::test_function_name`
- **Build Docker**: `docker build -t cortana .`
- **Run with Docker Compose**: `docker-compose up -d`
- **Stop Docker**: `docker-compose down`

## Architecture & Structure
- **Core modules**: `bot.py` (entrypoint), `config.py` (pydantic settings), `conversation_manager.py` (session/context), `llm_adapter.py` (PydanticAI), `memu_client.py` (memory SDK), `handlers/message_handler.py` (discord events)
- **Key integrations**: Discord.py for bot framework, MemU for agentic memory, PydanticAI/Google Gemini for LLM responses
- **Data flow**: Message → retrieve memories → build prompt → generate response → batch memorize
- **No databases**: Uses MemU cloud API for persistence, in-memory sessions with TTL

## Code Style Guidelines
- **Imports**: `from __future__ import annotations` first, then standard libs, third-party, local modules
- **Types**: Use type hints everywhere, `str | None` instead of `Optional[str]`, Pydantic for config validation
- **Naming**: camelCase classes (e.g. `MessageHandler`), snake_case functions/variables (e.g. `get_settings`)
- **Async**: All I/O operations async, use `asyncio` for tests
- **Error handling**: Log exceptions, graceful fallbacks, no bare except blocks
- **Formatting**: 4-space indentation, docstrings for public functions, line length ~100 chars
