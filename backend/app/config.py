"""Configuration settings for the application"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "SMC Backtesting Platform"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:4001",  # Vite dev server
        "http://localhost:5173",
        "http://127.0.0.1:4001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # Data
    DATA_DIR: Path = Path(__file__).parent.parent.parent / "LT1" / "data" / "forex"
    CACHE_SIZE: int = 100  # Number of dataframes to cache
    
    # API
    API_PREFIX: str = "/api"
    
    class Config:
        case_sensitive = True


settings = Settings()
