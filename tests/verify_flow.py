"""
Verification test for the Cortana agent flow.

Tests that tools are registered correctly and system prompt is generated properly.
"""
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock external dependencies
sys.modules['supabase'] = MagicMock()
sys.modules['zep_cloud'] = MagicMock()
sys.modules['zep_cloud.types'] = MagicMock()

# Mock config
mock_config = MagicMock()
mock_config.DISCORD_TOKEN = "mock_token"
mock_config.SUPABASE_URL = "mock_url"
mock_config.SUPABASE_KEY = "mock_key"
mock_config.ZEP_API_KEY = "mock_key"
mock_config.LLM_API_KEY = "mock_key"
mock_config.LLM_MODEL_NAME = "gpt-4o"
mock_config.LLM_BASE_URL = None
mock_config.DEFAULT_TIMEZONE = "UTC"
mock_config.EXA_API_KEY = None
mock_config.ENABLE_ROTATOR = False
mock_config.ENABLE_BASH_TOOL = False
mock_config.ENABLE_FILE_TOOLS = False
mock_config.ENABLE_SKILLS = False
mock_config.ROTATOR_API_KEYS = {}
mock_config.load_rotator_keys = MagicMock()
mock_config.get_rotator_config = MagicMock(return_value={"api_keys": {}, "oauth_credentials": {}})
mock_config.get_available_providers = MagicMock(return_value=[])
mock_config.get_key_count = MagicMock(return_value=0)
mock_config.validate = MagicMock()

sys.modules['src.config'] = MagicMock()
sys.modules['src.config'].config = mock_config


async def run_test():
    """Run verification tests for the agent."""
    print("Starting Verification Test...")
    
    # Mock database and memory before importing agent
    with patch('src.database.create_client') as mock_create_client, \
         patch('src.memory.AsyncZep') as mock_zep_client, \
         patch('src.rotator_client.rotating_completion') as mock_completion:
        
        mock_db = MagicMock()
        mock_create_client.return_value = mock_db
        
        mock_memory = MagicMock()
        mock_zep_client.return_value = mock_memory
        
        # Mock completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Mock response from Cortana"
        mock_response.choices[0].message.tool_calls = None
        mock_completion.return_value = mock_response
        
        # Import agent after mocks are set up
        from src.cortana_context import CortanaContext
        from src.cortana_agent import CortanaAgent
        from src.agent import cortana_agent, dynamic_system_prompt
        
        print("1. Verifying Tool Registration...")
        
        tools = cortana_agent.registry.get_all()
        tool_names = [t.name for t in tools]
        
        expected_tools = [
            'add_todo', 'list_todos', 'complete_todo', 
            'add_calendar_event', 'check_calendar_availability', 
            'search_long_term_memory', 'get_unread_emails',
            'add_reminder', 'list_reminders', 'cancel_reminder',
            'fetch_url'
        ]
        
        for tool in expected_tools:
            if tool in tool_names:
                print(f"  [PASS] Tool '{tool}' registered.")
            else:
                print(f"  [FAIL] Tool '{tool}' NOT registered.")
        
        print(f"\n  Total tools registered: {len(tool_names)}")
        
        print("\n2. Verifying System Prompt Injection...")
        
        deps = {
            "user_info": {"id": 123, "name": "TestUser"},
            "zep_memory_context": "User likes apples."
        }
        
        try:
            ctx = CortanaContext(deps=deps)
            prompt = await dynamic_system_prompt(ctx)
            
            checks = [
                ("Cortana" in prompt, "Cortana identity"),
                ("TestUser" in prompt, "User name"),
                ("User likes apples" in prompt, "Memory context"),
                ("Language Protocol" in prompt, "Language directive"),
                ("Time Awareness" in prompt, "Time directive"),
            ]
            
            for check, name in checks:
                status = "[PASS]" if check else "[FAIL]"
                print(f"  {status} {name} in prompt")
            
        except Exception as e:
            print(f"  [FAIL] Error running system prompt: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n3. Verifying Agent Run (with mock)...")
        
        try:
            result = await cortana_agent.run("Hello!", deps=deps)
            
            if result.output == "Mock response from Cortana":
                print("  [PASS] Agent run completed successfully")
            else:
                print(f"  [FAIL] Unexpected response: {result.output}")
                
            if result.success:
                print("  [PASS] Result marked as successful")
            else:
                print("  [FAIL] Result marked as failed")
                
        except Exception as e:
            print(f"  [FAIL] Error running agent: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n4. Verifying Tool Schemas...")
        
        for tool in tools[:3]:  # Check first 3 tools
            try:
                schema = tool.openai_tool()
                if schema.get("type") == "function" and schema.get("function", {}).get("name"):
                    print(f"  [PASS] Tool '{tool.name}' has valid OpenAI schema")
                else:
                    print(f"  [FAIL] Tool '{tool.name}' has invalid schema")
            except Exception as e:
                print(f"  [FAIL] Tool '{tool.name}' schema error: {e}")
        
        print("\nVerification Complete.")


if __name__ == "__main__":
    asyncio.run(run_test())
