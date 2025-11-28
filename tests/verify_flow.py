import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock config before importing anything else
with patch('src.config.Config') as MockConfig:
    MockConfig.DISCORD_TOKEN = "mock_token"
    MockConfig.SUPABASE_URL = "mock_url"
    MockConfig.SUPABASE_KEY = "mock_key"
    MockConfig.ZEP_API_URL = "mock_url"
    MockConfig.ZEP_API_KEY = "mock_key"
    MockConfig.OPENAI_API_KEY = "mock_key"

    # Mock external modules in sys.modules
    sys.modules['supabase'] = MagicMock()
    sys.modules['zep_python'] = MagicMock()
    sys.modules['openai'] = MagicMock()
    
    # Mock PydanticAI
    mock_pydantic_ai = MagicMock()
    sys.modules['pydantic_ai'] = mock_pydantic_ai
    
    # Define Mock Agent Class to handle decoration
    class MockAgent:
        def __init__(self, *args, **kwargs):
            self._function_tools = {}
            self._system_prompts = []
            
        def tool(self, func):
            # Store tool info for verification
            mock_info = MagicMock()
            mock_info.name = func.__name__
            
            mock_tool = MagicMock()
            mock_tool.info = mock_info
            self._function_tools[func.__name__] = mock_tool
            return func
            
        def system_prompt(self, func):
            self._system_prompts.append(MagicMock(run=func))
            return func

        async def run(self, *args, **kwargs):
            return MagicMock(data="Mock Response")

    mock_pydantic_ai.Agent = MockAgent
    mock_pydantic_ai.RunContext = MagicMock()

    # Mock dependencies
    with patch('src.database.create_client') as mock_create_client, \
         patch('src.memory.ZepClient') as mock_zep_client:
        
        # Setup Mock DB
        mock_db = MagicMock()
        mock_create_client.return_value = mock_db
        
        # Setup Mock Zep
        mock_memory = MagicMock()
        mock_zep_client.return_value = mock_memory
        
        # Import Agent (now that mocks are set)
        from src.agent import cortana_agent
        
        async def run_test():
            print("Starting Verification Test...")
            
            # Mock Agent Run
            # Since we can't easily mock the OpenAI call without making real requests or deep patching PydanticAI,
            # we will verify the tool definitions and system prompt generation.
            
            print("1. Verifying Tool Registration...")
            tools = cortana_agent._function_tools
            tool_names = [t.info.name for t in tools.values()]
            expected_tools = [
                'add_todo', 'list_todos', 'complete_todo', 
                'add_calendar_event', 'check_calendar_availability', 
                'search_long_term_memory', 'get_unread_emails'
            ]
            
            for tool in expected_tools:
                if tool in tool_names:
                    print(f"  [PASS] Tool '{tool}' registered.")
                else:
                    print(f"  [FAIL] Tool '{tool}' NOT registered.")
            
            print("\n2. Verifying System Prompt Injection...")
            # We can manually call the system prompt function if we can access it
            # PydanticAI stores it in _system_prompts
            
            # Create a dummy context
            from pydantic_ai import RunContext
            
            deps = {
                "user_info": {"id": 123, "name": "TestUser"},
                "zep_memory_context": "User likes apples."
            }
            
            # This is a bit hacky to test the system prompt function directly
            # but serves to verify it doesn't crash
            try:
                # Find the system prompt runner
                sys_prompt_runner = cortana_agent._system_prompts[0]
                # Create a mock context
                ctx = MagicMock(spec=RunContext)
                ctx.deps = deps
                
                prompt = await sys_prompt_runner.run(ctx)
                
                if "Cortana" in prompt and "TestUser" in prompt and "User likes apples" in prompt:
                    print("  [PASS] System Prompt generated correctly with context.")
                else:
                    print("  [FAIL] System Prompt missing key elements.")
                    print(f"Generated: {prompt[:100]}...")
            except Exception as e:
                print(f"  [FAIL] Error running system prompt: {e}")

            print("\nVerification Complete.")

        if __name__ == "__main__":
            asyncio.run(run_test())
