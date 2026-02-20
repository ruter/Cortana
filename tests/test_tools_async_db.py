
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules BEFORE importing src.tools
# 1. Mock supabase
mock_supabase = MagicMock()
mock_client_instance = MagicMock()
# Mock table().insert().execute() chain for blocking calls (current implementation)
mock_query_builder = MagicMock()
mock_query_builder.execute.return_value = MagicMock(data=[])
mock_client_instance.table.return_value.insert.return_value = mock_query_builder
mock_client_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

mock_supabase.create_client.return_value = mock_client_instance
sys.modules['supabase'] = mock_supabase

# 2. Mock src.config
mock_src_config = MagicMock()
mock_config_obj = MagicMock()
mock_config_obj.SUPABASE_URL = "http://test.url"
mock_config_obj.SUPABASE_KEY = "test_key"
mock_src_config.config = mock_config_obj
sys.modules['src.config'] = mock_src_config

# Import tools
try:
    from src.tools import add_todo, ensure_user_exists
except ImportError:
    # Fallback if import fails
    add_todo = None
    ensure_user_exists = None

@pytest.mark.asyncio
async def test_add_todo_uses_async_execute():
    if not add_todo:
        pytest.fail("Could not import add_todo")

    # Mock context
    ctx = MagicMock()
    ctx.deps = {'user_info': {'id': 123}}

    # We patch execute_async in src.tools to verify it is used
    # Note: verify that 'src.tools.execute_async' exists first
    # If I haven't modified tools.py, this patch will likely fail or create a new attribute
    # But we want to fail if it's NOT used.

    with patch('src.tools.execute_async', new_callable=AsyncMock) as mock_execute_async:
        mock_execute_async.return_value = MagicMock(data=[{'id': 1}])

        # We also need to mock db.table(...) to return something that is passed to execute_async
        # Since src.tools.db refers to the global db from database.py (which is mocked above via sys.modules['supabase'])
        # Wait, src.database imports create_client, but we mocked supabase module.
        # But src.database.db is instantiated at import time.
        # We mocked modules before import, so src.database.db should be our mock_client_instance.

        # Call add_todo
        await add_todo(ctx, "Test todo")

        # Verify execute_async was called
        mock_execute_async.assert_called()

        # Verify db.table was called
        from src.tools import db
        db.table.assert_called_with("todos")

@pytest.mark.asyncio
async def test_ensure_user_exists_uses_async_execute():
    if not ensure_user_exists:
        pytest.fail("Could not import ensure_user_exists")

    # Patch execute_async
    with patch('src.tools.execute_async', new_callable=AsyncMock) as mock_execute_async:
        mock_execute_async.return_value = MagicMock(data=[]) # Simulate user doesn't exist

        # Call ensure_user_exists
        await ensure_user_exists(123)

        # Verify execute_async was called (at least once for select, maybe twice for insert)
        assert mock_execute_async.call_count >= 1
