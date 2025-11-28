# Cortana - Discord Personal Assistant

Cortana is an intelligent Discord bot designed to be a personalized digital companion. She features **bionic memory** (Short-Term & Long-Term), **task management** (Todos, Calendar), and a unique personality.

Built with **Python**, **discord.py**, and **PydanticAI**, following a "Thin Client, Fat Cloud" architecture.

## Features

- 🧠 **Bionic Memory**: Powered by **Zep**. Remembers facts about you across conversations.
- ✅ **Task Management**: Manage To-Dos and Calendar events directly from Discord.
- 📅 **Calendar Integration**: Smart scheduling with conflict detection.
- 💬 **Natural Interaction**: Powered by LLMs (OpenAI/Anthropic) for fluid, witty conversations.
- ☁️ **Cloud Native**: Uses **Supabase** for data persistence and **Zep** for memory vectorization.

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
   
   # LLM Configuration
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_API_KEY=...
   LLM_MODEL_NAME=gpt-4o
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

## Project Structure

```
cortana-bot/
├── src/
│   ├── agent.py           # PydanticAI Agent & System Prompt
│   ├── config.py          # Env Config
│   ├── database.py        # Supabase Client
│   ├── main.py            # Discord Client Entry Point
│   ├── memory.py          # Zep Client
│   └── tools.py           # Agent Tools (Todos, Calendar, etc.)
├── tests/                 # Verification scripts
├── schema.sql             # Database Schema
├── requirements.txt       # Python Dependencies
└── README.md              # Documentation
```

## Architecture

- **Interface**: `discord.py` handles real-time events.
- **Brain**: `PydanticAI` orchestrates the LLM and tools.
- **Memory**: `Zep` provides long-term fact extraction and session context.
- **Storage**: `Supabase` stores structured business data.
