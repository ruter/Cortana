
import sys
import os
from unittest.mock import MagicMock
import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules BEFORE importing src.database
# 1. Mock supabase
mock_supabase = MagicMock()
mock_client_instance = MagicMock()
mock_supabase.create_client.return_value = mock_client_instance
sys.modules['supabase'] = mock_supabase

# 2. Mock src.config
mock_src_config = MagicMock()
mock_config_obj = MagicMock()
mock_config_obj.SUPABASE_URL = "http://test.url"
mock_config_obj.SUPABASE_KEY = "test_key"
mock_src_config.config = mock_config_obj
sys.modules['src.config'] = mock_src_config

# Now we can import src.database safely
try:
    from src.database import execute_async
except ImportError:
    # This might happen if relative imports fail due to how we manipulate sys.path/modules
    # Retrying with package context if needed, but assuming simple import works with sys.path modification
    execute_async = None

@pytest.mark.asyncio
async def test_execute_async_calls_execute_in_thread():
    """Test that execute_async calls execute method."""
    if execute_async is None:
         # Try to re-import inside test if module level failed (unlikely if setup is correct)
         from src.database import execute_async as ea
         func = ea
    else:
         func = execute_async

    mock_query = MagicMock()
    mock_query.execute.return_value = "result"

    # Run execute_async
    result = await func(mock_query)

    # Verify execute was called
    mock_query.execute.assert_called_once()
    assert result == "result"
