from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ModelError:
    provider: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ModelStats:
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    last_success: str | None = None
    last_error: str | None = None
    last_error_message: str | None = None


class AppState:
    def __init__(self):
        self.errors: deque[ModelError] = deque(maxlen=50)
        self.stats: dict[str, ModelStats] = {
            "openai": ModelStats(),
            "gemini": ModelStats(),
            "claude": ModelStats(),
        }

    def record_success(self, provider: str):
        s = self.stats.setdefault(provider, ModelStats())
        s.total_requests += 1
        s.success_count += 1
        s.last_success = datetime.now(timezone.utc).isoformat()

    def record_error(self, provider: str, message: str):
        s = self.stats.setdefault(provider, ModelStats())
        s.total_requests += 1
        s.error_count += 1
        s.last_error = datetime.now(timezone.utc).isoformat()
        s.last_error_message = message
        self.errors.appendleft(ModelError(provider=provider, message=message))

    def get_recent_errors(self, limit: int = 20) -> list[dict]:
        return [
            {"provider": e.provider, "message": e.message, "timestamp": e.timestamp}
            for e in list(self.errors)[:limit]
        ]

    def get_stats(self) -> dict:
        return {
            provider: {
                "total_requests": s.total_requests,
                "success_count": s.success_count,
                "error_count": s.error_count,
                "success_rate": round(s.success_count / s.total_requests * 100) if s.total_requests else None,
                "last_success": s.last_success,
                "last_error": s.last_error,
                "last_error_message": s.last_error_message,
            }
            for provider, s in self.stats.items()
        }


app_state = AppState()
