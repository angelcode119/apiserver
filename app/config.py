from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import Optional, List, Dict, Any
import json

class Settings(BaseSettings):

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "parental_control"

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8765
    DEBUG: bool = True

    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    TELEGRAM_2FA_BOT_TOKEN: Optional[str] = "2FA_BOT_TOKEN_HERE"
    TELEGRAM_2FA_CHAT_ID: Optional[str] = "-1002FA_CHAT_ID"

    TELEGRAM_ENABLED: bool = True

    ADMIN_BOT1_TOKEN: Optional[str] = "ADMIN_BOT1_TOKEN_HERE"
    ADMIN_BOT1_CHAT_ID: str = "-1001ADMIN1_CHATID"

    ADMIN_BOT2_TOKEN: Optional[str] = "ADMIN_BOT2_TOKEN_HERE"
    ADMIN_BOT2_CHAT_ID: str = "-1002ADMIN2_CHATID"

    ADMIN_BOT3_TOKEN: Optional[str] = "ADMIN_BOT3_TOKEN_HERE"
    ADMIN_BOT3_CHAT_ID: str = "-1003ADMIN3_CHATID"

    ADMIN_BOT4_TOKEN: Optional[str] = "ADMIN_BOT4_TOKEN_HERE"
    ADMIN_BOT4_CHAT_ID: str = "-1004ADMIN4_CHATID"

    ADMIN_BOT5_TOKEN: Optional[str] = "ADMIN_BOT5_TOKEN_HERE"
    ADMIN_BOT5_CHAT_ID: str = "-1005ADMIN5_CHATID"

    TELEGRAM_BOTS: List[Dict[str, Any]] = []

    @field_validator('TELEGRAM_BOTS', mode='before')
    @classmethod
    def parse_telegram_bots(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except:
                return []
        return v or []

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