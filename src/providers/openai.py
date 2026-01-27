from typing import List, Optional
from .base import ProviderInterface
from ..models import Model, ModelCost, Provider
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
        return [
            Model(
                id="gpt-4o",
                name="GPT-4o",
                api="openai-responses",
                provider=self.id,
                baseUrl="https://api.openai.com/v1",
                reasoning=False,
                input_types=["text", "image"],
                cost=ModelCost(input=2.5, output=10.0, cacheRead=1.25, cacheWrite=2.5),
                contextWindow=128000,
                maxTokens=16384
            ),
            Model(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                api="openai-responses",
                provider=self.id,
                baseUrl="https://api.openai.com/v1",
                reasoning=False,
                input_types=["text", "image"],
                cost=ModelCost(input=0.15, output=0.6, cacheRead=0.075, cacheWrite=0.15),
                contextWindow=128000,
                maxTokens=16384
            )
        ]
