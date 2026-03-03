from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"

    # LangSmith tracing
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "ai-data-analyst-react-app"
    LANGCHAIN_TRACING_V2: str = "true"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    # Storage
    UPLOAD_DIR: Path = Path("uploads")
    CHARTS_DIR: Path = Path("outputs/charts")
    EXPORTS_DIR: Path = Path("outputs/exports")
    MAX_FILE_SIZE_MB: int = 50
    SANDBOX_TIMEOUT_SECONDS: int = 30
    PANDAS_QUERY_KERNEL_READY_TIMEOUT_SECONDS: int = 10
    PANDAS_QUERY_EXEC_TIMEOUT_SECONDS: int = 10
    PANDAS_QUERY_CACHE_TTL_SECONDS: int = 120
    PANDAS_QUERY_POOL_MAX_KERNELS: int = 4
    PANDAS_QUERY_IDLE_KERNEL_TTL_SECONDS: int = 300
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: Path = Path("logs/app.log")
    LOG_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
