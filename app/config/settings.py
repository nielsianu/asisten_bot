import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_users_raw: str = Field(default="", validation_alias="TELEGRAM_ALLOWED_USERS")

    # 9Router AI Gateway
    ninerouter_api_key: str = Field(default="", validation_alias="NINEROUTER_API_KEY")
    ninerouter_base_url: str = Field(default="https://api.9router.com/v1", validation_alias="NINEROUTER_BASE_URL")
    ninerouter_model: str = Field(default="gpt-4o-mini", validation_alias="NINEROUTER_MODEL")

    # Google Sheets
    google_sheet_id: str = Field(default="", validation_alias="GOOGLE_SHEET_ID")
    google_credentials_file: str = Field(default="credentials.json", validation_alias="GOOGLE_CREDENTIALS_FILE")

    # Database & System
    database_path: str = Field(default="data/app.db", validation_alias="DATABASE_PATH")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @property
    def allowed_users(self) -> List[str]:
        """Parse TELEGRAM_ALLOWED_USERS string into a cleaned list of allowed user IDs/usernames."""
        if not self.telegram_allowed_users_raw:
            return []
        raw_list = [u.strip() for u in self.telegram_allowed_users_raw.split(",") if u.strip()]
        cleaned = []
        for item in raw_list:
            cleaned.append(item.lstrip("@").lower())
        return cleaned


# Global settings instance
settings = Settings()
