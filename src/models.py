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

# A subset of models from pi-mono MODELS
MODELS: Dict[Provider, Dict[str, Model]] = {
    "openai": {
        "gpt-4o": Model(
            id="gpt-4o",
            name="GPT-4o",
            api="openai-responses",
            provider="openai",
            baseUrl="https://api.openai.com/v1",
            reasoning=False,
            input_types=["text", "image"],
            cost=ModelCost(input=2.5, output=10.0, cacheRead=1.25, cacheWrite=2.5),
            contextWindow=128000,
            maxTokens=16384
        ),
        "gpt-4o-mini": Model(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            api="openai-responses",
            provider="openai",
            baseUrl="https://api.openai.com/v1",
            reasoning=False,
            input_types=["text", "image"],
            cost=ModelCost(input=0.15, output=0.6, cacheRead=0.075, cacheWrite=0.15),
            contextWindow=128000,
            maxTokens=16384
        )
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": Model(
            id="claude-3-5-sonnet-20241022",
            name="Claude 3.5 Sonnet",
            api="anthropic-messages",
            provider="anthropic",
            baseUrl="https://api.anthropic.com/v1",
            reasoning=False,
            input_types=["text", "image"],
            cost=ModelCost(input=3.0, output=15.0, cacheRead=0.3, cacheWrite=3.75),
            contextWindow=200000,
            maxTokens=8192
        )
    },
    "google": {
        "gemini-1.5-pro": Model(
            id="gemini-1.5-pro",
            name="Gemini 1.5 Pro",
            api="google-generative-ai",
            provider="google",
            baseUrl="https://generativelanguage.googleapis.com/v1beta",
            reasoning=False,
            input_types=["text", "image"],
            cost=ModelCost(input=3.5, output=10.5),
            contextWindow=2000000,
            maxTokens=8192
        )
    },
    "google-gemini-cli": {
        "gemini-2.0-flash": Model(
            id="gemini-2.0-flash",
            name="Gemini 2.0 Flash (CLI)",
            api="google-gemini-cli",
            provider="google-gemini-cli",
            baseUrl="https://cloudcode-pa.googleapis.com",
            reasoning=False,
            input_types=["text", "image"],
            cost=ModelCost(input=0.0, output=0.0),
            contextWindow=1000000,
            maxTokens=8192
        )
    },
    "google-antigravity": {
        "gemini-3-alpha": Model(
            id="gemini-3-alpha",
            name="Gemini 3 Alpha (Antigravity)",
            api="google-gemini-cli",
            provider="google-antigravity",
            baseUrl="https://cloudcode-pa.googleapis.com",
            reasoning=True,
            input_types=["text", "image"],
            cost=ModelCost(input=0.0, output=0.0),
            contextWindow=2000000,
            maxTokens=16384
        )
    }
}

def get_model(provider: Provider, model_id: str) -> Optional[Model]:
    provider_models = MODELS.get(provider)
    if provider_models:
        return provider_models.get(model_id)
    return None

def get_providers() -> List[Provider]:
    return list(MODELS.keys())

def get_models(provider: Provider) -> List[Model]:
    models = MODELS.get(provider)
    return list(models.values()) if models else []

def find_model_by_id(model_id: str) -> Optional[Model]:
    """Search across all providers for a model ID."""
    for provider_models in MODELS.values():
        if model_id in provider_models:
            return provider_models[model_id]
    return None
