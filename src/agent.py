"""
Cortana Agent Module
====================

Defines the CortanaAgent with dynamic system prompts, tool registration,
and integration with the RotatingClient for resilient LLM access.
"""

import logging
import asyncio
import functools
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .config import config
from .cortana_context import CortanaContext
from .cortana_agent import CortanaAgent
from .tools import (
    add_todo, list_todos, complete_todo,
    add_calendar_event, check_calendar_availability,
    search_long_term_memory, get_unread_emails,
    add_reminder, list_reminders, cancel_reminder,
    fetch_url, search_web_exa, get_contents_exa,
    execute_bash, read_file, write_file, edit_file
)
from .skills import load_all_skills, format_skills_for_prompt
from .rotator_client import normalize_model_name, get_key_pool_status

logger = logging.getLogger(__name__)


def _read_prompt_file_sync(filename: str) -> str:
    """
    Safely read a prompt file from the workspace directory (synchronous).

    Args:
        filename: Name of the file to read (e.g., 'IDENTITY.md').

    Returns:
        File content as string, or empty string if file doesn't exist.
    """
    file_path = Path(config.WORKSPACE_DIR) / filename
    try:
        return file_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logger.warning(f"Prompt file not found: {filename}")
        return ""
    except Exception as e:
        logger.error(f"Error reading prompt file {filename}: {e}")
        return ""


async def read_prompt_file(filename: str) -> str:
    """
    Safely read a prompt file from the workspace directory (asynchronous).

    Args:
        filename: Name of the file to read (e.g., 'IDENTITY.md').

    Returns:
        File content as string, or empty string if file doesn't exist.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _read_prompt_file_sync, filename)


async def _get_skills_prompt_async(user_id: str) -> str:
    """Generate the available skills section of the system prompt."""
    if not config.ENABLE_SKILLS:
        return ""

    loop = asyncio.get_running_loop()
    # load_all_skills does directory scanning, so we run it in executor
    skills = await loop.run_in_executor(
        None,
        functools.partial(load_all_skills, config.WORKSPACE_DIR, user_id)
    )

    if not skills:
        return ""

    skills_section = format_skills_for_prompt(skills)

    return f"""
## Available Skills

{skills_section}
"""


async def dynamic_system_prompt(ctx: CortanaContext) -> str:
    """Generate the dynamic system prompt based on context."""
    user_info = ctx.deps.get("user_info", {})
    user_id = str(user_info.get('id', 'unknown'))

    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(config.DEFAULT_TIMEZONE)
    except Exception:
        try:
            import pytz
            tz = pytz.timezone(config.DEFAULT_TIMEZONE)
        except Exception:
            from datetime import timezone
            tz = timezone.utc

    now = datetime.now(tz)
    current_time = now.isoformat()
    day_of_week = now.strftime('%A')

    zep_memory_context = ctx.deps.get("zep_memory_context", "No previous context.")

    # Load prompt files concurrently
    identity_content, soul_content, user_content, tools_content, skills_prompt = await asyncio.gather(
        read_prompt_file("IDENTITY.md"),
        read_prompt_file("SOUL.md"),
        read_prompt_file("USER.md"),
        read_prompt_file("TOOLS.md"),
        _get_skills_prompt_async(user_id)
    )
    
    workspace_dir = config.WORKSPACE_DIR

    soul_content = soul_content.replace("{WORKSPACE_DIR}", workspace_dir)
    
    user_content = user_content.replace(
        "{WORKSPACE_DIR}", workspace_dir
    ).replace(
        "- **Name:** (Loaded from context)",
        f"- **Name:** {user_info.get('name', 'Unknown')}"
    ).replace(
        "- **ID:** (Loaded from context)",
        f"- **ID:** {user_info.get('id', 'Unknown')}"
    ).replace(
        "- **Timezone:** (Loaded from config)",
        f"- **Timezone:** {config.DEFAULT_TIMEZONE}"
    )

    prompt = f"""
{identity_content}

---

{soul_content}

---

{user_content}

---

# Current Time

- **Now:** {current_time} ({day_of_week})
- **Timezone:** {config.DEFAULT_TIMEZONE}

## Retrieved Memory (Powered by Zep)

<RETRIEVED_MEMORY>
{zep_memory_context}
</RETRIEVED_MEMORY>

---

{tools_content}
{skills_prompt}
"""
    return prompt


def initialize_agent(model_name: Optional[str] = None) -> CortanaAgent:
    """
    Initialize the Cortana agent with the specified model.

    Uses RotatingClient for API key management via rotator_client.

    Args:
        model_name: Optional model name override. Defaults to config.LLM_MODEL_NAME.

    Returns:
        Configured CortanaAgent instance.
    """
    if model_name is None:
        model_name = config.LLM_MODEL_NAME

    config.load_rotator_keys()

    normalized = normalize_model_name(model_name)
    logger.info(f"Initializing agent with model: {normalized}")

    agent = CortanaAgent(model=normalized, max_steps=15)

    agent.system_prompt(dynamic_system_prompt)

    _register_agent_tools(agent)

    return agent


def _register_agent_tools(agent: CortanaAgent) -> None:
    """Register all tools with the agent."""

    agent.tool(add_todo)
    agent.tool(list_todos)
    agent.tool(complete_todo)
    agent.tool(add_calendar_event)
    agent.tool(check_calendar_availability)
    agent.tool(search_long_term_memory)
    agent.tool(get_unread_emails)
    agent.tool(add_reminder)
    agent.tool(list_reminders)
    agent.tool(cancel_reminder)
    agent.tool(fetch_url)

    if config.EXA_API_KEY:
        agent.tool(search_web_exa)
        agent.tool(get_contents_exa)

    if config.ENABLE_BASH_TOOL:
        agent.tool(execute_bash)

    if config.ENABLE_FILE_TOOLS:
        agent.tool(read_file)
        agent.tool(write_file)
        agent.tool(edit_file)

    logger.debug("Agent tools registered successfully")


def update_agent_model(model_name: str) -> None:
    """
    Update the agent to use a different model.

    Args:
        model_name: The new model name to use.
    """
    global cortana_agent

    normalized = normalize_model_name(model_name)
    config.LLM_MODEL_NAME = normalized

    logger.info(f"Updating agent model to: {normalized}")

    cortana_agent = initialize_agent(normalized)


async def get_agent_status() -> Dict[str, Any]:
    """
    Get the current agent and rotator status.

    Returns:
        Dict with model info, rotator status, and available providers.
    """
    pool_status = await get_key_pool_status()

    return {
        "current_model": config.LLM_MODEL_NAME,
        "normalized_model": normalize_model_name(config.LLM_MODEL_NAME),
        **pool_status
    }


cortana_agent = initialize_agent()
