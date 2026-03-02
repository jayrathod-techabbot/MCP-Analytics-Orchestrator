from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    UPLOAD_DIR: Path = Path("uploads")
    CHARTS_DIR: Path = Path("outputs/charts")
    MAX_FILE_SIZE_MB: int = 50
    SANDBOX_TIMEOUT_SECONDS: int = 30
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
