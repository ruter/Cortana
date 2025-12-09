import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    ZEP_API_KEY = os.getenv("ZEP_API_KEY")
    # LLM Configuration
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY"))
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o")
    ONE_BALANCE_AUTH_KEY = os.getenv("ONE_BALANCE_AUTH_KEY", "")
    EXA_API_KEY = os.getenv("EXA_API_KEY", "")

    DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

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
