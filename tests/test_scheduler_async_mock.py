
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules
mock_supabase = MagicMock()
mock_client_instance = MagicMock()
mock_supabase.create_client.return_value = mock_client_instance
sys.modules['supabase'] = mock_supabase

mock_src_config = MagicMock()
mock_src_config.config = MagicMock()
sys.modules['src.config'] = mock_src_config

# Import scheduler
try:
    from src.scheduler import ReminderScheduler
except ImportError:
    ReminderScheduler = None

@pytest.mark.asyncio
async def test_scheduler_uses_async_execute():
    if not ReminderScheduler:
        pytest.fail("Could not import ReminderScheduler")

    client = MagicMock()
    scheduler = ReminderScheduler(client)

    # Patch execute_async in src.scheduler
    with patch('src.scheduler.execute_async', new_callable=AsyncMock) as mock_execute_async:
        mock_execute_async.return_value = MagicMock(data=[])

        # Call check_and_send_reminders
        await scheduler.check_and_send_reminders()

        # Verify execute_async was called
        mock_execute_async.assert_called()
