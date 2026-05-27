from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://fund:fund123@localhost:5432/fund_analyzer"
    REDIS_URL: str = "redis://localhost:6379"
    DEBUG: bool = False
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
