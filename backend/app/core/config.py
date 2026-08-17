"""Application configuration using Pydantic BaseSettings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application settings
    app_name: str = Field(
        default="Hierarchy & Buying-Role Classification Agent",
        alias="APP_NAME",
    )
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # LLM Settings
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_base_url: str | None = Field(default=None, alias="LLM_BASE_URL")
    llm_temperature: float = Field(default=0.0, alias="LLM_TEMPERATURE")

    # Graph Execution Settings
    max_retries: int = Field(default=2, alias="MAX_RETRIES")
    graph_timeout_seconds: int = Field(default=60, alias="GRAPH_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    """Returns cached instance of the settings."""
    return Settings()


settings = get_settings()
