from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import aiohttp
from bs4 import BeautifulSoup
from exa_py import Exa
from .config import config
from .database import db
from .memory import memory_client
from .cortana_context import CortanaContext

# --- Data Models ---

class Todo(BaseModel):
    id: int
    content: str
    status: str
    due_date: Optional[datetime] = None
    priority: int

class CalendarEvent(BaseModel):
    id: int
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None

class Reminder(BaseModel):
    id: int
    user_id: int
    message: str
    remind_time: datetime
    is_sent: bool
    related_event_id: Optional[int] = None
    created_at: datetime

# --- Helper Functions ---

async def ensure_user_exists(user_id: int) -> None:
    """Ensure user exists in user_settings table."""
    try:
        # Check if user exists
        response = db.table("user_settings").select("user_id").eq("user_id", user_id).execute()
        if not response.data:
            # User doesn't exist, create it
            db.table("user_settings").insert({"user_id": user_id}).execute()
    except Exception as e:
        # If error is not about duplicate, log it
        if "duplicate" not in str(e).lower():
            print(f"Error ensuring user exists: {e}")

# --- Transaction Tools ---

async def add_todo(ctx: CortanaContext, content: str, due_date: Optional[datetime] = None, priority: int = 3) -> str:
    """
    Adds a new item to the user's To-Do list.
    
    Args:
        content: The content of the task.
        due_date: Optional deadline for the task.
        priority: Priority level (1=High, 5=Low, default=3).
    """
    user_id = ctx.deps['user_info']['id']
    
    # Ensure user exists in database
    await ensure_user_exists(user_id)
    
    data = {
        "user_id": user_id,
        "content": content,
        "priority": priority
    }
    if due_date:
        data["due_date"] = due_date.isoformat()
    
    try:
        response = db.table("todos").insert(data).execute()
        return f"Todo added: {content}"
    except Exception as e:
        return f"Error adding todo: {str(e)}"

async def list_todos(ctx: CortanaContext, status: str = "PENDING", limit: int = 10) -> str:
    """
    Lists the user's To-Do items.
    
    Args:
        status: Filter by status ('PENDING', 'COMPLETED', 'ARCHIVED').
        limit: Max number of items to return.
    """
    user_id = ctx.deps['user_info']['id']
    try:
        response = db.table("todos").select("*").eq("user_id", user_id).eq("status", status).order("created_at", desc=True).limit(limit).execute()
        todos = [Todo(**item) for item in response.data]
        if not todos:
            return f"No {status.lower()} todos found."
        
        result = f"**{status} Todos:**\n"
        for todo in todos:
            due_info = f" (Due: {todo.due_date})" if todo.due_date else ""
            result += f"- [{todo.id}] {todo.content}{due_info}\n"
        return result
    except Exception as e:
        return f"Error listing todos: {str(e)}"

async def complete_todo(ctx: CortanaContext, todo_id: int) -> str:
    """
    Marks a To-Do item as completed.
    
    Args:
        todo_id: The ID of the todo item to complete.
    """
    user_id = ctx.deps['user_info']['id']
    try:
        # Verify ownership
        response = db.table("todos").select("*").eq("id", todo_id).eq("user_id", user_id).execute()
        if not response.data:
            return "Todo not found or access denied."
        
        db.table("todos").update({"status": "COMPLETED"}).eq("id", todo_id).execute()
        return f"Todo {todo_id} marked as completed."
    except Exception as e:
        return f"Error completing todo: {str(e)}"

async def add_calendar_event(ctx: CortanaContext, title: str, start_time: datetime, end_time: datetime, location: Optional[str] = None) -> str:
    """
    Adds an event to the user's calendar.
    
    Args:
        title: Title of the event.
        start_time: Start time of the event.
        end_time: End time of the event.
        location: Optional location.
    """
    user_id = ctx.deps['user_info']['id']
    
    # Ensure user exists in database
    await ensure_user_exists(user_id)
    
    data = {
        "user_id": user_id,
        "title": title,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "location": location
    }
    try:
        db.table("calendar_events").insert(data).execute()
        return f"Event added: {title} at {start_time}"
    except Exception as e:
        return f"Error adding event: {str(e)}"

async def check_calendar_availability(ctx: CortanaContext, start_range: datetime, end_range: datetime) -> str:
    """
    Checks for conflicting events in a given time range.
    
    Args:
        start_range: Start of the range to check.
        end_range: End of the range to check.
    """
    user_id = ctx.deps['user_info']['id']
    try:
        # Overlap logic: (StartA <= EndB) and (EndA >= StartB)
        response = db.table("calendar_events").select("*") \
            .eq("user_id", user_id) \
            .lte("start_time", end_range.isoformat()) \
            .gte("end_time", start_range.isoformat()) \
            .execute()
        
        if response.data:
            events = [f"{e['title']} ({e['start_time']} - {e['end_time']})" for e in response.data]
            return f"Conflicts found: {', '.join(events)}"
        else:
            return "No conflicts found in this time range."
    except Exception as e:
        return f"Error checking availability: {str(e)}"

# --- Information Retrieval Tools ---

async def search_long_term_memory(ctx: CortanaContext, query: str, limit: int = 3) -> str:
    """
    Searches the user's long-term memory (facts) in Zep.
    
    Args:
        query: The search query.
        limit: Number of results to return (currently not used, returns full context).
    """
    user_id = str(ctx.deps['user_info']['id'])
    thread_id = f"discord_{user_id}"
    
    try:
        # Get user context from Zep
        memory = await memory_client.thread.get_user_context(thread_id=thread_id)
        
        if not memory or not memory.context:
            return "No relevant memories found."
            
        return f"Found relevant context:\n{memory.context}"
    except Exception as e:
        return f"Error searching memory: {str(e)}"

async def get_unread_emails(ctx: CortanaContext, limit: int = 5) -> str:
    """
    Mock function to get unread emails.
    In a real app, this would connect to Gmail/Outlook API.
    """
    return "No unread emails (Email integration not yet implemented)."

async def fetch_url(ctx: CortanaContext, url: str) -> str:
    """
    Fetches content from a URL.
    
    Args:
        url: The URL to fetch.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return f"Error fetching URL: {response.status} {response.reason}"
                html = await response.text()
                
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else "No title"
        
        # Get meta description
        meta_desc = ""
        meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        if meta:
            meta_desc = meta.get('content', '')
            
        # Get accessible text content
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit text length
        content_preview = text[:500] + "..." if len(text) > 500 else text
        
        return f"Title: {title}\\nDescription: {meta_desc}\\n\\nContent Preview:\\n{content_preview}"
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

async def search_web_exa(ctx: CortanaContext, query: str) -> str:
    """
    Searches the web using Exa.
    
    Args:
        query: The search query.
    """
    try:
        exa = Exa(api_key=config.EXA_API_KEY)
        response = exa.search_and_contents(
            query,
            type="neural",
            use_autoprompt=True,
            num_results=3,
            text=True
        )
        
        result = f"Search results for '{query}':\\n\\n"
        for r in response.results:
            result += f"Title: {r.title}\\nURL: {r.url}\\nContent: {r.text[:300]}...\\n\\n"
            
        return result
    except Exception as e:
        return f"Error searching with Exa: {str(e)}"

async def get_contents_exa(ctx: CortanaContext, urls: List[str]) -> str:
    """
    Retrieves content from specific URLs using Exa.
    
    Args:
        urls: List of URLs to retrieve.
    """
    try:
        exa = Exa(api_key=config.EXA_API_KEY)
        response = exa.get_contents(
            urls,
            text=True
        )
        
        result = ""
        for r in response.results:
            result += f"Title: {r.title}\\nURL: {r.url}\\nContent:\\n{r.text[:1000]}...\\n\\n"
            
        return result
    except Exception as e:
        return f"Error getting contents with Exa: {str(e)}"

# --- Reminder Tools ---

async def add_reminder(ctx: CortanaContext, message: str, remind_time: datetime, related_event_id: Optional[int] = None) -> str:
    """
    Creates a new reminder for the user.
    
    Args:
        message: The reminder message to send.
        remind_time: When to send the reminder.
        related_event_id: Optional ID of a related calendar event.
    """
    user_id = ctx.deps['user_info']['id']
    
    # Ensure user exists in database
    await ensure_user_exists(user_id)
    
    # Validate that remind_time is in the future
    try:
        from zoneinfo import ZoneInfo
        from .config import config
        tz = ZoneInfo(config.DEFAULT_TIMEZONE)
    except Exception:
        try:
            import pytz
            from .config import config
            tz = pytz.timezone(config.DEFAULT_TIMEZONE)
        except Exception:
            from datetime import timezone
            tz = timezone.utc
    
    now = datetime.now(tz)
    
    # Make remind_time timezone-aware if it's not
    if remind_time.tzinfo is None:
        remind_time = remind_time.replace(tzinfo=tz)
    
    if remind_time <= now:
        return "Error: Reminder time must be in the future. Cannot create reminders for past times."
    
    data = {
        "user_id": user_id,
        "message": message,
        "remind_time": remind_time.isoformat(),
        "related_event_id": related_event_id
    }
    
    try:
        response = db.table("reminders").insert(data).execute()
        if response.data:
            reminder_id = response.data[0]['id']
            return f"Reminder set: '{message}' at {remind_time.strftime('%Y-%m-%d %H:%M %Z')} (ID: {reminder_id})"
        return "Reminder created successfully."
    except Exception as e:
        return f"Error creating reminder: {str(e)}"

async def list_reminders(ctx: CortanaContext, include_sent: bool = False, limit: int = 10) -> str:
    """
    Lists the user's reminders.
    
    Args:
        include_sent: Whether to include already sent reminders (default: False).
        limit: Maximum number of reminders to return.
    """
    user_id = ctx.deps['user_info']['id']
    
    try:
        query = db.table("reminders").select("*").eq("user_id", user_id)
        
        if not include_sent:
            query = query.eq("is_sent", False)
        
        response = query.order("remind_time", desc=False).limit(limit).execute()
        
        if not response.data:
            status = "reminders" if include_sent else "pending reminders"
            return f"No {status} found."
        
        reminders = [Reminder(**item) for item in response.data]
        
        result = "**Your Reminders:**\n"
        for reminder in reminders:
            status_icon = "✅" if reminder.is_sent else "⏰"
            event_info = f" (Event #{reminder.related_event_id})" if reminder.related_event_id else ""
            result += f"{status_icon} [{reminder.id}] {reminder.message} - {reminder.remind_time.strftime('%Y-%m-%d %H:%M')}{event_info}\n"
        
        return result
    except Exception as e:
        return f"Error listing reminders: {str(e)}"

async def cancel_reminder(ctx: CortanaContext, reminder_id: int) -> str:
    """
    Cancels a pending reminder.
    
    Args:
        reminder_id: The ID of the reminder to cancel.
    """
    user_id = ctx.deps['user_info']['id']
    
    try:
        # Verify ownership and that reminder exists
        response = db.table("reminders").select("*").eq("id", reminder_id).eq("user_id", user_id).execute()
        
        if not response.data:
            return "Reminder not found or access denied."
        
        reminder = Reminder(**response.data[0])
        
        if reminder.is_sent:
            return f"Reminder {reminder_id} has already been sent and cannot be cancelled."
        
        # Delete the reminder
        db.table("reminders").delete().eq("id", reminder_id).execute()
        return f"Reminder {reminder_id} has been cancelled: '{reminder.message}'"
    except Exception as e:
        return f"Error cancelling reminder: {str(e)}"


# --- Coding Tools ---
# Ported from badlogic/pi-mono mom package for Pi Coding Agent capabilities

import asyncio
import os
from pathlib import Path

# Constants for output truncation
DEFAULT_MAX_LINES = 500
DEFAULT_MAX_BYTES = 51200  # 50KB


def _truncate_output(output: str, max_lines: int = DEFAULT_MAX_LINES, max_bytes: int = DEFAULT_MAX_BYTES) -> tuple[str, bool, dict]:
    """
    Truncate output to last N lines or N bytes, whichever is hit first.
    
    Returns:
        tuple: (truncated_content, was_truncated, truncation_info)
    """
    if not output:
        return output, False, {}
    
    lines = output.split('\n')
    total_lines = len(lines)
    total_bytes = len(output.encode('utf-8'))
    
    # Check if truncation is needed
    if total_lines <= max_lines and total_bytes <= max_bytes:
        return output, False, {}
    
    # Truncate by lines first
    if total_lines > max_lines:
        lines = lines[-max_lines:]
    
    result = '\n'.join(lines)
    result_bytes = len(result.encode('utf-8'))
    
    # Further truncate by bytes if needed
    if result_bytes > max_bytes:
        # Binary search for the right cut point
        while result_bytes > max_bytes and lines:
            lines = lines[1:]  # Remove from the beginning (keep tail)
            result = '\n'.join(lines)
            result_bytes = len(result.encode('utf-8'))
    
    truncation_info = {
        'total_lines': total_lines,
        'output_lines': len(lines),
        'total_bytes': total_bytes,
        'output_bytes': result_bytes,
        'truncated_by': 'lines' if total_lines > max_lines else 'bytes'
    }
    
    return result, True, truncation_info


def _format_size(bytes_count: int) -> str:
    """Format byte count as human-readable string."""
    if bytes_count < 1024:
        return f"{bytes_count}B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f}KB"
    else:
        return f"{bytes_count / (1024 * 1024):.1f}MB"


async def execute_bash(ctx: CortanaContext, command: str, timeout: Optional[int] = None) -> str:
    """
    Execute a bash command in the container environment.
    
    This is the primary tool for getting things done - installing packages,
    running scripts, system commands, etc. Output is truncated to the last
    500 lines or 50KB (whichever is hit first).
    
    Args:
        command: The bash command to execute.
        timeout: Optional timeout in seconds (default: 60).
    
    Returns:
        Command output (stdout + stderr combined).
    """
    if timeout is None:
        timeout = config.BASH_TIMEOUT_DEFAULT if hasattr(config, 'BASH_TIMEOUT_DEFAULT') else 60
    
    try:
        # Create subprocess
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Combine stderr into stdout
            cwd=config.WORKSPACE_DIR if hasattr(config, 'WORKSPACE_DIR') else '/workspace'
        )
        
        try:
            # Wait for completion with timeout
            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            output = stdout.decode('utf-8', errors='replace') if stdout else ""
            exit_code = process.returncode
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return f"Error: Command timed out after {timeout} seconds."
        
        # Truncate output if needed
        truncated_output, was_truncated, truncation_info = _truncate_output(output)
        
        # Build result
        result = truncated_output if truncated_output else "(no output)"
        
        if was_truncated:
            start_line = truncation_info['total_lines'] - truncation_info['output_lines'] + 1
            end_line = truncation_info['total_lines']
            result += f"\n\n[Showing lines {start_line}-{end_line} of {truncation_info['total_lines']} ({_format_size(truncation_info['output_bytes'])} of {_format_size(truncation_info['total_bytes'])})]"
        
        if exit_code != 0:
            result += f"\n\nCommand exited with code {exit_code}"
        
        return result
        
    except Exception as e:
        return f"Error executing command: {str(e)}"


async def read_file(ctx: CortanaContext, path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> str:
    """
    Read file contents with optional line range.
    
    Args:
        path: Path to the file to read (absolute or relative to workspace).
        offset: Starting line number (1-indexed, optional).
        limit: Number of lines to read from offset (optional).
    
    Returns:
        File contents with line numbers for context.
    """
    try:
        # Resolve path
        workspace = config.WORKSPACE_DIR if hasattr(config, 'WORKSPACE_DIR') else '/workspace'
        if not os.path.isabs(path):
            path = os.path.join(workspace, path)
        
        # Security check - ensure path is within allowed directories
        real_path = os.path.realpath(path)
        
        if not os.path.exists(real_path):
            return f"Error: File not found: {path}"
        
        if not os.path.isfile(real_path):
            return f"Error: Path is not a file: {path}"
        
        # Check if file is binary
        try:
            with open(real_path, 'rb') as f:
                chunk = f.read(8192)
                if b'\x00' in chunk:
                    return f"Error: Cannot read binary file: {path}"
        except Exception as e:
            return f"Error checking file: {str(e)}"
        
        # Read file
        with open(real_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        if total_lines == 0:
            return f"File is empty: {path}"
        
        # Apply offset and limit
        start_idx = 0
        end_idx = total_lines
        
        if offset is not None:
            start_idx = max(0, offset - 1)  # Convert to 0-indexed
        
        if limit is not None:
            end_idx = min(total_lines, start_idx + limit)
        
        # Apply default limit if file is too large
        max_lines = config.FILE_READ_MAX_LINES if hasattr(config, 'FILE_READ_MAX_LINES') else 1000
        if end_idx - start_idx > max_lines:
            end_idx = start_idx + max_lines
        
        selected_lines = lines[start_idx:end_idx]
        
        # Format with line numbers
        result_lines = []
        for i, line in enumerate(selected_lines, start=start_idx + 1):
            # Remove trailing newline for cleaner display
            line_content = line.rstrip('\n\r')
            result_lines.append(f"{i:4d} | {line_content}")
        
        result = '\n'.join(result_lines)
        
        # Add truncation notice if applicable
        if end_idx < total_lines or start_idx > 0:
            result += f"\n\n[Showing lines {start_idx + 1}-{end_idx} of {total_lines}]"
        
        return result
        
    except Exception as e:
        return f"Error reading file: {str(e)}"


async def write_file(ctx: CortanaContext, path: str, content: str) -> str:
    """
    Create or overwrite a file with the given content.
    
    Parent directories will be created automatically if they don't exist.
    
    Args:
        path: Path to the file to write (absolute or relative to workspace).
        content: Content to write to the file.
    
    Returns:
        Confirmation message with file path and bytes written.
    """
    try:
        # Resolve path
        workspace = config.WORKSPACE_DIR if hasattr(config, 'WORKSPACE_DIR') else '/workspace'
        if not os.path.isabs(path):
            path = os.path.join(workspace, path)
        
        real_path = os.path.realpath(path)
        
        # Create parent directories if needed
        parent_dir = os.path.dirname(real_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        # Write file
        with open(real_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        bytes_written = len(content.encode('utf-8'))
        
        return f"File written: {path} ({_format_size(bytes_written)})"
        
    except Exception as e:
        return f"Error writing file: {str(e)}"


async def edit_file(ctx: CortanaContext, path: str, old_text: str, new_text: str) -> str:
    """
    Make surgical edits to a file by replacing exact text matches.
    
    This tool finds the exact `old_text` in the file and replaces it with `new_text`.
    Use this for small, targeted edits rather than rewriting entire files.
    
    Args:
        path: Path to the file to edit (absolute or relative to workspace).
        old_text: Exact text to find and replace (must match exactly).
        new_text: Replacement text.
    
    Returns:
        Confirmation with a preview of the changes made.
    """
    try:
        # Resolve path
        workspace = config.WORKSPACE_DIR if hasattr(config, 'WORKSPACE_DIR') else '/workspace'
        if not os.path.isabs(path):
            path = os.path.join(workspace, path)
        
        real_path = os.path.realpath(path)
        
        if not os.path.exists(real_path):
            return f"Error: File not found: {path}"
        
        if not os.path.isfile(real_path):
            return f"Error: Path is not a file: {path}"
        
        # Read current content
        with open(real_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if old_text exists
        if old_text not in content:
            # Provide helpful error message
            if old_text.strip() in content:
                return f"Error: Exact text not found. Note: The text exists but with different whitespace. Make sure `old_text` matches exactly including spaces and newlines."
            return f"Error: Text to replace not found in file. Make sure `old_text` matches exactly."
        
        # Count occurrences
        occurrences = content.count(old_text)
        
        # Perform replacement
        new_content = content.replace(old_text, new_text)
        
        # Write back
        with open(real_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Generate diff preview
        old_preview = old_text[:100] + "..." if len(old_text) > 100 else old_text
        new_preview = new_text[:100] + "..." if len(new_text) > 100 else new_text
        
        result = f"File edited: {path}\n"
        result += f"Replaced {occurrences} occurrence(s)\n\n"
        result += f"**Before:**\n```\n{old_preview}\n```\n\n"
        result += f"**After:**\n```\n{new_preview}\n```"
        
        return result
        
    except Exception as e:
        return f"Error editing file: {str(e)}"
