from typing import Dict, List, Optional
from .base import ProviderInterface, OAuthProviderInterface
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from ..models import Provider

_providers: Dict[Provider, ProviderInterface] = {
    "openai": OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "google": GoogleProvider()
}

def get_provider(provider_id: Provider) -> Optional[ProviderInterface]:
    return _providers.get(provider_id)

def get_all_providers() -> List[ProviderInterface]:
    return list(_providers.values())

def get_oauth_providers() -> List[OAuthProviderInterface]:
    return [p for p in _providers.values() if isinstance(p, OAuthProviderInterface)]
