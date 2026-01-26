# Cortana: Your Bionic Personal Assistant

Cortana is a high-performance, proactive personal assistant bot for Discord, designed to manage your life with precision and a touch of wit. 
Built with **Python**, **discord.py**, and **PydanticAI**, following a "Thin Client, Fat Cloud" architecture.

## Features

- 🧠 **Bionic Memory**: Powered by **Zep**. Remembers facts about you across conversations.
- ✅ **Task Management**: Manage To-Dos and Calendar events directly from Discord.
- 📅 **Calendar Integration**: Smart scheduling with conflict detection.
- 💬 **Natural Interaction**: Powered by LLMs (OpenAI/Anthropic/Google) for fluid, witty conversations.
- ☁️ **Cloud Native**: Uses **Supabase** for data persistence and **Zep** for memory vectorization.
- 🛠️ **Coding Agent**: Execute commands, manage files, and create custom tools (skills).
- 🤖 **Provider & Model Management**: Support for multiple AI providers and models, including OAuth login for user-owned accounts.

## Prerequisites

- **Python 3.10+**
- **Supabase** Account (Database)
- **Zep Cloud** Account (Memory Service)
- **OpenAI** or **Anthropic** API Key
- **Discord** Bot Token

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ruter/Cortana.git
    cd Cortana
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Copy `.env.example` to `.env` and fill in your credentials.
    ```bash
    cp .env.example .env
    ```

4.  **Database Setup:**
    Run the SQL script `schema.sql` in your Supabase SQL Editor to create the necessary tables (`user_settings`, `todos`, `calendar_events`, `provider_credentials`).

## Usage

Run the bot:
```bash
python -m src.main
```

### Provider & Model Commands

| Command | Description |
|---------|-------------|
| `/models` | List all available AI models and providers |
| `/settings model <model_id>` | Switch the active model for the session |
| `/login <provider_id>` | Login to a provider (e.g., `anthropic`) to use your own account |

## Deployment with Docker

### Using Docker Compose (Recommended)

1.  Ensure you have Docker and Docker Compose installed.
2.  Update the `.env` file with your production credentials.
3.  Build and start the container:
    ```bash
    docker-compose up -d --build
    ```

## Documentation

- [Agent Architecture & Guidance](AGENTS.md) - Detailed guide on how Cortana's brain works.

## License

MIT
