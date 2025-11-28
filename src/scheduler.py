import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from .database import db
from .config import config

if TYPE_CHECKING:
    import discord

class ReminderScheduler:
    """Background service that checks and sends reminders to users via Discord DM."""
    
    def __init__(self, discord_client: 'discord.Client'):
        """
        Initialize the reminder scheduler.
        
        Args:
            discord_client: The Discord client instance for sending messages.
        """
        self.client = discord_client
        self.running = False
        self.task = None
    
    async def check_and_send_reminders(self):
        """Check for due reminders and send them to users."""
        try:
            # Get current time in UTC
            now = datetime.now(timezone.utc)
            
            # Query for reminders that are due and not yet sent
            response = db.table("reminders").select("*") \
                .lte("remind_time", now.isoformat()) \
                .eq("is_sent", False) \
                .execute()
            
            if not response.data:
                return
            
            print(f"Found {len(response.data)} reminder(s) to send")
            
            for reminder in response.data:
                await self.send_reminder(reminder)
        
        except Exception as e:
            print(f"Error checking reminders: {e}")
    
    async def send_reminder(self, reminder: dict):
        """
        Send a reminder to a user via Discord DM.
        
        Args:
            reminder: Dictionary containing reminder data from database.
        """
        try:
            user_id = reminder['user_id']
            message = reminder['message']
            reminder_id = reminder['id']
            
            # Get the Discord user object
            user = await self.client.fetch_user(user_id)
            
            if user is None:
                print(f"Could not find user {user_id}")
                # Mark as sent anyway to avoid retrying
                db.table("reminders").update({"is_sent": True}).eq("id", reminder_id).execute()
                return
            
            # Prepare the reminder message
            dm_message = f"⏰ **Reminder**: {message}"
            
            # Try to send DM
            try:
                await user.send(dm_message)
                print(f"Sent reminder {reminder_id} to user {user_id}")
                
                # Mark as sent
                db.table("reminders").update({"is_sent": True}).eq("id", reminder_id).execute()
                
            except Exception as dm_error:
                # User might have DMs disabled
                print(f"Failed to send DM to user {user_id}: {dm_error}")
                
                # Still mark as sent to avoid infinite retries
                # In a production system, you might want to log this differently
                db.table("reminders").update({"is_sent": True}).eq("id", reminder_id).execute()
        
        except Exception as e:
            print(f"Error sending reminder {reminder.get('id', 'unknown')}: {e}")
    
    async def run(self):
        """Main loop that periodically checks for reminders."""
        self.running = True
        print("Reminder scheduler started")
        
        while self.running:
            try:
                await self.check_and_send_reminders()
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error in reminder scheduler loop: {e}")
                # Wait a bit before retrying to avoid tight error loops
                await asyncio.sleep(60)
    
    def start(self):
        """Start the scheduler as a background task."""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.run())
            print("Reminder scheduler task created")
    
    def stop(self):
        """Stop the scheduler gracefully."""
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
            print("Reminder scheduler stopped")
