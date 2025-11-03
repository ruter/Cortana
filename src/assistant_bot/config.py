from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    discord_token: str = Field(..., alias="DISCORD_TOKEN")

    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")
    google_base_url: str = Field("https://generativelanguage.googleapis.com/v1beta", alias="GOOGLE_BASE_URL")
    google_model: str = Field(..., alias="GOOGLE_MODEL")

    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    openrouter_model: str = Field(..., alias="OPENROUTER_MODEL")
    openrouter_max_output_tokens: PositiveInt = Field(1024, alias="OPENROUTER_MAX_OUTPUT_TOKENS")

    one_balance_auth_key: str = Field(..., alias="ONE_BALANCE_AUTH_KEY")

    memu_api_key: str = Field(..., alias="MEMU_API_KEY")
    memu_base_url: str = Field("https://api.memu.so", alias="MEMU_BASE_URL")
    memu_agent_id: str = Field("discord-assistant", alias="MEMU_AGENT_ID")
    memu_agent_name: str = Field("Cortana", alias="MEMU_AGENT_NAME")
    memu_user_name_fallback: str = Field("User", alias="MEMU_USER_NAME_FALLBACK")
    memu_retrieve_top_k: PositiveInt = Field(20, alias="MEMU_RETRIEVE_TOP_K")

    context_max_tokens: PositiveInt = Field(4096, alias="CONTEXT_MAX_TOKENS")
    llm_temperature: float = Field(0.2, alias="LLM_TEMPERATURE")
    llm_thinking_budget: PositiveInt = Field(1024, alias="LLM_THINKING_BUDGET")
    session_ttl_seconds: PositiveInt = Field(900, alias="SESSION_TTL_SECONDS")
    memorization_batch_size: Literal[2, 3, 4] = Field(3, alias="MEMORIZATION_BATCH_SIZE")
    agent_system_prompt: str = Field("You are Cortana, a concise AI assistant.", alias="AGENT_SYSTEM_PROMPT")

    notion_token: str = Field(..., alias="NOTION_TOKEN")

    log_level: str = Field("INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
