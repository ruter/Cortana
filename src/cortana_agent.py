"""
Cortana Agent Module
====================

Custom agent orchestrator that replaces PydanticAI, using the rotator_library
for LLM calls with automatic key rotation and resilience features.

The agent implements a standard OpenAI-compatible tool calling loop:
1. Send messages to LLM with available tools
2. If LLM returns tool_calls, execute them and append results
3. Repeat until LLM returns a final text response
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import config
from .cortana_context import CortanaContext
from .rotator_client import normalize_model_name, rotating_completion
from .tooling import ToolRegistry, ToolSpec, create_tool_spec

logger = logging.getLogger(__name__)


class CortanaAgent:
    """
    Custom agent orchestrator for Cortana.
    
    Handles the LLM interaction loop, tool registration, and execution.
    Uses rotator_client for resilient API calls with key rotation.
    
    Attributes:
        model: The LLM model to use (e.g., "openai/gpt-4o").
        max_steps: Maximum tool call iterations to prevent infinite loops.
        registry: Tool registry containing all available tools.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        *,
        max_steps: int = 15,
        system_prompt_fn: Optional[Any] = None,
    ):
        """
        Initialize the Cortana agent.
        
        Args:
            model: LLM model name. Defaults to config.LLM_MODEL_NAME.
            max_steps: Maximum tool calling iterations.
            system_prompt_fn: Async function that generates the system prompt.
        """
        self.model = normalize_model_name(model or config.LLM_MODEL_NAME)
        self.max_steps = max_steps
        self.registry = ToolRegistry()
        self._system_prompt_fn = system_prompt_fn
    
    def tool(self, fn) -> Any:
        """
        Register a tool function.
        
        Can be used as a decorator or called directly.
        
        Args:
            fn: The async tool function to register.
        
        Returns:
            The original function.
        """
        self.registry.register(fn)
        return fn
    
    def register_tool(self, spec: ToolSpec) -> None:
        """Register a pre-built ToolSpec."""
        self.registry.register_spec(spec)
    
    def system_prompt(self, fn) -> Any:
        """
        Set the system prompt generator function.
        
        Can be used as a decorator.
        
        Args:
            fn: Async function that takes CortanaContext and returns str.
        
        Returns:
            The original function.
        """
        self._system_prompt_fn = fn
        return fn
    
    async def _get_system_prompt(self, ctx: CortanaContext) -> str:
        """Generate the system prompt using the registered function."""
        if self._system_prompt_fn is None:
            return "You are Cortana, an excellently efficient and highly intelligent personal assistant."
        
        return await self._system_prompt_fn(ctx)
    
    async def run(
        self,
        user_content: str,
        *,
        deps: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> "AgentResult":
        """
        Run the agent with a user message.
        
        This is the main entry point that handles the complete interaction loop:
        1. Build messages with system prompt and user content
        2. Call LLM with tools
        3. Execute any tool calls and append results
        4. Repeat until final response
        
        Args:
            user_content: The user's message.
            deps: Dependencies to pass to tools via CortanaContext.
            history: Optional conversation history (list of message dicts).
        
        Returns:
            AgentResult containing the final output and run metadata.
        """
        ctx = CortanaContext(deps=deps or {})
        system_prompt = await self._get_system_prompt(ctx)
        
        # Build initial messages
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": user_content})
        
        # Get tools payload
        tools_payload = self.registry.openai_tools() if len(self.registry) > 0 else None
        
        # Track tool calls for debugging
        tool_calls_made: List[Dict[str, Any]] = []
        
        for step in range(self.max_steps):
            logger.debug(f"Agent step {step + 1}/{self.max_steps}")
            
            try:
                # Make LLM call
                response = await rotating_completion(
                    model=self.model,
                    messages=messages,
                    tools=tools_payload,
                    tool_choice="auto" if tools_payload else None,
                    stream=False,
                )
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return AgentResult(
                    output=f"I encountered an error communicating with the AI service: {e}",
                    success=False,
                    tool_calls=tool_calls_made,
                    steps=step + 1,
                )
            
            # Handle error response (dict without choices)
            if isinstance(response, dict):
                error_msg = response.get("error", {}).get("message", "Unknown API error")
                logger.error(f"API returned error response: {error_msg}")
                return AgentResult(
                    output=f"I hit a snag with the AI service: {error_msg}",
                    success=False,
                    tool_calls=tool_calls_made,
                    steps=step + 1,
                )
            
            # Validate response has choices
            if not hasattr(response, "choices") or not response.choices:
                logger.error("API response missing choices")
                return AgentResult(
                    output="I received an unexpected response from the AI service. Let's try again in a moment.",
                    success=False,
                    tool_calls=tool_calls_made,
                    steps=step + 1,
                )
            
            # Extract message from response
            msg = response.choices[0].message
            
            # Normalize to dict format
            assistant_dict: Dict[str, Any] = {
                "role": "assistant",
                "content": getattr(msg, "content", None),
            }
            
            # Check for tool calls
            tool_calls = getattr(msg, "tool_calls", None)
            
            if tool_calls:
                # Normalize tool_calls to dict format
                assistant_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": getattr(tc, "type", "function"),
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ]
            
            # Append assistant message to history
            messages.append(assistant_dict)
            
            # If no tool calls, we're done
            if not tool_calls:
                final_content = assistant_dict.get("content") or ""
                return AgentResult(
                    output=final_content,
                    success=True,
                    tool_calls=tool_calls_made,
                    steps=step + 1,
                )
            
            # Execute tool calls
            for tc in tool_calls:
                tool_name = tc.function.name
                tool_call_id = tc.id
                raw_args = tc.function.arguments or "{}"
                
                logger.debug(f"Executing tool: {tool_name}")
                
                tool_calls_made.append({
                    "name": tool_name,
                    "arguments": raw_args,
                    "step": step + 1,
                })
                
                # Get tool spec
                tool = self.registry.get(tool_name)
                
                if not tool:
                    tool_result = f"Error: Unknown tool '{tool_name}'. Available tools: {', '.join(t.name for t in self.registry.get_all())}"
                    logger.warning(f"Unknown tool requested: {tool_name}")
                else:
                    try:
                        # Parse arguments
                        args_dict = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        
                        # Validate with Pydantic model
                        parsed_args = tool.input_model.model_validate(args_dict)
                        
                        # Execute tool
                        tool_result = await tool.fn(ctx, **parsed_args.model_dump())
                        
                    except json.JSONDecodeError as e:
                        tool_result = f"Error: Invalid JSON arguments for tool '{tool_name}': {e}"
                        logger.error(f"JSON decode error for {tool_name}: {e}")
                    except Exception as e:
                        tool_result = f"Error executing tool '{tool_name}': {e}"
                        logger.error(f"Tool execution error for {tool_name}: {e}", exc_info=True)
                
                # Append tool result
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": str(tool_result),
                })
        
        # Exceeded max steps
        logger.warning(f"Agent exceeded max_steps={self.max_steps}")
        return AgentResult(
            output=f"I'm having trouble completing this request. It seems to require too many steps. Please try simplifying your request.",
            success=False,
            tool_calls=tool_calls_made,
            steps=self.max_steps,
        )
    
    async def aclose(self) -> None:
        """Clean up agent resources."""
        from .rotator_client import close_rotating_client
        await close_rotating_client()
    
    async def __aenter__(self) -> "CortanaAgent":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()


class AgentResult:
    """
    Result from an agent run.
    
    Attributes:
        output: The final text response from the agent.
        success: Whether the run completed successfully.
        tool_calls: List of tool calls made during the run.
        steps: Number of LLM call iterations.
    """
    
    def __init__(
        self,
        output: str,
        success: bool = True,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        steps: int = 1,
    ):
        self.output = output
        self.success = success
        self.tool_calls = tool_calls or []
        self.steps = steps
    
    def __str__(self) -> str:
        return self.output
    
    def __repr__(self) -> str:
        return f"AgentResult(output={self.output[:50]!r}..., success={self.success}, steps={self.steps})"
