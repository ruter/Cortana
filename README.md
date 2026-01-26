![](https://img.shields.io/badge/Gemini%20Assisted-100%25-00a67d?logo=googlegemini)

# Cortana - Discord Personal Assistant

Cortana is an intelligent Discord bot designed to be a personalized digital companion. She features **bionic memory** (Short-Term & Long-Term), **task management** (Todos, Calendar), **coding agent capabilities**, and a unique personality.

Built with **Python**, **discord.py**, and **PydanticAI**, following a "Thin Client, Fat Cloud" architecture.

## Features

- 🧠 **Bionic Memory**: Powered by **Zep**. Remembers facts about you across conversations.
- ✅ **Task Management**: Manage To-Dos and Calendar events directly from Discord.
- 📅 **Calendar Integration**: Smart scheduling with conflict detection.
- 💬 **Natural Interaction**: Powered by LLMs (OpenAI/Anthropic) for fluid, witty conversations.
- ☁️ **Cloud Native**: Uses **Supabase** for data persistence and **Zep** for memory vectorization.
- 🛠️ **Coding Agent**: Execute commands, manage files, and create custom tools (skills).

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

## Prerequisites

- Python 3.10+
- **Supabase** Project (PostgreSQL)
- **Zep** Account (Memory Service)
- **OpenAI** or **Anthropic** API Key
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
   
   # LLM Configuration
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_API_KEY=...
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

To persist workspace data (skills, files), mount a volume:

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
      - ./workspace:/workspace
```

## Project Structure

```
cortana-bot/
├── src/
│   ├── agent.py           # PydanticAI Agent & System Prompt
│   ├── config.py          # Env Config
│   ├── database.py        # Supabase Client
│   ├── main.py            # Discord Client Entry Point
│   ├── memory.py          # Zep Client
│   ├── skills.py          # Skills System (Pi Coding Agent)
│   └── tools.py           # Agent Tools (Todos, Calendar, Coding)
├── tests/
│   ├── test_coding_tools.py  # Coding tools tests
│   ├── test_skills.py        # Skills system tests
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
- **Memory**: `Zep` provides long-term fact extraction and session context.
- **Storage**: `Supabase` stores structured business data.
- **Coding**: Pi Coding Agent tools for command execution and file management.

## Credits

Coding agent capabilities are inspired by and ported from [badlogic/pi-mono](https://github.com/badlogic/pi-mono)'s `mom` package ([@mariozechner/pi-mom](https://www.npmjs.com/package/@mariozechner/pi-mom)).
