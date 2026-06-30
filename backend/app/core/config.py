from pydantic_settings import BaseSettings
from typing import Optional


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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
