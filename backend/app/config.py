"""Configuration settings for the application"""
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables at the module level for Settings
load_dotenv()

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
    DATA_DIR: Path = Path(__file__).parent.parent.parent / "archive" / "charts" / "forex"
    CACHE_SIZE: int = 100  # Number of dataframes to cache
    
    # Database
    DB_URL: str = "sqlite:///./data/smc_trading.db"

    # API
    API_PREFIX: str = "/api"

    # cTrader Credentials
    CTRADER_CLIENT_ID: str
    CTRADER_CLIENT_SECRET: str
    CTRADER_ACCOUNT_ID: int
    CTRADER_ACCESS_TOKEN: str
    
    # Telegram Credentials
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    
    class Config:
        case_sensitive = True
        env_file = ".env" # Load environment variables from .env file relative to the current working directory (backend)


settings = Settings()
