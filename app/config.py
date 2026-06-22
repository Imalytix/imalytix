from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_vision_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_VISION_MODEL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_vision_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_VISION_MODEL")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_vision_model: str = Field(default="claude-haiku-4-5-20251001", alias="ANTHROPIC_VISION_MODEL")
    hive_api_key: str | None = Field(default=None, alias="HIVE_API_KEY")
    max_file_size_mb: int = Field(default=10, alias="MAX_FILE_SIZE_MB")
    image_long_side: int = Field(default=1024, alias="IMAGE_LONG_SIDE")
    request_timeout_seconds: int = Field(default=60, alias="REQUEST_TIMEOUT_SECONDS")
    app_env: Literal["local", "dev", "staging", "prod"] = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    mock_vision_fallback: bool = Field(default=False, alias="MOCK_VISION_FALLBACK")
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ALLOWED_ORIGINS",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
