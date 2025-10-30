from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    discord_token: str = Field(..., alias="DISCORD_TOKEN")
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(..., alias="OPENROUTER_MODEL")
    memu_api_key: str = Field(..., alias="MEMU_API_KEY")
    memu_base_url: str = Field("https://api.memu.ai/v1", alias="MEMU_BASE_URL")
    memu_agent_id: str = Field("discord-assistant", alias="MEMU_AGENT_ID")
    memu_agent_name: str = Field("Cortana", alias="MEMU_AGENT_NAME")
    memu_user_name_fallback: str = Field("User", alias="MEMU_USER_NAME_FALLBACK")
    memu_retrieve_top_k: PositiveInt = Field(20, alias="MEMU_RETRIEVE_TOP_K")

    context_max_tokens: PositiveInt = Field(3000, alias="CONTEXT_MAX_TOKENS")
    session_ttl_seconds: PositiveInt = Field(900, alias="SESSION_TTL_SECONDS")
    memorization_batch_size: Literal[2, 3, 4] = Field(3, alias="MEMORIZATION_BATCH_SIZE")

    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    openrouter_temperature: float = Field(0.2, alias="OPENROUTER_TEMPERATURE")
    openrouter_max_output_tokens: PositiveInt = Field(800, alias="OPENROUTER_MAX_OUTPUT_TOKENS")

    log_level: str = Field("INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
