# Cortana Project - Agent Guidance Document

## 0 · Project Overview

**Cortana** is an intelligent Discord bot designed as a personalized digital assistant. It combines real-time Discord interactions with cloud-native infrastructure (Supabase for storage, Zep for memory, LLMs for reasoning).

### Core Tech Stack
- **Language:** Python 3.10+
- **Bot Framework:** `discord.py`
- **AI/LLM:** `PydanticAI` (supports OpenAI, Anthropic, Google models)
- **Memory System:** `Zep` (long-term memory with vectorization)
- **Database:** `Supabase` (PostgreSQL)
- **Web Scraping:** `aiohttp`, `BeautifulSoup`
- **Search Integration:** `Exa API` (optional, for web search)
- **Coding Agent:** Pi Coding Agent capabilities (ported from `badlogic/pi-mono`)

---

## 1 · Architecture & Core Concepts

### 1.1 High-Level Architecture

```
Discord Messages
     ↓
main.py (CortanaClient)
     ↓
┌────────────────────────────────┐
│ Memory Context Retrieval       │
│ (Zep: Long-term + Short-term)  │
└────────────────────────────────┘
     ↓
agent.py (PydanticAI Agent)
     ↓
┌─────────────────────────────────────────────┐
│ Dynamic System Prompt + Available Tools     │
│ - Task Management (Todos, Calendar)         │
│ - Information Retrieval (Web, Email)        │
│ - Memory Manipulation                       │
└─────────────────────────────────────────────┘
     ↓
LLM (OpenAI/Anthropic/Google)
     ↓
Tools Execution (tools.py)
     ↓
Supabase Database | Zep Memory
     ↓
Discord Response
```

### 1.2 Key Design Principles

- **"Thin Client, Fat Cloud":** Discord client is minimal; most logic runs on cloud backends.
- **Context-Aware Responses:** System prompt dynamically includes current time, timezone, user context.
- **Bionic Memory:** Zep stores facts and recent conversation context; agent uses this for personalization.
- **Tool-Driven Agents:** Agent calls functions (add_todo, check_calendar, etc.) rather than directly manipulating data.
- **Async-First:** All I/O operations (Discord, Zep, Supabase) are async.

---

## 2 · Project Structure

```
cortana-bot/
├── src/
│   ├── __init__.py
│   ├── main.py              # Discord client entry point
│   ├── agent.py             # PydanticAI agent setup, dynamic system prompt
│   ├── config.py            # Environment variable management
│   ├── database.py          # Supabase client singleton
│   ├── memory.py            # Zep async client singleton
│   ├── scheduler.py         # Background reminder scheduler
│   ├── skills.py            # Skills system (Pi Coding Agent)
│   └── tools.py             # Agent tools (CRUD, search, coding, etc.)
│
├── tests/
│   ├── test_coding_tools.py # Coding tools tests
│   ├── test_skills.py       # Skills system tests
│   ├── test_exa.py          # Web search functionality tests
│   ├── test_fetch.py        # URL fetching tests
│   ├── test_reminders.py    # Reminder scheduling tests
│   └── verify_flow.py       # End-to-end flow verification
│
├── workspace/               # Workspace directory (mounted volume)
│   └── skills/              # Global skills
│
├── schema.sql               # Database schema (user_settings, todos, calendar_events, reminders)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .env                     # Local environment (not in git)
├── docker-compose.yml       # Containerized deployment
├── Dockerfile               # Docker image definition
└── README.md                # User documentation
```

---

## 3 · Key Modules & Responsibilities

### 3.1 `main.py` - Discord Client & Message Handler

**Responsibility:** Real-time Discord message handling, context aggregation, response delivery.

**Key Classes:**
- `SettingsGroup`: Slash command group for `/settings model` (change LLM model).
- `CortanaClient`: Extends `discord.Client`, manages message events and reminder scheduler.

**Flow:**
1. On message: Retrieve user context from Zep.
2. Ensure user/thread exists in Zep (create if necessary).
3. Get memory context from Zep's `thread.get_user_context()`.
4. Pass message + context to `cortana_agent.run()`.
5. Receive response, send to Discord.
6. Save both messages to Zep for long-term memory.

**Important Notes:**
- User/thread creation in Zep is done lazily on first message.
- Reminder scheduler is initialized once in `on_ready()`.
- Message context is retrieved to personalize agent behavior.

### 3.2 `agent.py` - PydanticAI Agent & System Prompt

**Responsibility:** Agent initialization, tool registration, dynamic system prompt generation.

**Key Functions:**
- `dynamic_system_prompt(ctx)`: Generates system prompt dynamically with:
  - Current date/time (with timezone awareness).
  - User info (name, Discord ID).
  - Zep memory context (facts, recent conversation).
  - Task management and reminder directives.
  - Language matching protocol (respond in user's language).
  
- `initialize_agent()`: Sets up PydanticAI agent with:
  - Model selection (OpenAI, Anthropic, Google with fallbacks).
  - Tool registration (todos, calendar, reminders, search, etc.).
  - System prompt setup.

**Important Notes:**
- System prompt is **critical**: It defines Cortana's personality, language protocol, and tool usage rules.
- Model can be changed at runtime via `/settings model` command.
- Support for custom endpoints (LLM_BASE_URL) allows flexibility.

### 3.3 `config.py` - Configuration Management

**Responsibility:** Environment variable loading and validation.

**Key Variables:**
- `DISCORD_TOKEN`: Bot authentication token.
- `SUPABASE_URL`, `SUPABASE_KEY`: Database credentials.
- `ZEP_API_KEY`: Memory system API key.
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`: LLM configuration.
- `ONE_BALANCE_AUTH_KEY`: (Optional) Google API key override.
- `EXA_API_KEY`: (Optional) Web search API key.
- `DEFAULT_TIMEZONE`: User timezone for time calculations.

**Validation:** `config.validate()` ensures all required variables are set before bot starts.

### 3.4 `database.py` - Supabase Client Singleton

**Responsibility:** Centralized Supabase connection.

**Pattern:** Singleton to avoid multiple connections.

```python
db = Database().get_client()  # Get the Supabase client
```

**Usage Pattern:** `db.table("todos").select("*").eq("user_id", user_id).execute()`

### 3.5 `memory.py` - Zep Client Singleton

**Responsibility:** Centralized Zep connection for memory operations.

```python
memory_client = AsyncZep(api_key=config.ZEP_API_KEY)
```

**Key Operations:**
- `memory_client.user.add(user_id, first_name, metadata)`: Create user.
- `memory_client.user.get(user_id)`: Retrieve user info.
- `memory_client.thread.create(thread_id, user_id)`: Create conversation thread.
- `memory_client.thread.get_user_context(thread_id)`: Retrieve memory context.
- `memory_client.thread.add_messages(thread_id, messages)`: Save messages to memory.

### 3.6 `scheduler.py` - Background Reminder Scheduler

**Responsibility:** Periodic check for due reminders and delivery via Discord DM.

**Key Class:** `ReminderScheduler`
- Runs as an asyncio task in the background.
- Every 30 seconds, checks for reminders where `remind_time <= now` and `is_sent = False`.
- Sends DM to user and marks reminder as sent.
- Handles missing users gracefully (still marks as sent).

**Important Notes:**
- Started in `CortanaClient.on_ready()`.
- Gracefully handles DM failures (user may have DMs disabled).
- Prevents infinite retries by marking even failed sends as sent.

### 3.7 `tools.py` - Agent Tool Implementations

**Responsibility:** CRUD operations for todos, calendar, reminders, and information retrieval.

**Tool Categories:**

#### Task Management
- `add_todo(content, due_date, priority)`: Add todo.
- `list_todos(status, limit)`: List pending/completed todos.
- `complete_todo(todo_id)`: Mark todo as completed.
- `add_reminder(message, remind_time, related_event_id)`: Add reminder.
- `list_reminders()`: List active reminders.
- `cancel_reminder(reminder_id)`: Cancel a reminder.

#### Calendar
- `add_calendar_event(title, start_time, end_time, location)`: Add event.
- `check_calendar_availability(start_time, end_time)`: Check for conflicts.

#### Memory & Context
- `search_long_term_memory(query)`: Search Zep memory by keyword.
- `get_unread_emails()`: Fetch unread email count (placeholder).

#### Information Retrieval
- `fetch_url(url)`: Scrape webpage and extract text.
- `search_web_exa(query)`: Search web using Exa API.
- `get_contents_exa(exa_result_id)`: Fetch content from Exa search result.

#### Coding Tools (Pi Coding Agent)
- `execute_bash(command, timeout)`: Execute shell commands in the container.
- `read_file(path, offset, limit)`: Read file contents with optional line range.
- `write_file(path, content)`: Create or overwrite files.
- `edit_file(path, old_text, new_text)`: Make surgical edits to files.

**Important Notes:**
- All tools take `ctx: RunContext[Dict[str, Any]]` as first param to access user info.
- Tools return string responses (agent-friendly format).
- `ensure_user_exists()` creates user in DB if needed.

---

## 4 · Data Models & Database Schema

### 4.1 Tables (Supabase PostgreSQL)

```sql
-- User settings table
CREATE TABLE user_settings (
  user_id BIGINT PRIMARY KEY,
  created_at TIMESTAMP DEFAULT now()
);

-- Todo list
CREATE TABLE todos (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES user_settings(user_id),
  content TEXT NOT NULL,
  status VARCHAR (50) DEFAULT 'PENDING',
  due_date TIMESTAMP,
  priority INT DEFAULT 3,
  created_at TIMESTAMP DEFAULT now()
);

-- Calendar events
CREATE TABLE calendar_events (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES user_settings(user_id),
  title TEXT NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL,
  location VARCHAR (255),
  created_at TIMESTAMP DEFAULT now()
);

-- Reminders
CREATE TABLE reminders (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES user_settings(user_id),
  message TEXT NOT NULL,
  remind_time TIMESTAMP NOT NULL,
  is_sent BOOLEAN DEFAULT FALSE,
  related_event_id BIGINT REFERENCES calendar_events(id),
  created_at TIMESTAMP DEFAULT now()
);
```

### 4.2 Zep Memory Structure

- **User:** Identified by `user_id` (Discord ID as string).
- **Thread:** Identified by `thread_id` (format: `discord_{user_id}`).
- **Messages:** Stored with role (`user`/`assistant`), content, and metadata.
- **Context:** System-generated facts extracted from conversation history.

---

## 5 · Workflow Examples

### 5.1 Basic Message Handling Flow

```
User: "Add a meeting tomorrow at 3 PM"
  ↓
[Zep memory context retrieved]
  ↓
[Dynamic system prompt generated with current time + memory]
  ↓
Agent analyzes: 
  - Current date from system prompt
  - Relative time "tomorrow at 3 PM" → ISO timestamp
  - Check calendar availability (tool)
  - Call add_calendar_event tool
  ↓
Tool executes: Insert into calendar_events table
  ↓
Agent generates response: "I've secured that slot for you. Try not to be late."
  ↓
[Response sent to Discord + saved to Zep memory]
```

### 5.2 Reminder Workflow

```
User: "Remind me 10 minutes before my 3 PM meeting tomorrow"
  ↓
Agent:
  1. Calls add_calendar_event(title="...", start_time="tomorrow 3 PM")
  2. Receives event_id
  3. Calculates reminder_time = start_time - 10 minutes
  4. Calls add_reminder(message="...", remind_time=calc_time, related_event_id=event_id)
  ↓
[30 seconds later, scheduler checks reminders]
  ↓
If remind_time <= now:
  - Fetch user from Discord
  - Send DM: "⏰ **Reminder**: ..."
  - Mark as_sent = TRUE
```

### 5.3 Multi-turn Conversation with Memory

```
Turn 1:
User: "I hate early mornings"
  → Zep extracts fact: "User hates early mornings"

Turn 2:
User: "Schedule my daily standup"
  → Zep memory context includes: "User hates early mornings"
  → Agent suggests: "How about 10 AM instead of 7 AM?"
```

---

## 6 · Common Development Tasks

### 6.1 Adding a New Tool

1. **Define tool function in `tools.py`:**
   ```python
   async def my_tool(ctx: RunContext[Dict[str, Any]], param1: str) -> str:
       """Tool description for LLM."""
       user_id = ctx.deps['user_info']['id']
       # Implement logic
       return "Result message"
   ```

2. **Register in `agent.py`:**
   ```python
   agent.tool(my_tool)
   ```

3. **Update system prompt if needed** in `dynamic_system_prompt()`.

### 6.2 Modifying the System Prompt

- Edit `dynamic_system_prompt()` in `agent.py`.
- Key sections: Language Protocol, Time Awareness, Memory Protocol, Tool Usage, Response Guidelines.
- Changes take effect immediately on next message.

### 6.3 Changing LLM Model

**At Runtime:**
- User runs: `/settings model gpt-4-turbo`
- Calls `update_agent_model("gpt-4-turbo")` which reinitializes the agent.

**At Startup:**
- Set `LLM_MODEL_NAME` in `.env` file.

### 6.4 Adding a New Database Table

1. Write migration SQL in `schema.sql`.
2. Run in Supabase SQL Editor.
3. Create Pydantic models in `tools.py` if needed.
4. Use `db.table("table_name").insert/select/update/delete()` in tools.

### 6.5 Debugging Memory Issues

- Check Zep API response in logs.
- Verify `ZEP_API_KEY` is valid.
- User/thread creation happens lazily; check Zep dashboard to confirm records exist.
- Memory context is logged in `main.py:on_message()`.

---

## 7 · Environment Configuration

### Required Variables
```env
DISCORD_TOKEN=your_discord_bot_token
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_supabase_api_key
ZEP_API_KEY=your_zep_api_key
LLM_API_KEY=your_openai_or_anthropic_key
```

### Optional Variables
```env
LLM_BASE_URL=https://api.openai.com/v1          # Custom endpoint
LLM_MODEL_NAME=gpt-4o                            # Model choice
ONE_BALANCE_AUTH_KEY=...                         # Google API override
EXA_API_KEY=...                                  # Web search (Exa)
DEFAULT_TIMEZONE=America/New_York                # User timezone
LOG_LEVEL=INFO                                   # Logging level
```

### Coding Agent Variables
```env
ENABLE_BASH_TOOL=true                            # Enable bash execution
ENABLE_FILE_TOOLS=true                           # Enable file read/write/edit
ENABLE_SKILLS=true                               # Enable skills system
WORKSPACE_DIR=/workspace                         # Workspace directory
SKILLS_DIR=/workspace/skills                     # Skills directory
BASH_TIMEOUT_DEFAULT=60                          # Default bash timeout (seconds)
BASH_OUTPUT_MAX_LINES=500                        # Max output lines
BASH_OUTPUT_MAX_BYTES=51200                      # Max output bytes (50KB)
FILE_READ_MAX_LINES=1000                         # Max lines to read
```

---

## 8 · Testing

### Test Files
- `test_coding_tools.py`: Coding tools (bash, read, write, edit).
- `test_skills.py`: Skills system.
- `test_exa.py`: Web search functionality.
- `test_fetch.py`: URL scraping/fetching.
- `test_reminders.py`: Reminder scheduling.
- `verify_flow.py`: End-to-end integration test.

### Running Tests
```bash
pytest tests/test_exa.py -v
pytest tests/ -k reminder -v
```

---

## 9 · Deployment

### Docker Deployment
```bash
docker-compose up -d
docker-compose logs -f
```

### Local Development
```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

---

## 10 · Known Constraints & Design Decisions

1. **Timezone Handling:** System prompt includes current time; relative times must be converted to ISO timestamps. Fallback to UTC if tzdata unavailable (Windows).

2. **Language Matching:** Agent must detect user language and respond in kind. This is mandated in the system prompt.

3. **Reminder Scheduling:** 30-second polling interval. For millisecond precision, consider event-based notification (webhook) instead.

4. **Memory Retention:** Zep stores facts; old conversation history may be pruned per Zep policy. For critical data, store in Supabase.

5. **Discord Rate Limiting:** Large responses split across multiple messages if needed (discord.py handles this).

6. **Async-Only:** All I/O must be async. Blocking calls will stall the bot.

7. **Tool Ordering:** For reminders, **create calendar event first, then reminder**. Agent should understand this precedence from system prompt.

---

## 11 · Glossary

| Term | Definition |
|------|-----------|
| **Cortana** | The Discord bot / assistant personality. |
| **PydanticAI** | Python framework for building LLM-powered agents. |
| **Zep** | Long-term memory & context retrieval service. |
| **Supabase** | PostgreSQL database with REST API. |
| **Tool** | A Python async function the agent can call. |
| **System Prompt** | Instructions that define agent behavior and knowledge. |
| **Thread** | A conversation context in Zep (one per user). |
| **Reminder** | A scheduled notification sent via Discord DM. |
| **Exa** | Third-party web search API. |
| **Skill** | A custom CLI tool defined by a SKILL.md file. |
| **Workspace** | Directory for file operations and skills. |
| **Pi Coding Agent** | Coding agent capabilities ported from badlogic/pi-mono. |

---

## 12 · Quick Reference: Critical Code Paths

### Message Arrives → Response Sent
`main.py:on_message()` → Zep context retrieval → `agent.py:cortana_agent.run()` → Tool calls → `tools.py` functions → Database/API interactions → Discord response

### Reminder Triggers
`scheduler.py:ReminderScheduler.run()` (every 30s) → Query due reminders → `send_reminder()` → Discord DM → Mark as sent

### User Model Switch
`/settings model X` → `main.py:model()` command → `agent.py:update_agent_model()` → Reinitialize agent

---

## 13 · Recommendations for Agent Assistance

When working with this codebase, prioritize:

1. **System Prompt Alignment:** Ensure tool behavior matches the documented directives in `dynamic_system_prompt()`.
2. **Async Safety:** All database/API calls must be `await`ed.
3. **User Context:** Always extract `user_id` from `ctx.deps['user_info']`.
4. **Error Handling:** Return user-friendly error strings from tools, not exceptions.
5. **Memory Integrity:** Zep memory is append-only; be careful with large message batches.
6. **Testing:** Write tests for new tools before integration.

---

---

## 14 · Coding Agent (Pi Coding Agent Capabilities)

### 14.1 Overview

Cortana includes coding agent capabilities ported from [badlogic/pi-mono](https://github.com/badlogic/pi-mono)'s `mom` package. This enables command execution, file management, and custom tool creation.

### 14.2 Skills System

Skills are custom CLI tools that Cortana can create and use for recurring tasks.

**Directory Structure:**
```
/workspace/
├── skills/                    # Global skills (shared)
│   └── skill-name/
│       ├── SKILL.md           # Skill definition
│       └── script.py          # Implementation
└── users/{user_id}/skills/    # User-specific skills
    └── skill-name/
        ├── SKILL.md
        └── ...
```

**SKILL.md Format:**
```markdown
---
name: skill-name
description: Short description
---

# Skill Name

Usage instructions here.
Scripts are in: {baseDir}/
```

### 14.3 Adding Coding Tools

1. **Define tool in `tools.py`:**
   ```python
   async def my_coding_tool(ctx: RunContext[Dict[str, Any]], param: str) -> str:
       """Tool description."""
       # Implementation
       return "Result"
   ```

2. **Register conditionally in `agent.py`:**
   ```python
   if config.ENABLE_MY_TOOL:
       agent.tool(my_coding_tool)
   ```

3. **Update system prompt** in `_get_coding_tools_prompt()` if needed.

### 14.4 Security Considerations

- Cortana runs in Docker, providing container isolation.
- Bash commands execute within the container's security context.
- File operations are restricted to the workspace directory.
- Timeout limits prevent runaway processes.
- Output truncation prevents memory exhaustion.

---

**Document Version:** 1.1  
**Last Updated:** January 26, 2025  
**Project:** Cortana Discord Bot
