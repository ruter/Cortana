"""
Test script for reminder functionality.

This script tests the reminder creation and scheduling functionality
without requiring a live Discord connection.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import db
from src.config import config

async def test_reminder_creation():
    """Test creating a reminder directly in the database."""
    print("=== Testing Reminder Creation ===")
    
    # Test user ID (use a Discord user ID you have access to)
    test_user_id = 123456789  # Replace with your Discord user ID for testing
    
    # Create a reminder 2 minutes in the future
    remind_time = datetime.now(timezone.utc) + timedelta(minutes=2)
    
    try:
        # First ensure user exists in user_settings
        print(f"Creating test user {test_user_id}...")
        try:
            db.table("user_settings").insert({"user_id": test_user_id}).execute()
        except Exception as e:
            if "duplicate" not in str(e).lower():
                print(f"Warning: {e}")
            else:
                print("User already exists")
        
        # Create a test reminder
        print(f"Creating reminder for {remind_time.isoformat()}...")
        response = db.table("reminders").insert({
            "user_id": test_user_id,
            "message": "Test reminder - this is a test message",
            "remind_time": remind_time.isoformat(),
            "is_sent": False
        }).execute()
        
        if response.data:
            reminder_id = response.data[0]['id']
            print(f"✅ Reminder created successfully! ID: {reminder_id}")
            print(f"   Message: 'Test reminder - this is a test message'")
            print(f"   Remind at: {remind_time}")
            return reminder_id
        else:
            print("❌ Failed to create reminder")
            return None
    
    except Exception as e:
        print(f"❌ Error creating reminder: {e}")
        return None

async def test_reminder_query():
    """Test querying reminders that are due."""
    print("\n=== Testing Reminder Query ===")
    
    try:
        now = datetime.now(timezone.utc)
        
        # Query for reminders that should be sent
        response = db.table("reminders").select("*") \
            .lte("remind_time", now.isoformat()) \
            .eq("is_sent", False) \
            .execute()
        
        print(f"Found {len(response.data)} reminders due now")
        
        for reminder in response.data:
            print(f"  - ID {reminder['id']}: {reminder['message']}")
        
        return response.data
    
    except Exception as e:
        print(f"❌ Error querying reminders: {e}")
        return []

async def test_reminder_marking_sent(reminder_id):
    """Test marking a reminder as sent."""
    print(f"\n=== Testing Marking Reminder {reminder_id} as Sent ===")
    
    try:
        db.table("reminders").update({"is_sent": True}).eq("id", reminder_id).execute()
        print(f"✅ Reminder {reminder_id} marked as sent")
        
        # Verify
        response = db.table("reminders").select("*").eq("id", reminder_id).execute()
        if response.data and response.data[0]['is_sent']:
            print(f"✅ Verification successful: is_sent = True")
        else:
            print(f"❌ Verification failed")
    
    except Exception as e:
        print(f"❌ Error marking reminder as sent: {e}")

async def test_list_user_reminders(user_id):
    """Test listing all reminders for a user."""
    print(f"\n=== Testing List Reminders for User {user_id} ===")
    
    try:
        response = db.table("reminders").select("*").eq("user_id", user_id).execute()
        
        print(f"Found {len(response.data)} total reminders for this user")
        
        for reminder in response.data:
            status = "✅ Sent" if reminder['is_sent'] else "⏰ Pending"
            print(f"  {status} [{reminder['id']}] {reminder['message']} - {reminder['remind_time']}")
    
    except Exception as e:
        print(f"❌ Error listing reminders: {e}")

async def cleanup_test_reminders(user_id):
    """Clean up test reminders."""
    print(f"\n=== Cleaning Up Test Reminders ===")
    
    try:
        response = db.table("reminders").delete().eq("user_id", user_id).eq("message", "Test reminder - this is a test message").execute()
        print(f"✅ Cleaned up test reminders")
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")

async def main():
    """Main test function."""
    print("Starting reminder functionality tests...")
    print(f"Database URL: {config.SUPABASE_URL}")
    print()
    
    # Test 1: Create a reminder
    reminder_id = await test_reminder_creation()
    
    if reminder_id:
        # Test 2: Query reminders (should not find it yet as it's in the future)
        await test_reminder_query()
        
        # Test 3: List user reminders
        await test_list_user_reminders(123456789)
        
        # Test 4: Mark as sent
        await test_reminder_marking_sent(reminder_id)
        
        # Test 5: List again to see the change
        await test_list_user_reminders(123456789)
        
        # Cleanup
        await cleanup_test_reminders(123456789)
    
    print("\n=== Tests Complete ===")
    print("\nTo test the full scheduler functionality:")
    print("1. Update the test_user_id in this script to your Discord user ID")
    print("2. Create a reminder for 1-2 minutes in the future")
    print("3. Run the Discord bot (python -m src.main)")
    print("4. Wait for the reminder time and check your Discord DMs")

if __name__ == "__main__":
    try:
        config.validate()
        asyncio.run(main())
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please ensure your .env file is properly configured")
