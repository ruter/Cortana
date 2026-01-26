import aiohttp
import time
import base64
import hashlib
import secrets
from typing import List, Optional, Dict, Any
from .base import OAuthProviderInterface, OAuthCredentials, OAuthAuthInfo
from ..models import Model, Provider, get_models
from ..config import config
from .oauth import get_valid_access_token

# Ported from pi-mono ai package anthropic.ts

CLIENT_ID = base64.b64decode("OWQxYzI1MGEtZTYxYi00NGQ5LTg4ZWQtNTk0NGQxOTYyZjVl").decode("utf-8")
AUTHORIZE_URL = "https://claude.ai/oauth/authorize"
TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
REDIRECT_URI = "https://console.anthropic.com/oauth/code/callback"
SCOPES = "org:create_api_key user:profile user:inference"

class AnthropicProvider(OAuthProviderInterface):
    def __init__(self):
        self._verifiers: Dict[int, str] = {}

    @property
    def id(self) -> Provider:
        return "anthropic"

    @property
    def name(self) -> str:
        return "Anthropic (Claude Pro/Max)"

    async def get_api_key(self, user_id: int) -> Optional[str]:
        # Try OAuth first
        token = await get_valid_access_token(user_id, self.id, self)
        if token:
            return token
        
        # Fallback to global API key if configured for Anthropic
        if "anthropic" in config.LLM_BASE_URL.lower() or "claude" in config.LLM_MODEL_NAME.lower():
            return config.LLM_API_KEY
        return None

    def get_models(self) -> List[Model]:
        return get_models(self.id)

    async def login(self, user_id: int) -> OAuthAuthInfo:
        # Generate PKCE
        verifier = secrets.token_urlsafe(32)
        self._verifiers[user_id] = verifier
        
        sha256 = hashlib.sha256(verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').replace('=', '')

        params = {
            "code": "true",
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": verifier
        }
        
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{AUTHORIZE_URL}?{query}"
        
        return OAuthAuthInfo(
            url=url,
            instructions="1. Open the URL and log in to Claude.ai\n2. After authorization, you will be redirected to a page that says 'Authentication Successful'.\n3. Copy the code from that page and paste it here."
        )

    async def complete_login(self, user_id: int, auth_code: str) -> OAuthCredentials:
        verifier = self._verifiers.get(user_id)
        if not verifier:
            raise ValueError("Login session expired or not found")

        # auth_code is usually code#state
        splits = auth_code.split("#")
        code = splits[0]
        state = splits[1] if len(splits) > 1 else verifier

        async with aiohttp.ClientSession() as session:
            payload = {
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "code": code,
                "state": state,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": verifier
            }
            
            async with session.post(TOKEN_URL, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Token exchange failed: {error_text}")
                
                data = await resp.json()
                
                expires_at = int(time.time() * 1000) + data["expires_in"] * 1000 - 5 * 60 * 1000
                
                return OAuthCredentials(
                    refresh=data["refresh_token"],
                    access=data["access_token"],
                    expires=expires_at
                )

    async def refresh_token(self, credentials: OAuthCredentials) -> OAuthCredentials:
        async with aiohttp.ClientSession() as session:
            payload = {
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "refresh_token": credentials.refresh
            }
            
            async with session.post(TOKEN_URL, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Token refresh failed: {error_text}")
                
                data = await resp.json()
                
                expires_at = int(time.time() * 1000) + data["expires_in"] * 1000 - 5 * 60 * 1000
                
                return OAuthCredentials(
                    refresh=data["refresh_token"],
                    access=data["access_token"],
                    expires=expires_at
                )
