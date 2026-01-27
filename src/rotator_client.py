"""
Rotator Client Singleton
========================

Provides a centralized, lazily-initialized RotatingClient for LLM API calls
with automatic key rotation, failover, and resilience features.

Usage:
    from .rotator_client import get_rotating_client, rotating_completion
    
    # Get the client instance
    client = await get_rotating_client()
    
    # Or use the convenience wrapper
    response = await rotating_completion(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    
    # Anthropic-compatible requests
    response = await anthropic_messages(request)
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .config import config

logger = logging.getLogger(__name__)

# Global client instance
_rotating_client: Optional[Any] = None
_client_lock = asyncio.Lock()
_initialization_attempted = False


async def get_rotating_client():
    """
    Get or create the RotatingClient singleton.
    
    Returns the client instance, or None if rotator is disabled or unavailable.
    Thread-safe via asyncio lock.
    """
    global _rotating_client, _initialization_attempted
    
    if not config.ENABLE_ROTATOR:
        logger.debug("Rotator is disabled via ENABLE_ROTATOR=false")
        return None
    
    if _rotating_client is not None:
        return _rotating_client
    
    async with _client_lock:
        # Double-check after acquiring lock
        if _rotating_client is not None:
            return _rotating_client
        
        if _initialization_attempted:
            # Already tried and failed, don't retry
            return None
        
        _initialization_attempted = True
        
        try:
            from rotator_library import RotatingClient
            
            # Ensure keys are loaded
            config.load_rotator_keys()
            
            rotator_config = config.get_rotator_config()
            
            # Check if we have any keys to work with
            if not rotator_config["api_keys"] and not rotator_config["oauth_credentials"]:
                logger.warning("No API keys or OAuth credentials found for rotator. Falling back to legacy mode.")
                return None
            
            logger.info(f"Initializing RotatingClient with providers: {list(rotator_config['api_keys'].keys())}")
            
            # Create the client
            _rotating_client = RotatingClient(
                api_keys=rotator_config["api_keys"],
                oauth_credentials=rotator_config["oauth_credentials"],
                max_retries=rotator_config["max_retries"],
                global_timeout=rotator_config["global_timeout"],
                rotation_tolerance=rotator_config["rotation_tolerance"],
                usage_file_path=rotator_config["usage_file_path"],
                enable_request_logging=rotator_config["enable_request_logging"],
                configure_logging=rotator_config["configure_logging"],
                ignore_models=rotator_config["ignore_models"] or None,
                whitelist_models=rotator_config["whitelist_models"] or None,
                max_concurrent_requests_per_key=rotator_config["max_concurrent_requests_per_key"] or None,
            )
            
            logger.info("RotatingClient initialized successfully")
            return _rotating_client
            
        except ImportError as e:
            logger.warning(f"rotator_library not installed, falling back to legacy mode: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize RotatingClient: {e}")
            return None


async def close_rotating_client():
    """Close the rotating client and release resources."""
    global _rotating_client, _initialization_attempted
    
    async with _client_lock:
        if _rotating_client is not None:
            try:
                await _rotating_client.__aexit__(None, None, None)
                logger.info("RotatingClient closed")
            except Exception as e:
                logger.warning(f"Error closing RotatingClient: {e}")
            finally:
                _rotating_client = None
                _initialization_attempted = False


def normalize_model_name(model: str) -> str:
    """
    Normalize model name to provider/model format.
    
    Examples:
        "gpt-4o" -> "openai/gpt-4o"
        "gemini-2.5-flash" -> "gemini/gemini-2.5-flash"
        "claude-3-sonnet" -> "anthropic/claude-3-sonnet"
        "openai/gpt-4o" -> "openai/gpt-4o" (unchanged)
    """
    if "/" in model:
        return model
    
    model_lower = model.lower()
    
    # Detect provider from model name
    if model_lower.startswith("gpt-") or model_lower.startswith("o1") or model_lower.startswith("o3"):
        return f"openai/{model}"
    elif model_lower.startswith("gemini"):
        return f"gemini/{model}"
    elif model_lower.startswith("claude"):
        return f"anthropic/{model}"
    elif model_lower.startswith("qwen"):
        return f"qwen/{model}"
    elif model_lower.startswith("deepseek"):
        return f"deepseek/{model}"
    elif model_lower.startswith("llama") or model_lower.startswith("meta"):
        return f"meta/{model}"
    else:
        # Default to openai for unknown models
        return f"openai/{model}"


async def rotating_completion(
    model: Optional[str] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    stream: bool = False,
    **kwargs
) -> Any:
    """
    Make a completion request through the RotatingClient.
    
    Falls back to direct litellm if rotator is unavailable.
    
    Args:
        model: Model name (e.g., "gpt-4o" or "openai/gpt-4o")
        messages: List of message dicts
        stream: Whether to stream the response
        **kwargs: Additional arguments passed to acompletion
    
    Returns:
        Response object (or async generator if streaming)
    
    Raises:
        Exception if all retries fail
    """
    # Use default model if not specified
    if model is None:
        model = config.LLM_MODEL_NAME
    
    # Normalize model name
    model = normalize_model_name(model)
    
    # Try to get rotating client
    client = await get_rotating_client()
    
    if client is not None:
        # Use rotating client
        return await client.acompletion(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs
        )
    else:
        # Fallback to direct litellm
        import litellm
        
        logger.debug(f"Using direct litellm for model: {model}")
        
        # For fallback, we need to set the API key
        if config.LLM_API_KEY:
            kwargs.setdefault("api_key", config.LLM_API_KEY)
        if config.LLM_BASE_URL and "openai" in model.lower():
            kwargs.setdefault("api_base", config.LLM_BASE_URL)
        
        return await litellm.acompletion(
            model=model,
            messages=messages,
            stream=stream,
            **kwargs
        )


async def rotating_embedding(
    model: Optional[str] = None,
    input: Union[str, List[str]] = None,
    **kwargs
) -> Any:
    """
    Make an embedding request through the RotatingClient.
    
    Args:
        model: Embedding model name
        input: Text or list of texts to embed
        **kwargs: Additional arguments passed to aembedding
    
    Returns:
        Embedding response object
    """
    client = await get_rotating_client()
    
    if model is None:
        model = "openai/text-embedding-3-small"
    else:
        model = normalize_model_name(model)
    
    if client is not None:
        return await client.aembedding(
            model=model,
            input=input,
            **kwargs
        )
    else:
        import litellm
        
        if config.LLM_API_KEY:
            kwargs.setdefault("api_key", config.LLM_API_KEY)
        
        return await litellm.aembedding(
            model=model,
            input=input,
            **kwargs
        )


# =============================================================================
# Anthropic API Compatibility
# =============================================================================

async def anthropic_messages(
    request: Any,
    raw_request: Any = None,
    pre_request_callback: Any = None
) -> Any:
    """
    Handle Anthropic Messages API requests through the rotator.
    
    Accepts requests in Anthropic's format, translates them to OpenAI format
    internally, processes them through acompletion, and returns responses
    in Anthropic's format.
    
    Args:
        request: An AnthropicMessagesRequest object (from anthropic_compat.models)
        raw_request: Optional raw request object for client disconnect checks
        pre_request_callback: Optional async callback before each API request
    
    Returns:
        For non-streaming: dict in Anthropic Messages format
        For streaming: AsyncGenerator yielding Anthropic SSE format strings
    """
    client = await get_rotating_client()
    
    if client is not None:
        try:
            return await client.anthropic_messages(
                request=request,
                raw_request=raw_request,
                pre_request_callback=pre_request_callback
            )
        except AttributeError:
            logger.warning("RotatingClient does not support anthropic_messages, using fallback")
    
    # Fallback: Convert Anthropic request to OpenAI format manually
    return await _anthropic_fallback(request)


async def anthropic_count_tokens(request: Any) -> dict:
    """
    Handle Anthropic count_tokens API requests.
    
    Args:
        request: An AnthropicCountTokensRequest object
    
    Returns:
        Dict with input_tokens count in Anthropic format
    """
    client = await get_rotating_client()
    
    if client is not None:
        try:
            return await client.anthropic_count_tokens(request)
        except AttributeError:
            pass
    
    # Fallback: Use litellm token counter
    try:
        messages = request.messages if hasattr(request, 'messages') else []
        count = token_count(
            model=request.model if hasattr(request, 'model') else 'claude-3-sonnet',
            messages=messages
        )
        return {"input_tokens": count}
    except Exception as e:
        logger.warning(f"Token counting failed: {e}")
        return {"input_tokens": 0}


async def _anthropic_fallback(request: Any) -> dict:
    """
    Fallback implementation for Anthropic requests when rotator doesn't support it.
    
    Converts Anthropic format to OpenAI format, makes the request, and converts back.
    """
    # Extract fields from request
    model = getattr(request, 'model', 'claude-3-sonnet')
    messages = getattr(request, 'messages', [])
    max_tokens = getattr(request, 'max_tokens', 1024)
    system = getattr(request, 'system', None)
    
    # Build OpenAI-format messages
    openai_messages = []
    if system:
        openai_messages.append({"role": "system", "content": system})
    
    for msg in messages:
        if isinstance(msg, dict):
            openai_messages.append(msg)
        else:
            # Handle Anthropic message objects
            role = getattr(msg, 'role', 'user')
            content = getattr(msg, 'content', '')
            openai_messages.append({"role": role, "content": content})
    
    # Make request
    response = await rotating_completion(
        model=normalize_model_name(model),
        messages=openai_messages,
        max_tokens=max_tokens
    )
    
    # Convert response to Anthropic format
    content = ""
    if hasattr(response, 'choices') and response.choices:
        content = response.choices[0].message.content or ""
    
    return {
        "id": getattr(response, 'id', 'msg_fallback'),
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content}],
        "model": model,
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": getattr(response, 'usage', {}).get('prompt_tokens', 0),
            "output_tokens": getattr(response, 'usage', {}).get('completion_tokens', 0),
        }
    }


# =============================================================================
# Model and Provider Information
# =============================================================================

async def get_available_models(provider: Optional[str] = None) -> Union[Dict[str, List[str]], List[str]]:
    """
    Get available models from the rotating client.
    
    Args:
        provider: Optional provider name to filter by
    
    Returns:
        If provider specified: List of model names
        If no provider: Dict of {provider: [models]}
    """
    client = await get_rotating_client()
    
    if client is None:
        # Return default model only
        return {config.LLM_MODEL_NAME.split("/")[0] if "/" in config.LLM_MODEL_NAME else "openai": [config.LLM_MODEL_NAME]}
    
    if provider:
        return await client.get_available_models(provider)
    else:
        return await client.get_all_available_models(grouped=True)


async def get_key_pool_status() -> Dict[str, Any]:
    """
    Get the current status of the API key pool.
    
    Returns dict with:
        - providers: list of provider names
        - key_counts: dict of {provider: count}
        - rotator_enabled: bool
    """
    config.load_rotator_keys()
    
    providers = config.get_available_providers()
    key_counts = {p: config.get_key_count(p) for p in providers}
    
    return {
        "providers": providers,
        "key_counts": key_counts,
        "rotator_enabled": config.ENABLE_ROTATOR,
        "current_model": config.LLM_MODEL_NAME,
    }


# =============================================================================
# Usage Tracking and Statistics
# =============================================================================

def get_usage_file_path() -> str:
    """Get the path to the usage statistics file."""
    return config.ROTATOR_USAGE_FILE_PATH


def load_usage_stats() -> Dict[str, Any]:
    """
    Load usage statistics from the JSON file.
    
    Returns:
        Dict containing usage data, or empty dict if file doesn't exist
    """
    usage_path = get_usage_file_path()
    
    if not os.path.exists(usage_path):
        return {}
    
    try:
        with open(usage_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load usage stats: {e}")
        return {}


def get_usage_summary() -> Dict[str, Any]:
    """
    Get a summary of API key usage.
    
    Returns:
        Dict with usage summary including:
        - total_requests: int
        - total_tokens: int
        - by_provider: dict of provider stats
        - by_model: dict of model stats
        - last_updated: timestamp
    """
    stats = load_usage_stats()
    
    if not stats:
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "by_provider": {},
            "by_model": {},
            "last_updated": None,
            "file_path": get_usage_file_path(),
        }
    
    # Aggregate stats
    total_requests = 0
    total_tokens = 0
    total_cost = 0.0
    by_provider: Dict[str, Dict[str, Any]] = {}
    by_model: Dict[str, int] = {}
    
    # Parse the usage file format (rotator_library stores by key)
    for key_id, key_data in stats.items():
        if key_id.startswith("_"):  # Skip metadata keys
            continue
        
        if isinstance(key_data, dict):
            # Get provider from key pattern or metadata
            provider = key_data.get("provider", "unknown")
            
            requests = key_data.get("requests", 0) or key_data.get("success_count", 0)
            tokens = key_data.get("total_tokens", 0)
            cost = key_data.get("cost", 0.0)
            
            total_requests += requests
            total_tokens += tokens
            total_cost += cost
            
            if provider not in by_provider:
                by_provider[provider] = {"requests": 0, "tokens": 0, "cost": 0.0, "keys": 0}
            
            by_provider[provider]["requests"] += requests
            by_provider[provider]["tokens"] += tokens
            by_provider[provider]["cost"] += cost
            by_provider[provider]["keys"] += 1
            
            # Model stats
            model_stats = key_data.get("models", {})
            for model, model_data in model_stats.items():
                if model not in by_model:
                    by_model[model] = 0
                by_model[model] += model_data.get("requests", 0)
    
    # Get file modification time
    usage_path = get_usage_file_path()
    last_updated = None
    if os.path.exists(usage_path):
        try:
            mtime = os.path.getmtime(usage_path)
            last_updated = datetime.fromtimestamp(mtime).isoformat()
        except OSError:
            pass
    
    return {
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 4),
        "by_provider": by_provider,
        "by_model": by_model,
        "last_updated": last_updated,
        "file_path": usage_path,
    }


async def get_detailed_usage() -> Dict[str, Any]:
    """
    Get detailed usage information including current key states.
    
    Returns comprehensive usage data for monitoring.
    """
    summary = get_usage_summary()
    pool_status = await get_key_pool_status()
    
    return {
        **summary,
        **pool_status,
    }


# =============================================================================
# Token Counting
# =============================================================================

def token_count(model: str, text: str = None, messages: List[Dict[str, str]] = None) -> int:
    """
    Count tokens for text or messages using the rotating client.
    
    This is a synchronous operation as token counting doesn't require API calls.
    """
    try:
        # Try to use rotator's token counter if available
        if _rotating_client is not None:
            return _rotating_client.token_count(
                model=normalize_model_name(model),
                text=text,
                messages=messages
            )
    except Exception:
        pass
    
    # Fallback to litellm
    try:
        import litellm
        if messages:
            return litellm.token_counter(model=model, messages=messages)
        elif text:
            return litellm.token_counter(model=model, text=text)
    except Exception:
        pass
    
    # Rough estimate as last resort
    if text:
        return len(text) // 4
    elif messages:
        return sum(len(m.get("content", "")) for m in messages) // 4
    return 0
