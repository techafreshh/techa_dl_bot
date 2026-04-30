from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    TARGET_GROUP_ID: int
    TELEGRAM_API_URL: str = "http://telegram-bot-api:8081"

    # Required for Local Bot API server
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    DOWNLOAD_DIR: str = "/var/lib/telegram-bot-api/downloads"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
