"""Configuration management for the AI Resume Screener."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    anthropic_api_key: str
    app_name: str = "AI Resume Screener"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
