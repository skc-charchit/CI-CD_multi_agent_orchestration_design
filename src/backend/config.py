"""Application configuration settings."""

from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = "backend-app"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"


settings = Settings()
