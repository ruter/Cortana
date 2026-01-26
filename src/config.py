import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord Configuration
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    
    # Database Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Memory Configuration
    ZEP_API_KEY = os.getenv("ZEP_API_KEY")
    
    # LLM Configuration
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY"))
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o")
    ONE_BALANCE_AUTH_KEY = os.getenv("ONE_BALANCE_AUTH_KEY", "")
    EXA_API_KEY = os.getenv("EXA_API_KEY", "")

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
    def validate(cls):
        missing = []
        if not cls.DISCORD_TOKEN: missing.append("DISCORD_TOKEN")
        if not cls.SUPABASE_URL: missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY: missing.append("SUPABASE_KEY")
        if not cls.ZEP_API_KEY: missing.append("ZEP_API_KEY")
        if not cls.LLM_API_KEY: missing.append("LLM_API_KEY")

        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

config = Config()
