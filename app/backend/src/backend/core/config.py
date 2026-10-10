"""Environment-backed application settings."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings shared across the API application."""

    app_name: str = "Feature Studio"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]
    database_url: SecretStr | None = None
    postgres_host: str | None = None
    postgres_port: int | None = None
    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o"
    openai_base_url: str | None = None
    openai_max_tokens: int = Field(default=1024, gt=0)
    agent_api_key: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for this process."""
    return Settings()


settings = get_settings()
