from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel

# Ported from pi-mono ai package

Api = Literal[
    "openai-completions",
    "openai-responses",
    "azure-openai-responses",
    "openai-codex-responses",
    "anthropic-messages",
    "bedrock-converse-stream",
    "google-generative-ai",
    "google-gemini-cli",
    "google-vertex"
]

Provider = Literal[
    "amazon-bedrock",
    "anthropic",
    "google",
    "google-gemini-cli",
    "google-antigravity",
    "google-vertex",
    "openai",
    "azure-openai-responses",
    "openai-codex",
    "github-copilot",
    "xai",
    "groq",
    "cerebras",
    "openrouter",
    "zai",
    "mistral",
    "minimax",
    "minimax-cn",
    "opencode"
]

class ModelCost(BaseModel):
    input: float  # $/million tokens
    output: float  # $/million tokens
    cacheRead: float = 0.0  # $/million tokens
    cacheWrite: float = 0.0  # $/million tokens

class Model(BaseModel):
    id: str
    name: str
    api: Api
    provider: Provider
    baseUrl: str
    reasoning: bool
    input_types: List[str]  # "text", "image"
    cost: ModelCost
    contextWindow: int
    maxTokens: int

def get_all_models() -> List[Model]:
    """Dynamically aggregate models from all registered providers."""
    from .providers import get_all_providers
    all_models = []
    for provider in get_all_providers():
        all_models.extend(provider.get_models())
    return all_models

def get_model(provider_id: Provider, model_id: str) -> Optional[Model]:
    """Retrieve a specific model from a provider."""
    from .providers import get_provider
    provider = get_provider(provider_id)
    if provider:
        for model in provider.get_models():
            if model.id == model_id:
                return model
    return None

def get_providers() -> List[Provider]:
    """Get IDs of all registered providers."""
    from .providers import get_all_providers
    return [p.id for p in get_all_providers()]

def get_models(provider_id: Provider) -> List[Model]:
    """Get all models for a specific provider."""
    from .providers import get_provider
    provider = get_provider(provider_id)
    return provider.get_models() if provider else []

def find_model_by_id(model_id: str) -> Optional[Model]:
    """Search across all providers for a model ID."""
    for model in get_all_models():
        if model.id == model_id:
            return model
    return None
