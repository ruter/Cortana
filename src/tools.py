from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import RunContext
from .database import db
from .memory import memory_client

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

async def add_todo(ctx: RunContext[Dict[str, Any]], content: str, due_date: Optional[datetime] = None, priority: int = 3) -> str:
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

async def list_todos(ctx: RunContext[Dict[str, Any]], status: str = "PENDING", limit: int = 10) -> str:
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

async def complete_todo(ctx: RunContext[Dict[str, Any]], todo_id: int) -> str:
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

async def add_calendar_event(ctx: RunContext[Dict[str, Any]], title: str, start_time: datetime, end_time: datetime, location: Optional[str] = None) -> str:
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

async def check_calendar_availability(ctx: RunContext[Dict[str, Any]], start_range: datetime, end_range: datetime) -> str:
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

async def search_long_term_memory(ctx: RunContext[Dict[str, Any]], query: str, limit: int = 3) -> str:
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

async def get_unread_emails(ctx: RunContext[Dict[str, Any]], limit: int = 5) -> str:
    """
    Mock function to get unread emails.
    In a real app, this would connect to Gmail/Outlook API.
    """
    return "No unread emails (Email integration not yet implemented)."
