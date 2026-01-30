![](https://img.shields.io/badge/Gemini%20Assisted-100%25-00a67d?logo=googlegemini)

# Cortana - Discord Personal Assistant

Cortana is an intelligent Discord bot designed to be a personalized digital companion. She features **bionic memory** (Short-Term & Long-Term), **task management** (Todos, Calendar), **coding agent capabilities**, **resilient multi-provider LLM access**, and a unique personality.

Built with **Python**, **discord.py**, and **PydanticAI**, following a "Thin Client, Fat Cloud" architecture.

## Features

- 🧠 **Bionic Memory**: Powered by **Zep**. Remembers facts about you across conversations.
- ✅ **Task Management**: Manage To-Dos and Calendar events directly from Discord.
- 📅 **Calendar Integration**: Smart scheduling with conflict detection.
- 💬 **Natural Interaction**: Powered by LLMs (OpenAI/Anthropic/Google) for fluid, witty conversations.
- ☁️ **Cloud Native**: Uses **Supabase** for data persistence and **Zep** for memory vectorization.
- 🛠️ **Coding Agent**: Execute commands, manage files, and create custom tools (skills).
- 🔄 **API Key Rotation**: Resilient multi-key, multi-provider LLM access with automatic failover.
- 💬 **Conversation Cache**: In-memory conversation history with TTL-based expiration and auto-compaction.
- 🔒 **Master User Access**: Secure access control - only the designated master user can interact with Cortana via DM.

## API Key Rotation (rotator_library)

Cortana integrates [rotator_library](https://github.com/Mirrowel/LLM-API-Key-Proxy) for resilient LLM access across multiple providers and API keys.

### Benefits

- **High Availability**: Automatic failover when a key is exhausted or rate-limited
- **Cost Optimization**: Distribute load across multiple keys to stay within free tiers
- **Multi-Provider Support**: Seamlessly switch between OpenAI, Anthropic, Google Gemini, DeepSeek, Qwen, and more
- **Smart Key Selection**: Weighted random or deterministic selection for load balancing
- **Escalating Cooldowns**: Failed keys are temporarily removed from rotation with increasing cooldown periods

### Configuration

#### Multi-Key Setup

Add multiple API keys using the pattern `<PROVIDER>_API_KEY` or `<PROVIDER>_API_KEY_<N>`:

```ini
# Multiple OpenAI keys
OPENAI_API_KEY_1=sk-xxx...
OPENAI_API_KEY_2=sk-yyy...

# Multiple Gemini keys
GEMINI_API_KEY_1=AIza...
GEMINI_API_KEY_2=AIza...

# Single Anthropic key
ANTHROPIC_API_KEY=sk-ant-...

# Enable the rotator (default: true)
ENABLE_ROTATOR=true
```

#### OAuth Credentials (Advanced)

For providers requiring OAuth (Gemini CLI, Qwen Code, Antigravity, iFlow):

```ini
# Gemini CLI OAuth
GEMINI_CLI_OAUTH_CREDENTIALS=/path/to/gemini_oauth.json

# Antigravity OAuth (supports Gemini 3, Claude, GPT-OSS)
ANTIGRAVITY_OAUTH_CREDENTIALS=/path/to/antigravity_oauth.json
```

#### Rotator Tuning

```ini
# Retry settings
ROTATOR_MAX_RETRIES=2
ROTATOR_GLOBAL_TIMEOUT=120

# Rotation strategy
ROTATOR_ROTATION_TOLERANCE=2.0
# 0.0 = deterministic (always pick least-used key)
# 2.0 = weighted random (recommended, harder to fingerprint)
# 5.0+ = high randomness

# Usage tracking
ROTATOR_USAGE_FILE_PATH=key_usage.json
```

### Discord Commands

| Command | Description |
|---------|-------------|
| `/settings model <name>` | Change the active LLM model (e.g., `gpt-4o`, `openai/gpt-4o`, `gemini/gemini-2.5-flash`) |
| `/settings status` | Show current model and API key pool status |
| `/settings models [provider]` | List available models for a provider |

### Backward Compatibility

If you prefer the legacy single-key mode, simply set:

```ini
LLM_API_KEY=your_key
ENABLE_ROTATOR=false
```

The rotator will also auto-wrap a single `LLM_API_KEY` if no provider-specific keys are found.

---

## Conversation Cache

Cortana maintains an in-memory conversation cache that preserves context across messages within a session. This ensures continuity in conversations without losing important context.

### Features

- **TTL-based Expiration**: Conversations automatically expire after a period of inactivity (default: 30 minutes). Each interaction resets the timer (sliding window TTL).
- **Auto-Compaction**: When the conversation approaches the model's context limit (80% by default), older messages are summarized by the LLM and the conversation is compacted.
- **Crash Recovery**: Conversation state is persisted to disk for recovery after restarts.
- **Model-Aware**: Uses `litellm` to dynamically fetch context limits for any model.

### Configuration

```ini
# Time-to-live for conversations (seconds, default: 1800 = 30 minutes)
CONVERSATION_TTL_SECONDS=1800

# Token threshold for compaction (fraction of model context limit, default: 0.8)
CONVERSATION_TOKEN_THRESHOLD=0.8

# Number of recent message pairs to keep after compaction (default: 3)
CONVERSATION_KEEP_RECENT=3
```

### How It Works

1. **Normal Flow**: Messages are cached and sent as conversation history to the LLM.
2. **TTL Expiration**: After 30 minutes of inactivity, the conversation is cleared (fresh start).
3. **Compaction Trigger**: When token count exceeds 80% of the model's context limit:
   - Old messages are summarized by the LLM
   - Only the last 3 message pairs are retained
   - The summary is prepended to future requests
   - TTL is reset

### Persistence

Conversation state is saved to `{WORKSPACE_DIR}/.conversation_cache/` as JSON files. This allows recovery after bot restarts.

---

## Coding Agent Capabilities

Cortana now includes **Pi Coding Agent** capabilities, ported from [badlogic/pi-mono](https://github.com/badlogic/pi-mono)'s `mom` package. This enables:

### Coding Tools

| Tool | Description |
|------|-------------|
| `execute_bash` | Execute shell commands in the container environment |
| `read_file` | Read file contents with optional line range |
| `write_file` | Create or overwrite files |
| `edit_file` | Make surgical edits to existing files |

### Skills System

Skills are custom CLI tools that Cortana can create and use for recurring tasks. Each skill is a directory containing a `SKILL.md` file with YAML frontmatter.

**Creating a Skill:**

```markdown
---
name: my-skill
description: Does something useful
---

# My Skill

Usage instructions here.
Scripts are in: {baseDir}/
```

**Skill Locations:**
- Global skills: `/workspace/skills/<skill-name>/`
- User-specific skills: `/workspace/users/<user_id>/skills/<skill-name>/`

### Configuration

Enable/disable coding features via environment variables:

```ini
# Feature Toggles
ENABLE_BASH_TOOL=true
ENABLE_FILE_TOOLS=true
ENABLE_SKILLS=true

# Workspace Configuration
WORKSPACE_DIR=/workspace
SKILLS_DIR=/workspace/skills

# Tool Limits
BASH_TIMEOUT_DEFAULT=60
BASH_OUTPUT_MAX_LINES=500
BASH_OUTPUT_MAX_BYTES=51200
FILE_READ_MAX_LINES=1000
```

---

## Access Control

Cortana implements strict access control to ensure only the designated master user can interact with the bot.

### Access Restrictions

- **🔒 Master User Only**: Only the user specified by `MASTER_USER_ID` can interact with Cortana
- **📩 DM Only**: Cortana only responds to Direct Messages (DM). All channel interactions are blocked:
  - Regular messages in channels are ignored
  - Slash commands (`/settings`, etc.) cannot be used in channels
  - Only DM interactions are permitted

### Required Configuration

The `MASTER_USER_ID` environment variable is **required** for the bot to start. If not configured, the bot will fail to initialize with an error message.

### How to Get Your Discord User ID

1. Enable **Developer Mode** in Discord:
   - Go to **Settings** → **Advanced**
   - Toggle **Developer Mode** on
   
2. Copy your User ID:
   - Right-click on your Discord profile
   - Select **Copy User ID**

3. Set the environment variable:
   ```ini
   MASTER_USER_ID=123456789012345678
   ```

### Behavior Summary

| Scenario | Behavior |
|----------|----------|
| Master user sends DM to bot | ✅ Responds normally |
| Non-master user sends DM to bot | ❌ Ignores message |
| Any message in a channel | ❌ Ignored (even from master user) |
| Slash command in a channel | ❌ Blocked with error message |
| Slash command in DM (master user) | ✅ Executes normally |
| Slash command in DM (non-master) | ❌ Unauthorized error |

---

## Prerequisites

- Python 3.10+
- **Supabase** Project (PostgreSQL)
- **Zep** Account (Memory Service)
- **OpenAI**, **Anthropic**, or **Google** API Key(s)
- **Discord** Bot Token
- **Discord** User ID (for master user access control)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cortana-bot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
   
   ```ini
   DISCORD_TOKEN=...
   SUPABASE_URL=...
   SUPABASE_KEY=...
   ZEP_API_KEY=...
   EXA_API_KEY=...
   
   # Master User ID (Required)
   # Get your Discord User ID: Settings → Advanced → Enable Developer Mode → Right-click your profile → Copy User ID
   MASTER_USER_ID=123456789012345678
   
   # LLM Configuration (multi-key recommended)
   OPENAI_API_KEY_1=...
   OPENAI_API_KEY_2=...
   GEMINI_API_KEY_1=...
   LLM_MODEL_NAME=gpt-4o
   
   # Coding Agent (optional)
   ENABLE_BASH_TOOL=true
   ENABLE_FILE_TOOLS=true
   ENABLE_SKILLS=true
   WORKSPACE_DIR=/workspace
   ```

4. **Database Initialization**
   Run the SQL script `schema.sql` in your Supabase SQL Editor to create the necessary tables (`user_settings`, `todos`, `calendar_events`).

## Usage

Run the bot:
```bash
python -m src.main
```

## Deployment with Docker

### Using Docker Compose (Recommended)

1.  Ensure you have Docker and Docker Compose installed.
2.  Create your `.env` file as described in the Installation section.
3.  Run the bot:
    ```bash
    docker-compose up -d
    ```
4.  View logs:
    ```bash
    docker-compose logs -f
    ```

### Using Docker Manually

1.  Build the image:
    ```bash
    docker build -t cortana-bot .
    ```
2.  Run the container:
    ```bash
    docker run -d --name cortana-bot --env-file .env cortana-bot
    ```

### Workspace Volume (for Coding Agent)

To persist workspace data (skills, files, key usage):

```bash
docker run -d --name cortana-bot \
  --env-file .env \
  -v /path/to/workspace:/workspace \
  cortana-bot
```

Or in `docker-compose.yml`:

```yaml
services:
  cortana:
    # ... other config
    volumes:
      - cortana-workspace:/workspace
      # Optional: OAuth credentials
      # - ./credentials:/app/credentials:ro

volumes:
  cortana-workspace:
```

## Prompt System

Cortana uses a modular, file-based prompt system that allows for dynamic personality and context management. All prompt files are located in the workspace directory (`WORKSPACE_DIR`).

### Prompt Files

| File | Type | Description |
|------|------|-------------|
| `IDENTITY.md` | Read-Only | Core role, mission, language protocol, immutable constraints |
| `SOUL.md` | **Read/Write** | Personality traits, humor style, tone guidelines. Cortana can update this to evolve |
| `USER.md` | **Read/Write** | User profile, preferences, learned context. Cortana updates this with new learnings |
| `TOOLS.md` | Read-Only | Tool usage policies, time awareness rules, reminder guidelines |

### Self-Evolution

Cortana can modify `SOUL.md` and `USER.md` using the `edit_file` tool, enabling:

- **Personality Evolution**: Adjusting tone, humor style, or expression patterns based on feedback
- **Context Learning**: Recording user preferences and facts for better personalization

### Setup

Copy the prompt files to your workspace directory:

```bash
cp IDENTITY.md SOUL.md USER.md TOOLS.md /path/to/workspace/
```

Or in Docker, mount them as part of the workspace volume.

---

## Project Structure

```
cortana-bot/
├── src/
│   ├── agent.py           # PydanticAI Agent & System Prompt
│   ├── config.py          # Env Config (with rotator key loading)
│   ├── database.py        # Supabase Client
│   ├── main.py            # Discord Client Entry Point
│   ├── memory.py          # Zep Client
│   ├── rotator_client.py  # RotatingClient Singleton & Helpers
│   ├── conversation_cache.py # In-memory conversation cache with TTL
│   ├── skills.py          # Skills System (Pi Coding Agent)
│   └── tools.py           # Agent Tools (Todos, Calendar, Coding)
├── tests/
│   ├── test_coding_tools.py       # Coding tools tests
│   ├── test_rotator_integration.py # Rotator integration tests
│   ├── test_skills.py             # Skills system tests
│   ├── test_conversation_cache.py # Conversation cache tests
│   └── ...
├── workspace/             # Workspace directory (mounted volume)
│   ├── skills/            # Global skills
│   ├── IDENTITY.md        # Core identity (read-only)
│   ├── SOUL.md            # Personality (read/write)
│   ├── USER.md            # User context (read/write)
│   └── TOOLS.md           # Tool policies (read-only)
├── IDENTITY.md            # Default prompt files (copy to workspace)
├── SOUL.md
├── USER.md
├── TOOLS.md
├── schema.sql             # Database Schema
├── requirements.txt       # Python Dependencies
└── README.md              # Documentation
```

## Architecture

- **Interface**: `discord.py` handles real-time events.
- **Brain**: `PydanticAI` orchestrates the LLM and tools.
- **LLM Access**: `rotator_library` provides resilient, multi-key API access.
- **Memory**: `Zep` provides long-term fact extraction and session context.
- **Storage**: `Supabase` stores structured business data.
- **Coding**: Pi Coding Agent tools for command execution and file management.

## Credits

- Coding agent capabilities are inspired by and ported from [badlogic/pi-mono](https://github.com/badlogic/pi-mono)'s `mom` package ([@mariozechner/pi-mom](https://www.npmjs.com/package/@mariozechner/pi-mom)).
- API key rotation powered by [rotator_library](https://github.com/Mirrowel/LLM-API-Key-Proxy).
