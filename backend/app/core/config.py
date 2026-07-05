import os
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE = os.path.join(BASE_DIR, ".env")


class Settings(BaseSettings):
    APP_NAME: str = "Genesis AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://genesis:genesis@localhost:5432/genesis"
    REDIS_URL: str = "redis://localhost:6379/0"

    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: Optional[str] = None
    LLM_API_URL: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"

    COGNEE_API_KEY: Optional[str] = None
    COGNEE_API_URL: str = "https://api.cognee.ai/v1"
    COGNEE_DATASET: str = "genesis_memories"

    UPLOAD_DIR: str = "./data/uploads"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    AUTH_ENABLED: bool = False
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = {"env_file": ENV_FILE, "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
