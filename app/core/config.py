from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Portfolio Tracker"
    ENVIRONMENT: str = "development"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    # Security
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    
    # Alpaca (for stocks/ETFs)
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None
    
    # Gemini (for crypto)
    GEMINI_API_KEY: str
    GEMINI_API_SECRET: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            # Prioritize Doppler environment variables over local .env
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )

def get_settings() -> Settings:
    """
    Get settings from environment variables.
    Supports both Doppler and local .env file.
    """
    return Settings()

settings = get_settings() 