from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from ..models import Model, Provider

class OAuthCredentials(BaseModel):
    refresh: str
    access: str
    expires: int  # Unix timestamp in milliseconds
    metadata: Dict[str, Any] = {}

class OAuthAuthInfo(BaseModel):
    url: str
    instructions: Optional[str] = None

class ProviderInterface(ABC):
    @property
    @abstractmethod
    def id(self) -> Provider:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def get_api_key(self, user_id: int) -> Optional[str]:
        """Retrieve the API key for this provider, handling OAuth refresh if needed."""
        pass

    @abstractmethod
    def get_models(self) -> List[Model]:
        """Return all models supported by this provider."""
        pass

class OAuthProviderInterface(ProviderInterface):
    @abstractmethod
    async def login(self, user_id: int) -> OAuthAuthInfo:
        """Start the OAuth login flow."""
        pass

    @abstractmethod
    async def complete_login(self, user_id: int, code: str) -> OAuthCredentials:
        """Complete the OAuth login flow with the provided code."""
        pass

    @abstractmethod
    async def refresh_token(self, credentials: OAuthCredentials) -> OAuthCredentials:
        """Refresh expired credentials."""
        pass
