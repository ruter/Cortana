"""
Cortana Context Module
======================

Provides CortanaContext as a replacement for PydanticAI's RunContext,
maintaining the same deps access pattern for tool functions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CortanaContext:
    """
    Context object passed to tool functions.
    
    Replaces PydanticAI's RunContext[Dict[str, Any]] with the same
    deps access pattern for backward compatibility with existing tools.
    
    Attributes:
        deps: Dictionary containing user_info, zep_memory_context, etc.
    
    Usage in tools:
        async def my_tool(ctx: CortanaContext, arg: str) -> str:
            user_id = ctx.deps['user_info']['id']
            ...
    """
    deps: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Convenience method to get a value from deps."""
        return self.deps.get(key, default)
