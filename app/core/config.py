from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "AstroNova Admin"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/astronova"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production-make-it-very-long-and-random"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Shopify
    SHOPIFY_SHOP_URL: str = ""  # e.g., "your-store.myshopify.com"
    SHOPIFY_ACCESS_TOKEN: str = ""  # Admin API access token
    SHOPIFY_API_VERSION: str = "2024-01"
    
    # TimeZoneDB API (for timezone calculation)
    TIMEZONEDB_API_KEY: str = ""  # Get free key from https://timezonedb.com/

    # OpenAI
    OPENAI_API_KEY: str = ""  # ChatGPT API key

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
