from typing import List, Optional
from .base import ProviderInterface
from ..models import Model, Provider, get_models
from ..config import config

class OpenAIProvider(ProviderInterface):
    @property
    def id(self) -> Provider:
        return "openai"

    @property
    def name(self) -> str:
        return "OpenAI"

    async def get_api_key(self, user_id: int) -> Optional[str]:
        # For now, we use the global API key from config
        # In the future, we could allow users to provide their own keys
        return config.LLM_API_KEY

    def get_models(self) -> List[Model]:
        return get_models(self.id)
