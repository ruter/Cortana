"""
Tool Registry Module
====================

Provides the ToolSpec dataclass and tool registration utilities
for the custom CortanaAgent orchestrator.
"""

import inspect
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, get_type_hints

from pydantic import BaseModel, Field, create_model


ToolFn = Callable[..., Awaitable[str]]


@dataclass
class ToolSpec:
    """
    Specification for a registered tool.
    
    Attributes:
        name: The function name (used by the LLM to call it).
        description: Description from the function's docstring.
        fn: The async function to execute.
        input_model: Pydantic model for validating/parsing arguments.
    """
    name: str
    description: str
    fn: ToolFn
    input_model: Type[BaseModel]
    
    def openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI tools format for API calls."""
        schema = self.input_model.model_json_schema()
        
        # Remove title and definitions that OpenAI doesn't need
        schema.pop("title", None)
        schema.pop("$defs", None)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }


def _get_type_for_annotation(annotation: Any) -> Any:
    """Convert Python type annotations to Pydantic-compatible types."""
    # Handle Optional types
    origin = getattr(annotation, "__origin__", None)
    if origin is type(None):
        return type(None)
    
    # datetime stays as datetime - Pydantic handles ISO string parsing
    if annotation is datetime:
        return datetime
    
    return annotation


def _extract_param_description(docstring: str, param_name: str) -> str:
    """Extract parameter description from docstring Args section."""
    if not docstring:
        return ""
    
    lines = docstring.split("\n")
    in_args = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if in_args:
            if stripped and not stripped.startswith("-") and ":" in stripped:
                # Check for "Returns:" or other sections
                if stripped.lower().startswith(("returns:", "raises:", "example")):
                    break
            if stripped.startswith(f"{param_name}:"):
                # Found the parameter
                desc = stripped[len(param_name) + 1:].strip()
                return desc
    return ""


def create_tool_spec(fn: ToolFn) -> ToolSpec:
    """
    Create a ToolSpec from an async function.
    
    Automatically generates a Pydantic input model from the function's
    type annotations (excluding the first 'ctx' parameter).
    
    Args:
        fn: The async tool function to wrap.
    
    Returns:
        ToolSpec with auto-generated input model.
    """
    name = fn.__name__
    docstring = fn.__doc__ or ""
    
    # Extract first line of docstring as description
    description = docstring.split("\n")[0].strip() if docstring else name
    
    # Get function signature
    sig = inspect.signature(fn)
    hints = get_type_hints(fn)
    
    # Build field definitions for Pydantic model (skip 'ctx' parameter)
    fields: Dict[str, Any] = {}
    
    for param_name, param in sig.parameters.items():
        if param_name == "ctx":
            continue  # Skip the context parameter
        
        # Get type annotation
        annotation = hints.get(param_name, str)
        
        # Get default value
        if param.default is inspect.Parameter.empty:
            default = ...  # Required field
        else:
            default = param.default
        
        # Get description from docstring
        param_desc = _extract_param_description(docstring, param_name)
        
        # Create field with description
        if param_desc:
            fields[param_name] = (annotation, Field(default=default, description=param_desc))
        else:
            fields[param_name] = (annotation, default)
    
    # Create dynamic Pydantic model
    model_name = f"{name.title().replace('_', '')}Args"
    input_model = create_model(model_name, **fields)
    
    return ToolSpec(
        name=name,
        description=description,
        fn=fn,
        input_model=input_model,
    )


class ToolRegistry:
    """
    Registry for managing tool specifications.
    
    Provides methods to register tools and convert them to OpenAI format.
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}
    
    def register(self, fn: ToolFn) -> ToolFn:
        """
        Register a tool function.
        
        Can be used as a decorator or called directly.
        
        Args:
            fn: The async tool function to register.
        
        Returns:
            The original function (for decorator use).
        """
        spec = create_tool_spec(fn)
        self._tools[spec.name] = spec
        return fn
    
    def register_spec(self, spec: ToolSpec) -> None:
        """Register a pre-built ToolSpec."""
        self._tools[spec.name] = spec
    
    def get(self, name: str) -> Optional[ToolSpec]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all(self) -> List[ToolSpec]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def openai_tools(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI format."""
        return [t.openai_tool() for t in self._tools.values()]
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
