from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List

class Settings(BaseSettings):

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "parental_control"

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8765
    DEBUG: bool = True

    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # 2FA Bot Configuration (shared for all admins)
    TELEGRAM_2FA_BOT_TOKEN: Optional[str] = "2FA_BOT_TOKEN_HERE"
    TELEGRAM_2FA_CHAT_ID: Optional[str] = "-1002FA_CHAT_ID"
    
    TELEGRAM_ENABLED: bool = True

    PING_INTERVAL: int = 30
    CONNECTION_TIMEOUT: int = 60
    MAX_MESSAGE_SIZE: int = 10 * 1024 * 1024

    SMS_RETENTION_DAYS: int = 180
    LOGS_RETENTION_DAYS: int = 30
    ADMIN_ACTIVITY_RETENTION_DAYS: int = 90

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )

settings = Settings()
