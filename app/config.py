import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_TITLE: str = "CodeSage"
    API_VERSION: str = "1.0.0"
    
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    
    REDIS_HOST: str = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.environ.get("REDIS_PASSWORD", "")
    
    GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")
    GITHUB_WEBHOOK_SECRET: str = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    
    RATE_LIMIT: int = int(os.environ.get("RATE_LIMIT", 10))
    RATE_LIMIT_WINDOW: int = int(os.environ.get("RATE_LIMIT_WINDOW", 1))
    
    CACHE_TTL: int = int(os.environ.get("CACHE_TTL", 3600))
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
