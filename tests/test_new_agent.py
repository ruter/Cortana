"""
Tests for the new CortanaAgent and related components.

These tests verify the core agent infrastructure without external dependencies.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from typing import Optional

import sys
import os

# Setup path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock external dependencies before importing src modules
sys.modules['zep_cloud'] = MagicMock()
sys.modules['zep_cloud.client'] = MagicMock()
sys.modules['zep_cloud.types'] = MagicMock()
sys.modules['supabase'] = MagicMock()
sys.modules['exa_py'] = MagicMock()
sys.modules['rotator_library'] = MagicMock()


class TestCortanaContext:
    """Tests for CortanaContext."""
    
    def test_context_creation(self):
        from src.cortana_context import CortanaContext
        
        deps = {"user_info": {"id": 123, "name": "TestUser"}}
        ctx = CortanaContext(deps=deps)
        
        assert ctx.deps["user_info"]["id"] == 123
        assert ctx.deps["user_info"]["name"] == "TestUser"
    
    def test_context_get_method(self):
        from src.cortana_context import CortanaContext
        
        deps = {"key": "value"}
        ctx = CortanaContext(deps=deps)
        
        assert ctx.get("key") == "value"
        assert ctx.get("missing") is None
        assert ctx.get("missing", "default") == "default"
    
    def test_context_empty(self):
        from src.cortana_context import CortanaContext
        
        ctx = CortanaContext()
        assert ctx.deps == {}


class TestTooling:
    """Tests for the tooling module."""
    
    def test_create_tool_spec(self):
        from src.tooling import create_tool_spec
        from src.cortana_context import CortanaContext
        
        async def sample_tool(ctx: CortanaContext, message: str, count: int = 1) -> str:
            """A sample tool for testing.
            
            Args:
                message: The message to process.
                count: Number of times to repeat.
            """
            return message * count
        
        spec = create_tool_spec(sample_tool)
        
        assert spec.name == "sample_tool"
        assert "sample tool" in spec.description.lower()
        assert spec.fn == sample_tool
    
    def test_tool_spec_openai_format(self):
        from src.tooling import create_tool_spec
        from src.cortana_context import CortanaContext
        
        async def greet(ctx: CortanaContext, name: str) -> str:
            """Greet someone by name.
            
            Args:
                name: Person's name.
            """
            return f"Hello, {name}!"
        
        spec = create_tool_spec(greet)
        openai_tool = spec.openai_tool()
        
        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "greet"
        assert "parameters" in openai_tool["function"]
        assert openai_tool["function"]["parameters"]["type"] == "object"
    
    def test_tool_with_optional_datetime(self):
        from src.tooling import create_tool_spec
        from src.cortana_context import CortanaContext
        
        async def schedule(ctx: CortanaContext, title: str, when: Optional[datetime] = None) -> str:
            """Schedule an event.
            
            Args:
                title: Event title.
                when: Optional event time.
            """
            return f"Scheduled: {title}"
        
        spec = create_tool_spec(schedule)
        
        # Should not raise
        openai_tool = spec.openai_tool()
        assert openai_tool["function"]["name"] == "schedule"
    
    def test_tool_registry(self):
        from src.tooling import ToolRegistry
        from src.cortana_context import CortanaContext
        
        registry = ToolRegistry()
        
        async def tool_a(ctx: CortanaContext, x: int) -> str:
            """Tool A."""
            return str(x)
        
        async def tool_b(ctx: CortanaContext, y: str) -> str:
            """Tool B."""
            return y
        
        registry.register(tool_a)
        registry.register(tool_b)
        
        assert len(registry) == 2
        assert "tool_a" in registry
        assert "tool_b" in registry
        
        tools = registry.openai_tools()
        assert len(tools) == 2


class TestCortanaAgent:
    """Tests for CortanaAgent."""
    
    @pytest.fixture
    def mock_rotating_completion(self):
        """Create a mock for rotating_completion."""
        with patch('src.cortana_agent.rotating_completion') as mock:
            response = MagicMock()
            response.choices = [MagicMock()]
            response.choices[0].message = MagicMock()
            response.choices[0].message.content = "Test response"
            response.choices[0].message.tool_calls = None
            mock.return_value = response
            yield mock
    
    @pytest.mark.asyncio
    async def test_agent_simple_run(self, mock_rotating_completion):
        from src.cortana_agent import CortanaAgent
        
        agent = CortanaAgent(model="openai/gpt-4o")
        
        result = await agent.run(
            "Hello!",
            deps={"user_info": {"id": 123}}
        )
        
        assert result.output == "Test response"
        assert result.success is True
        assert result.steps == 1
    
    @pytest.mark.asyncio
    async def test_agent_with_tools(self, mock_rotating_completion):
        from src.cortana_agent import CortanaAgent
        from src.cortana_context import CortanaContext
        
        agent = CortanaAgent(model="openai/gpt-4o")
        
        @agent.tool
        async def get_time(ctx: CortanaContext) -> str:
            """Get the current time."""
            return "12:00 PM"
        
        assert len(agent.registry) == 1
        assert "get_time" in agent.registry
        
        result = await agent.run("What time is it?", deps={})
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_agent_tool_execution(self):
        from src.cortana_agent import CortanaAgent
        from src.cortana_context import CortanaContext
        
        agent = CortanaAgent(model="openai/gpt-4o")
        
        tool_executed = False
        
        @agent.tool
        async def my_tool(ctx: CortanaContext, value: str) -> str:
            """A test tool.
            
            Args:
                value: The value to return.
            """
            nonlocal tool_executed
            tool_executed = True
            return f"Received: {value}"
        
        # Mock the completion to return a tool call first, then a final response
        call_count = [0]
        
        def mock_completion(**kwargs):
            call_count[0] += 1
            response = MagicMock()
            response.choices = [MagicMock()]
            msg = response.choices[0].message
            
            if call_count[0] == 1:
                # First call: return a tool call
                msg.content = None
                tool_call = MagicMock()
                tool_call.id = "call_123"
                tool_call.type = "function"
                tool_call.function = MagicMock()
                tool_call.function.name = "my_tool"
                tool_call.function.arguments = '{"value": "test"}'
                msg.tool_calls = [tool_call]
            else:
                # Second call: return final response
                msg.content = "Done!"
                msg.tool_calls = None
            
            return response
        
        with patch('src.cortana_agent.rotating_completion', side_effect=mock_completion):
            result = await agent.run("Use my_tool", deps={})
        
        assert tool_executed is True
        assert result.output == "Done!"
        assert result.steps == 2
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "my_tool"
    
    @pytest.mark.asyncio
    async def test_agent_max_steps_exceeded(self):
        from src.cortana_agent import CortanaAgent
        from src.cortana_context import CortanaContext
        
        agent = CortanaAgent(model="openai/gpt-4o", max_steps=2)
        
        @agent.tool
        async def infinite_tool(ctx: CortanaContext) -> str:
            """A tool that keeps getting called."""
            return "Call me again"
        
        def mock_completion(**kwargs):
            response = MagicMock()
            response.choices = [MagicMock()]
            msg = response.choices[0].message
            msg.content = None
            tool_call = MagicMock()
            tool_call.id = "call_123"
            tool_call.type = "function"
            tool_call.function = MagicMock()
            tool_call.function.name = "infinite_tool"
            tool_call.function.arguments = '{}'
            msg.tool_calls = [tool_call]
            return response
        
        with patch('src.cortana_agent.rotating_completion', side_effect=mock_completion):
            result = await agent.run("Loop forever", deps={})
        
        assert result.success is False
        assert "too many steps" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_agent_unknown_tool_handling(self):
        from src.cortana_agent import CortanaAgent
        
        agent = CortanaAgent(model="openai/gpt-4o")
        
        call_count = [0]
        
        def mock_completion(**kwargs):
            call_count[0] += 1
            response = MagicMock()
            response.choices = [MagicMock()]
            msg = response.choices[0].message
            
            if call_count[0] == 1:
                msg.content = None
                tool_call = MagicMock()
                tool_call.id = "call_123"
                tool_call.type = "function"
                tool_call.function = MagicMock()
                tool_call.function.name = "nonexistent_tool"
                tool_call.function.arguments = '{}'
                msg.tool_calls = [tool_call]
            else:
                msg.content = "Handled error"
                msg.tool_calls = None
            
            return response
        
        with patch('src.cortana_agent.rotating_completion', side_effect=mock_completion):
            result = await agent.run("Use unknown tool", deps={})
        
        assert result.success is True
        # Agent should handle unknown tool gracefully and continue


class TestAgentResult:
    """Tests for AgentResult."""
    
    def test_result_creation(self):
        from src.cortana_agent import AgentResult
        
        result = AgentResult(output="Hello", success=True, steps=1)
        
        assert result.output == "Hello"
        assert result.success is True
        assert result.steps == 1
        assert result.tool_calls == []
    
    def test_result_str(self):
        from src.cortana_agent import AgentResult
        
        result = AgentResult(output="Hello World")
        assert str(result) == "Hello World"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
