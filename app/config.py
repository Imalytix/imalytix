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
    max_file_size_mb: int = Field(default=10, alias="MAX_FILE_SIZE_MB")
    image_long_side: int = Field(default=1024, alias="IMAGE_LONG_SIDE")
    request_timeout_seconds: int = Field(default=60, alias="REQUEST_TIMEOUT_SECONDS")
    app_env: Literal["local", "dev", "staging", "prod"] = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: str = Field(default="logs", alias="LOG_DIR")
    log_file: str = Field(default="logs/imalytix.log", alias="LOG_FILE")
    analysis_log_file: str = Field(default="logs/analysis.log", alias="ANALYSIS_LOG_FILE")
    log_max_bytes: int = Field(default=5 * 1024 * 1024, alias="LOG_MAX_BYTES")
    log_backup_count: int = Field(default=5, alias="LOG_BACKUP_COUNT")
    analysis_slow_threshold_ms: int = Field(default=3000, alias="ANALYSIS_SLOW_THRESHOLD_MS")
    mock_vision_fallback: bool = Field(default=False, alias="MOCK_VISION_FALLBACK")
    phash_cache_enabled: bool = Field(default=True, alias="PHASH_CACHE_ENABLED")
    phash_db_path: str = Field(default="data/phash_cache.sqlite3", alias="PHASH_DB_PATH")
    phash_similarity_threshold: int = Field(default=6, alias="PHASH_SIMILARITY_THRESHOLD")
    embedding_store_enabled: bool = Field(default=True, alias="EMBEDDING_STORE_ENABLED")
    embedding_db_path: str = Field(default="data/embedding_store.sqlite3", alias="EMBEDDING_DB_PATH")
    embedding_top_k: int = Field(default=5, alias="EMBEDDING_TOP_K")

    # ── 실제 DINOv2 / OpenCLIP 임베딩 모델 설정 (Phase B) ───────────
    # NOTE: 아래 두 모델은 최초 호출 시 HuggingFace/OpenCLIP 허브에서
    #       가중치를 내려받는다(수백 MB 단위 네트워크 비용 발생).
    #       팀 합의 없이 배포 환경에서 자동 다운로드가 실행되지 않도록
    #       `embedding_model_backend`로 실모델/레거시를 명시적으로 스위치한다.
    embedding_model_backend: Literal["real", "legacy"] = Field(
        default="legacy", alias="EMBEDDING_MODEL_BACKEND"
    )
    dinov2_model_name: str = Field(
        default="facebook/dinov2-small", alias="DINOV2_MODEL_NAME"
    )  # ViT-S/14, 384dim
    clip_model_name: str = Field(default="ViT-B-32", alias="CLIP_MODEL_NAME")
    clip_pretrained_tag: str = Field(default="openai", alias="CLIP_PRETRAINED_TAG")
    embedding_device: Literal["cpu", "cuda"] = Field(default="cpu", alias="EMBEDDING_DEVICE")

    # ── 임베딩 → 3-LLM 라우팅 게이팅 (Phase B, 기본 OFF) ────────────
    # true로 켜면, pHash/embedding 유사도가 이미 알려진 이미지와
    # 매우 높은 확신으로 일치할 때 quick 모드에서 LLM 호출을 생략한다.
    # 비용 절감 목적이며, 잘못된 라벨이 그대로 재사용될 위험이 있으므로
    # 기본값은 비활성화(false)로 두고 팀 검토 후 켠다.
    embedding_routing_shortcut_enabled: bool = Field(
        default=False, alias="EMBEDDING_ROUTING_SHORTCUT_ENABLED"
    )
    embedding_strong_similarity_threshold: float = Field(
        default=0.97, alias="EMBEDDING_STRONG_SIMILARITY_THRESHOLD"
    )

    tracking_enabled: bool = Field(default=True, alias="TRACKING_ENABLED")
    tracking_db_path: str = Field(default="data/tracking.sqlite3", alias="TRACKING_DB_PATH")

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
