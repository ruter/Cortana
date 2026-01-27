"""
OAuth Handler for Multi-Provider LLM Access
=============================================

Handles OAuth credential loading, token management, and provider-specific
OAuth implementations (Gemini CLI, Qwen Code, Antigravity, iFlow).

Usage:
    from .oauth_handler import OAuthHandler
    
    handler = OAuthHandler()
    
    # Load and get tokens for a provider
    token = await handler.get_token("gemini_cli")
    
    # Refresh a specific credential
    await handler.refresh_token("gemini_cli", credential_index=0)
    
    # List available OAuth providers
    providers = handler.get_available_providers()
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OAuthCredential:
    """Represents a single OAuth credential with token management."""
    
    def __init__(self, provider: str, source: str, cred_data: dict):
        """
        Args:
            provider: Provider name (e.g., "gemini_cli", "qwen_code")
            source: Path or identifier for the credential
            cred_data: OAuth credential data (access_token, refresh_token, etc.)
        """
        self.provider = provider
        self.source = source
        self.data = cred_data
        self.last_refreshed = datetime.now()
        self.refresh_count = 0
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired or about to expire."""
        if "expires_at" not in self.data:
            # No expiry info, assume valid
            return False
        
        expires_at = self.data["expires_at"]
        if isinstance(expires_at, str):
            try:
                expires_at = float(expires_at)
            except (ValueError, TypeError):
                return False
        
        # Consider expired if within buffer period
        return datetime.fromtimestamp(expires_at) <= datetime.now() + timedelta(seconds=buffer_seconds)
    
    def time_to_expiry(self) -> Optional[int]:
        """Return seconds until token expires, or None if no expiry."""
        if "expires_at" not in self.data:
            return None
        
        expires_at = self.data["expires_at"]
        if isinstance(expires_at, str):
            try:
                expires_at = float(expires_at)
            except (ValueError, TypeError):
                return None
        
        secs_left = expires_at - datetime.now().timestamp()
        return max(0, int(secs_left))
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token."""
        return self.data.get("access_token")
    
    def get_refresh_token(self) -> Optional[str]:
        """Get refresh token (if available)."""
        return self.data.get("refresh_token")


class OAuthHandler:
    """Manages OAuth credentials for multiple providers."""
    
    PROVIDER_CONFIGS = {
        "gemini_cli": {
            "name": "Gemini CLI",
            "token_endpoint": "https://oauth2.googleapis.com/token",
            "supports_refresh": True,
        },
        "qwen_code": {
            "name": "Qwen Code",
            "token_endpoint": "https://api.aliyun.com/oauth/token",
            "supports_refresh": True,
        },
        "antigravity": {
            "name": "Antigravity",
            "token_endpoint": "https://api.antigravity.dev/oauth/token",
            "supports_refresh": True,
        },
        "iflow": {
            "name": "iFlow",
            "token_endpoint": "https://oauth.iflow.dev/token",
            "supports_refresh": True,
        },
    }
    
    def __init__(self):
        """Initialize OAuth handler."""
        self.credentials: Dict[str, List[OAuthCredential]] = {}
        self._lock = asyncio.Lock()
        self._load_credentials()
    
    def _load_credentials(self) -> None:
        """Load OAuth credentials from environment variables."""
        oauth_env_vars = {}
        
        # Collect all OAuth credential environment variables
        for key, value in os.environ.items():
            if "_OAUTH_CREDENTIALS" in key and value:
                oauth_env_vars[key] = value
        
        if not oauth_env_vars:
            logger.info("No OAuth credentials found in environment")
            return
        
        for env_key, source in oauth_env_vars.items():
            # Extract provider: "GEMINI_CLI_OAUTH_CREDENTIALS_1" -> "gemini_cli"
            provider = env_key.split("_OAUTH_CREDENTIALS")[0].lower()
            
            if provider not in self.PROVIDER_CONFIGS:
                logger.warning(f"Unknown OAuth provider: {provider}")
                continue
            
            # Load credential data
            cred_data = self._load_credential_data(source)
            if not cred_data:
                logger.warning(f"Failed to load credential from {source}")
                continue
            
            # Store credential
            if provider not in self.credentials:
                self.credentials[provider] = []
            
            credential = OAuthCredential(provider, source, cred_data)
            self.credentials[provider].append(credential)
            logger.info(f"Loaded OAuth credential for {provider} from {source}")
    
    def _load_credential_data(self, source: str) -> Optional[Dict[str, Any]]:
        """
        Load credential data from a source (file path or JSON string).
        
        Args:
            source: File path or JSON string
            
        Returns:
            Credential data dict or None if failed
        """
        # Try as file path first
        if os.path.isfile(source):
            try:
                with open(source, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load credential from {source}: {e}")
                return None
        
        # Try as JSON string
        try:
            return json.loads(source)
        except json.JSONDecodeError:
            logger.error(f"Invalid credential source (not a file or JSON): {source}")
            return None
    
    async def get_token(self, provider: str, credential_index: int = 0) -> Optional[str]:
        """
        Get access token for a provider.
        
        Args:
            provider: Provider name (e.g., "gemini_cli")
            credential_index: Which credential to use (0 = first)
            
        Returns:
            Access token string or None
        """
        async with self._lock:
            if provider not in self.credentials or not self.credentials[provider]:
                logger.warning(f"No OAuth credentials for provider: {provider}")
                return None
            
            if credential_index >= len(self.credentials[provider]):
                logger.warning(f"Credential index {credential_index} out of range for {provider}")
                return None
            
            cred = self.credentials[provider][credential_index]
            
            # Check if expired and try refresh
            if cred.is_expired():
                logger.info(f"Token for {provider} is expired, attempting refresh...")
                refreshed = await self._refresh_token_internal(cred)
                if not refreshed:
                    logger.error(f"Failed to refresh token for {provider}")
                    return None
            
            return cred.get_access_token()
    
    async def refresh_token(self, provider: str, credential_index: int = 0) -> bool:
        """
        Manually refresh token for a provider.
        
        Args:
            provider: Provider name
            credential_index: Which credential to refresh
            
        Returns:
            True if refresh successful, False otherwise
        """
        async with self._lock:
            if provider not in self.credentials or not self.credentials[provider]:
                logger.warning(f"No OAuth credentials for provider: {provider}")
                return False
            
            if credential_index >= len(self.credentials[provider]):
                logger.warning(f"Credential index {credential_index} out of range for {provider}")
                return False
            
            cred = self.credentials[provider][credential_index]
            return await self._refresh_token_internal(cred)
    
    async def _refresh_token_internal(self, cred: OAuthCredential) -> bool:
        """
        Internal token refresh implementation.
        
        Args:
            cred: OAuthCredential instance
            
        Returns:
            True if refresh successful
        """
        refresh_token = cred.get_refresh_token()
        if not refresh_token:
            logger.error(f"No refresh token available for {cred.provider}")
            return False
        
        provider_config = self.PROVIDER_CONFIGS.get(cred.provider)
        if not provider_config or not provider_config.get("supports_refresh"):
            logger.error(f"Token refresh not supported for {cred.provider}")
            return False
        
        try:
            import aiohttp
            
            token_endpoint = provider_config["token_endpoint"]
            
            # Prepare refresh request (varies by provider)
            refresh_data = self._prepare_refresh_request(cred.provider, refresh_token)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_endpoint, data=refresh_data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        logger.error(f"Token refresh failed for {cred.provider}: HTTP {resp.status}")
                        return False
                    
                    new_token_data = await resp.json()
                    
                    # Update credential with new token
                    cred.data.update(new_token_data)
                    cred.last_refreshed = datetime.now()
                    cred.refresh_count += 1
                    
                    # Save back to file if source is a file path
                    if os.path.isfile(cred.source):
                        try:
                            with open(cred.source, 'w') as f:
                                json.dump(cred.data, f, indent=2)
                            logger.info(f"Updated credential file: {cred.source}")
                        except IOError as e:
                            logger.warning(f"Failed to save updated credential: {e}")
                    
                    logger.info(f"Successfully refreshed token for {cred.provider}")
                    return True
                    
        except Exception as e:
            logger.error(f"Token refresh error for {cred.provider}: {e}")
            return False
    
    def _prepare_refresh_request(self, provider: str, refresh_token: str) -> dict:
        """
        Prepare provider-specific token refresh request.
        
        Args:
            provider: Provider name
            refresh_token: Refresh token
            
        Returns:
            Request data dict
        """
        # Standard OAuth 2.0 refresh request
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        # Provider-specific handling
        if provider == "gemini_cli":
            # Gemini CLI uses Google OAuth
            data["client_id"] = os.getenv("GEMINI_CLIENT_ID", "")
            data["client_secret"] = os.getenv("GEMINI_CLIENT_SECRET", "")
        elif provider == "qwen_code":
            data["client_id"] = os.getenv("QWEN_CLIENT_ID", "")
            data["client_secret"] = os.getenv("QWEN_CLIENT_SECRET", "")
        elif provider == "antigravity":
            data["client_id"] = os.getenv("ANTIGRAVITY_CLIENT_ID", "")
            data["client_secret"] = os.getenv("ANTIGRAVITY_CLIENT_SECRET", "")
        elif provider == "iflow":
            data["client_id"] = os.getenv("IFLOW_CLIENT_ID", "")
            data["client_secret"] = os.getenv("IFLOW_CLIENT_SECRET", "")
        
        return data
    
    def get_available_providers(self) -> List[str]:
        """Get list of configured OAuth providers."""
        return list(self.credentials.keys())
    
    def get_credential_count(self, provider: str) -> int:
        """Get number of credentials for a provider."""
        return len(self.credentials.get(provider, []))
    
    def get_credential_status(self, provider: str, credential_index: int = 0) -> Optional[Dict[str, Any]]:
        """
        Get status information for a credential.
        
        Args:
            provider: Provider name
            credential_index: Credential index
            
        Returns:
            Status dict with expiry info, or None
        """
        if provider not in self.credentials or not self.credentials[provider]:
            return None
        
        if credential_index >= len(self.credentials[provider]):
            return None
        
        cred = self.credentials[provider][credential_index]
        
        return {
            "provider": provider,
            "index": credential_index,
            "source": cred.source,
            "is_expired": cred.is_expired(),
            "time_to_expiry": cred.time_to_expiry(),
            "last_refreshed": cred.last_refreshed.isoformat(),
            "refresh_count": cred.refresh_count,
            "has_refresh_token": bool(cred.get_refresh_token()),
        }
    
    def list_all_credentials(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get status for all credentials."""
        result = {}
        for provider in self.get_available_providers():
            result[provider] = []
            for i in range(self.get_credential_count(provider)):
                status = self.get_credential_status(provider, i)
                if status:
                    result[provider].append(status)
        return result


# Global instance
_oauth_handler: Optional[OAuthHandler] = None


async def get_oauth_handler() -> OAuthHandler:
    """Get or create the OAuth handler singleton."""
    global _oauth_handler
    if _oauth_handler is None:
        _oauth_handler = OAuthHandler()
    return _oauth_handler
