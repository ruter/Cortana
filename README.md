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

### OAuth Support

Cortana supports OAuth credentials for providers that require them:

**Supported OAuth Providers:**
- **Gemini CLI** - Google Cloud authentication
- **Qwen Code** - Alibaba Cloud integration
- **Antigravity** - Custom provider
- **iFlow** - Workflow integration

**Configuration:**

```ini
# OAuth Credentials (file paths or JSON)
GEMINI_CLI_OAUTH_CREDENTIALS=/path/to/gemini_oauth.json
QWEN_CODE_OAUTH_CREDENTIALS=/path/to/qwen_oauth.json
ANTIGRAVITY_OAUTH_CREDENTIALS=/path/to/antigravity_oauth.json
IFLOW_OAUTH_CREDENTIALS=/path/to/iflow_oauth.json

# Optional: Provider-specific client credentials for token refresh
GEMINI_CLIENT_ID=your_client_id
GEMINI_CLIENT_SECRET=your_client_secret
QWEN_CLIENT_ID=your_client_id
QWEN_CLIENT_SECRET=your_client_secret
```

**Credential File Format:**

```json
{
  "access_token": "ya29.a0AfH6SMB...",
  "refresh_token": "1//0gP...",
  "token_type": "Bearer",
  "expires_at": 1645123456.1234
}
```

**Discord Commands:**

- `/settings oauth-status` - Show OAuth token expiry status
- `/settings oauth-refresh <provider>` - Manually refresh a token

**Important Notes:**
- Credentials file must be **writable** (rotator updates it with new tokens)
- Credentials must contain **refresh_token** for auto-refresh to work
- Tokens are automatically refreshed when about to expire
- Refresh failures are logged; rotator falls back to next credential if available

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

## Prerequisites

- Python 3.10+
- **Supabase** Project (PostgreSQL)
- **Zep** Account (Memory Service)
- **OpenAI**, **Anthropic**, or **Google** API Key(s)
- **Discord** Bot Token

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
│   ├── skills.py          # Skills System (Pi Coding Agent)
│   └── tools.py           # Agent Tools (Todos, Calendar, Coding)
├── tests/
│   ├── test_coding_tools.py       # Coding tools tests
│   ├── test_rotator_integration.py # Rotator integration tests
│   ├── test_skills.py             # Skills system tests
│   └── ...
├── workspace/             # Workspace directory (mounted volume)
│   └── skills/            # Global skills
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
