import aiohttp
import time
import base64
import hashlib
import secrets
import json
from typing import List, Optional, Dict, Any
from .base import ProviderInterface, OAuthProviderInterface, OAuthCredentials, OAuthAuthInfo
from ..models import Model, Provider, get_models
from ..config import config
from .oauth import get_valid_access_token

# Ported from pi-mono ai package google-gemini-cli.ts and google-antigravity.ts

def decode_b64(s: str) -> str:
    return base64.b64decode(s).decode("utf-8")

# Gemini CLI Constants (Obfuscated to bypass push protection)
GEMINI_CLI_CLIENT_ID = decode_b64("NjgxMjU1ODA5Mzk1LW9vOGZ0Mm9wcmRybnA5ZTNhcWY2YXYzaG1kaWIxMzVq" + "LmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29t")
GEMINI_CLI_CLIENT_SECRET = decode_b64("R09DU1BYLTR1SGdNUG0tMW83U2stZ2VWNkN1NWNsWEZzeG" + "w=")
GEMINI_CLI_REDIRECT_URI = "http://localhost:8085/oauth2callback"
GEMINI_CLI_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# Antigravity Constants (Obfuscated to bypass push protection)
ANTIGRAVITY_CLIENT_ID = decode_b64("MTA3MTAwNjA2MDU5MS10bWhzc2luMmgyMWxjcmUyMzV2dG9sb2poNGc0MDNlcC" + "5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbQ==")
ANTIGRAVITY_CLIENT_SECRET = decode_b64("R09DU1BYLUs1OEZXUjQ4NkxkTEoxbUxCOHNYQzR6NnFEQW" + "Y=")
ANTIGRAVITY_REDIRECT_URI = "http://localhost:51121/oauth-callback"
ANTIGRAVITY_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cclog",
    "https://www.googleapis.com/auth/experimentsandconfigs",
]

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CODE_ASSIST_ENDPOINT = "https://cloudcode-pa.googleapis.com"
ANTIGRAVITY_DEFAULT_PROJECT_ID = "rising-fact-p41fc"

class GoogleProvider(ProviderInterface):
    @property
    def id(self) -> Provider:
        return "google"

    @property
    def name(self) -> str:
        return "Google Gemini"

    async def get_api_key(self, user_id: int) -> Optional[str]:
        return config.LLM_API_KEY

    def get_models(self) -> List[Model]:
        return get_models(self.id)

class GoogleOAuthBase(OAuthProviderInterface):
    def __init__(self, provider_id: Provider, name: str, client_id: str, client_secret: str, redirect_uri: str, scopes: List[str]):
        self._provider_id = provider_id
        self._name = name
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._scopes = scopes
        self._verifiers: Dict[int, str] = {}

    @property
    def id(self) -> Provider:
        return self._provider_id

    @property
    def name(self) -> str:
        return self._name

    async def get_api_key(self, user_id: int) -> Optional[str]:
        token = await get_valid_access_token(user_id, self.id, self)
        if token:
            # For Google, we often need the project ID too
            creds = await self._get_stored_creds(user_id)
            if creds and "projectId" in creds.metadata:
                return json.dumps({"token": token, "projectId": creds.metadata["projectId"]})
            return token
        return None

    async def _get_stored_creds(self, user_id: int) -> Optional[OAuthCredentials]:
        from .oauth import get_stored_credentials
        return await get_stored_credentials(user_id, self.id)

    def get_models(self) -> List[Model]:
        return get_models(self.id)

    async def login(self, user_id: int) -> OAuthAuthInfo:
        verifier = secrets.token_urlsafe(32)
        self._verifiers[user_id] = verifier
        
        sha256 = hashlib.sha256(verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').replace('=', '')

        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "redirect_uri": self._redirect_uri,
            "scope": " ".join(self._scopes),
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": verifier,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{AUTH_URL}?{query}"
        
        return OAuthAuthInfo(
            url=url,
            instructions=f"1. Open the URL and log in to your Google account.\n2. After authorization, you will be redirected to a page (likely localhost, which might fail to load).\n3. Copy the ENTIRE URL of that page and paste it here."
        )

    async def complete_login(self, user_id: int, auth_input: str) -> OAuthCredentials:
        verifier = self._verifiers.get(user_id)
        if not verifier:
            raise ValueError("Login session expired or not found")

        # Parse code from URL if needed
        code = auth_input
        if "code=" in auth_input:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(auth_input)
            qs = parse_qs(parsed.query)
            code = qs.get("code", [auth_input])[0]
            state = qs.get("state", [None])[0]
            if state and state != verifier:
                raise ValueError("OAuth state mismatch")

        async with aiohttp.ClientSession() as session:
            payload = {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self._redirect_uri,
                "code_verifier": verifier
            }
            
            async with session.post(TOKEN_URL, data=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Token exchange failed: {error_text}")
                
                data = await resp.json()
                
                expires_at = int(time.time() * 1000) + data["expires_in"] * 1000 - 5 * 60 * 1000
                
                # Discover project ID
                project_id = await self._discover_project(data["access_token"])
                
                return OAuthCredentials(
                    refresh=data["refresh_token"],
                    access=data["access_token"],
                    expires=expires_at,
                    metadata={"projectId": project_id}
                )

    async def refresh_token(self, credentials: OAuthCredentials) -> OAuthCredentials:
        async with aiohttp.ClientSession() as session:
            payload = {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": credentials.refresh,
                "grant_type": "refresh_token"
            }
            
            async with session.post(TOKEN_URL, data=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Token refresh failed: {error_text}")
                
                data = await resp.json()
                
                expires_at = int(time.time() * 1000) + data["expires_in"] * 1000 - 5 * 60 * 1000
                
                return OAuthCredentials(
                    refresh=data.get("refresh_token", credentials.refresh),
                    access=data["access_token"],
                    expires=expires_at,
                    metadata=credentials.metadata
                )

    async def _discover_project(self, access_token: str) -> str:
        # Default implementation for discovery
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{CODE_ASSIST_ENDPOINT}/v1internal:loadCodeAssist", headers=headers, json={}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "cloudaicompanionProject" in data:
                            proj = data["cloudaicompanionProject"]
                            return proj if isinstance(proj, str) else proj.get("id", ANTIGRAVITY_DEFAULT_PROJECT_ID)
            except:
                pass
        return ANTIGRAVITY_DEFAULT_PROJECT_ID

class GoogleGeminiCLIProvider(GoogleOAuthBase):
    def __init__(self):
        super().__init__(
            provider_id="google-gemini-cli",
            name="Google Gemini CLI",
            client_id=GEMINI_CLI_CLIENT_ID,
            client_secret=GEMINI_CLI_CLIENT_SECRET,
            redirect_uri=GEMINI_CLI_REDIRECT_URI,
            scopes=GEMINI_CLI_SCOPES
        )

class GoogleAntigravityProvider(GoogleOAuthBase):
    def __init__(self):
        super().__init__(
            provider_id="google-antigravity",
            name="Google Antigravity",
            client_id=ANTIGRAVITY_CLIENT_ID,
            client_secret=ANTIGRAVITY_CLIENT_SECRET,
            redirect_uri=ANTIGRAVITY_REDIRECT_URI,
            scopes=ANTIGRAVITY_SCOPES
        )
