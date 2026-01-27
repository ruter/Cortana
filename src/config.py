import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


def _load_provider_api_keys() -> Dict[str, List[str]]:
    """
    Dynamically load all provider API keys from environment variables.
    
    Supports patterns like:
    - OPENAI_API_KEY, OPENAI_API_KEY_1, OPENAI_API_KEY_2
    - GEMINI_API_KEY, GEMINI_API_KEY_1
    - ANTHROPIC_API_KEY, etc.
    
    Returns a dict: {"openai": ["key1", "key2"], "gemini": ["key1"], ...}
    """
    api_keys: Dict[str, List[str]] = {}
    
    for key, value in os.environ.items():
        if not value:
            continue
            
        # Match patterns: PROVIDER_API_KEY or PROVIDER_API_KEY_N
        if (key.endswith("_API_KEY") or "_API_KEY_" in key):
            # Skip non-LLM keys
            skip_prefixes = (
                "PROXY_API_KEY", "SUPABASE", "ZEP", "EXA", 
                "DISCORD", "LLM_API_KEY"  # LLM_API_KEY is legacy single-key
            )
            if any(key.startswith(prefix) for prefix in skip_prefixes):
                continue
            
            # Extract provider name: "OPENAI_API_KEY_1" -> "openai"
            provider = key.split("_API_KEY")[0].lower()
            
            if provider not in api_keys:
                api_keys[provider] = []
            
            # Avoid duplicates
            if value not in api_keys[provider]:
                api_keys[provider].append(value)
    
    return api_keys


def _load_oauth_credentials() -> Dict[str, List[str]]:
    """
    Load OAuth credential file paths from environment variables.
    
    Supports patterns like:
    - GEMINI_CLI_OAUTH_CREDENTIALS=/path/to/creds.json
    - GEMINI_CLI_OAUTH_CREDENTIALS_1=/path/to/creds1.json
    - QWEN_CODE_OAUTH_CREDENTIALS=/path/to/qwen.json
    - ANTIGRAVITY_OAUTH_CREDENTIALS=/path/to/ag.json
    - IFLOW_OAUTH_CREDENTIALS=/path/to/iflow.json
    
    Returns a dict: {"gemini_cli": ["/path/to/creds.json"], ...}
    """
    oauth_credentials: Dict[str, List[str]] = {}
    
    for key, value in os.environ.items():
        if not value:
            continue
            
        if "_OAUTH_CREDENTIALS" in key:
            # Extract provider: "GEMINI_CLI_OAUTH_CREDENTIALS_1" -> "gemini_cli"
            provider = key.split("_OAUTH_CREDENTIALS")[0].lower()
            
            if provider not in oauth_credentials:
                oauth_credentials[provider] = []
            
            # Value can be a path or JSON string (for stateless deployment)
            if value not in oauth_credentials[provider]:
                oauth_credentials[provider].append(value)
    
    return oauth_credentials


def _parse_json_env(env_var: str, default: Optional[dict] = None) -> Optional[dict]:
    """Parse a JSON string from environment variable."""
    value = os.getenv(env_var, "")
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


class Config:
    # Discord Configuration
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    
    # Database Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Memory Configuration
    ZEP_API_KEY = os.getenv("ZEP_API_KEY")
    
    # --- LLM Configuration (Legacy single-key mode) ---
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY"))
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o")
    EXA_API_KEY = os.getenv("EXA_API_KEY", "")

    # --- Rotator Library Configuration ---
    # Enable/disable the rotating client (falls back to legacy single-key if disabled)
    ENABLE_ROTATOR = os.getenv("ENABLE_ROTATOR", "true").lower() == "true"
    
    # Core rotator settings
    ROTATOR_MAX_RETRIES = int(os.getenv("ROTATOR_MAX_RETRIES", "2"))
    ROTATOR_GLOBAL_TIMEOUT = int(os.getenv("ROTATOR_GLOBAL_TIMEOUT", "120"))
    ROTATOR_ROTATION_TOLERANCE = float(os.getenv("ROTATOR_ROTATION_TOLERANCE", "2.0"))
    ROTATOR_USAGE_FILE_PATH = os.getenv("ROTATOR_USAGE_FILE_PATH", "key_usage.json")
    ROTATOR_ENABLE_REQUEST_LOGGING = os.getenv("ROTATOR_ENABLE_REQUEST_LOGGING", "false").lower() == "true"
    ROTATOR_CONFIGURE_LOGGING = os.getenv("ROTATOR_CONFIGURE_LOGGING", "true").lower() == "true"
    
    # Model filtering (JSON arrays or comma-separated)
    # Example: ROTATOR_IGNORE_MODELS='{"openai": ["*-preview"], "gemini": ["gemini-1.0-*"]}'
    ROTATOR_IGNORE_MODELS = _parse_json_env("ROTATOR_IGNORE_MODELS", {})
    # Example: ROTATOR_WHITELIST_MODELS='{"openai": ["gpt-4o", "gpt-4-turbo"]}'
    ROTATOR_WHITELIST_MODELS = _parse_json_env("ROTATOR_WHITELIST_MODELS", {})
    
    # Per-provider concurrent request limits (JSON object)
    # Example: ROTATOR_MAX_CONCURRENT_PER_KEY='{"openai": 5, "gemini": 3}'
    ROTATOR_MAX_CONCURRENT_PER_KEY = _parse_json_env("ROTATOR_MAX_CONCURRENT_PER_KEY", {})
    
    # Dynamically loaded API keys and OAuth credentials
    ROTATOR_API_KEYS: Dict[str, List[str]] = {}
    ROTATOR_OAUTH_CREDENTIALS: Dict[str, List[str]] = {}

    # General Settings
    DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # --- Coding Agent Configuration ---
    # Ported from badlogic/pi-mono mom package
    
    # Feature Toggles
    ENABLE_BASH_TOOL = os.getenv("ENABLE_BASH_TOOL", "true").lower() == "true"
    ENABLE_FILE_TOOLS = os.getenv("ENABLE_FILE_TOOLS", "true").lower() == "true"
    ENABLE_SKILLS = os.getenv("ENABLE_SKILLS", "true").lower() == "true"
    
    # Workspace Configuration
    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/workspace")
    SKILLS_DIR = os.getenv("SKILLS_DIR", "/workspace/skills")
    
    # Bash Tool Limits
    BASH_TIMEOUT_DEFAULT = int(os.getenv("BASH_TIMEOUT_DEFAULT", "60"))
    BASH_OUTPUT_MAX_LINES = int(os.getenv("BASH_OUTPUT_MAX_LINES", "500"))
    BASH_OUTPUT_MAX_BYTES = int(os.getenv("BASH_OUTPUT_MAX_BYTES", "51200"))  # 50KB
    
    # File Tool Limits
    FILE_READ_MAX_LINES = int(os.getenv("FILE_READ_MAX_LINES", "1000"))

    @classmethod
    def load_rotator_keys(cls):
        """
        Load API keys and OAuth credentials for the rotator.
        Call this after environment is fully loaded.
        """
        cls.ROTATOR_API_KEYS = _load_provider_api_keys()
        cls.ROTATOR_OAUTH_CREDENTIALS = _load_oauth_credentials()
        
        # Backward compatibility: if no provider keys found but LLM_API_KEY exists,
        # add it as a single OpenAI key
        if not cls.ROTATOR_API_KEYS and cls.LLM_API_KEY:
            # Infer provider from model name or default to openai
            model = cls.LLM_MODEL_NAME.lower()
            if "gemini" in model:
                provider = "gemini"
            elif "claude" in model or "anthropic" in model:
                provider = "anthropic"
            elif "gpt" in model or "o1" in model or "o3" in model:
                provider = "openai"
            else:
                provider = "openai"
            
            cls.ROTATOR_API_KEYS[provider] = [cls.LLM_API_KEY]

    @classmethod
    def get_rotator_config(cls) -> dict:
        """
        Get configuration dict for RotatingClient initialization.
        """
        return {
            "api_keys": cls.ROTATOR_API_KEYS,
            "oauth_credentials": cls.ROTATOR_OAUTH_CREDENTIALS,
            "max_retries": cls.ROTATOR_MAX_RETRIES,
            "global_timeout": cls.ROTATOR_GLOBAL_TIMEOUT,
            "rotation_tolerance": cls.ROTATOR_ROTATION_TOLERANCE,
            "usage_file_path": cls.ROTATOR_USAGE_FILE_PATH,
            "enable_request_logging": cls.ROTATOR_ENABLE_REQUEST_LOGGING,
            "configure_logging": cls.ROTATOR_CONFIGURE_LOGGING,
            "ignore_models": cls.ROTATOR_IGNORE_MODELS,
            "whitelist_models": cls.ROTATOR_WHITELIST_MODELS,
            "max_concurrent_requests_per_key": cls.ROTATOR_MAX_CONCURRENT_PER_KEY,
        }

    @classmethod
    def validate(cls):
        missing = []
        if not cls.DISCORD_TOKEN: missing.append("DISCORD_TOKEN")
        if not cls.SUPABASE_URL: missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY: missing.append("SUPABASE_KEY")
        if not cls.ZEP_API_KEY: missing.append("ZEP_API_KEY")
        
        # Load rotator keys before validation
        cls.load_rotator_keys()
        
        # Check for LLM keys: either rotator keys or legacy single key
        if not cls.ROTATOR_API_KEYS and not cls.LLM_API_KEY:
            missing.append("LLM_API_KEY (or provider-specific keys like OPENAI_API_KEY)")

        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of configured LLM providers."""
        return list(cls.ROTATOR_API_KEYS.keys()) + list(cls.ROTATOR_OAUTH_CREDENTIALS.keys())

    @classmethod
    def get_key_count(cls, provider: str) -> int:
        """Get the number of API keys configured for a provider."""
        return len(cls.ROTATOR_API_KEYS.get(provider, []))


config = Config()
