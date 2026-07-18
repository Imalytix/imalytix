"""
분석 이벤트 트래킹 서비스.

사용자 이미지 원본은 저장하지 않는다. pHash(역추적 불가)와
분석 결과 텍스트만 수집한다.

수집 항목:
  - phash          : 퍼셉추얼 해시 (이미지 고유 ID, 원본 복원 불가)
  - 이미지 메타데이터 : 크기·해상도·파일 유형 (원본 없이 통계 분석용)
  - 분석 결과       : AI 확률, 레이블, 사용된 모델 목록
  - 처리 시간       : 성능 모니터링용
  - 소스 유형       : file_upload / image_url (사용 패턴 파악)
  - 캐시 여부       : 중복 요청 비율 측정

저장하지 않는 항목:
  - 이미지 바이트 / 픽셀 데이터
  - URL, 파일명 (개인정보 포함 가능)
  - IP 주소, 쿠키, 사용자 식별자
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from app.utils.logger import get_logger

logger = get_logger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS analysis_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    request_id          TEXT    NOT NULL,

    -- 이미지 지문 (역추적 불가)
    phash               TEXT    NOT NULL,

    -- 이미지 메타데이터
    file_size_bytes     INTEGER,
    width               INTEGER,
    height              INTEGER,
    mime_type           TEXT,

    -- 분석 결과
    ai_probability      REAL,
    final_label         TEXT,
    confidence          TEXT,
    is_ai_generated     INTEGER,   -- 0 / 1 / NULL

    -- 소스
    input_type          TEXT,      -- file_upload | image_url
    source_type         TEXT,      -- unknown | social | trusted | ai_service

    -- 모델 호출 정보
    mode                TEXT,
    vision_models       TEXT,      -- JSON 배열: ["openai","gemini","claude"]
    metadata_ai_flag    INTEGER,   -- 0 / 1

    -- 성능
    total_ms            REAL,
    cache_hit           INTEGER    -- 0 / 1
);

CREATE INDEX IF NOT EXISTS idx_events_created  ON analysis_events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_phash    ON analysis_events(phash);
CREATE INDEX IF NOT EXISTS idx_events_label    ON analysis_events(final_label);
"""

_STATS_SQL = """
SELECT
    COUNT(*)                                  AS total_events,
    SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END)  AS cache_hits,
    ROUND(AVG(ai_probability) * 100, 1)       AS avg_ai_prob_pct,
    ROUND(AVG(total_ms), 0)                   AS avg_total_ms,
    SUM(CASE WHEN is_ai_generated = 1 THEN 1 ELSE 0 END) AS ai_detected,
    SUM(CASE WHEN is_ai_generated = 0 THEN 1 ELSE 0 END) AS real_detected,
    MAX(created_at)                           AS last_event_at
FROM analysis_events
"""

_LABEL_DIST_SQL = """
SELECT final_label, COUNT(*) AS cnt
FROM analysis_events
GROUP BY final_label
ORDER BY cnt DESC
"""

_RECENT_SQL = """
SELECT request_id, created_at, final_label, ai_probability, total_ms
FROM analysis_events
ORDER BY id DESC
LIMIT ?
"""


class TrackingService:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._loop: asyncio.AbstractEventLoop | None = None
        self._initialized = False

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        try:
            conn.executescript(_CREATE_TABLE_SQL)
            conn.commit()
        finally:
            conn.close()
        self._initialized = True

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self._db_path, timeout=5, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _insert_sync(self, row: dict[str, Any]) -> None:
        if not self._initialized:
            self._init_db()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO analysis_events (
                    request_id, phash,
                    file_size_bytes, width, height, mime_type,
                    ai_probability, final_label, confidence, is_ai_generated,
                    input_type, source_type,
                    mode, vision_models, metadata_ai_flag,
                    total_ms, cache_hit
                ) VALUES (
                    :request_id, :phash,
                    :file_size_bytes, :width, :height, :mime_type,
                    :ai_probability, :final_label, :confidence, :is_ai_generated,
                    :input_type, :source_type,
                    :mode, :vision_models, :metadata_ai_flag,
                    :total_ms, :cache_hit
                )
                """,
                row,
            )

    async def record(self, row: dict[str, Any]) -> None:
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._insert_sync, row)
        except Exception as exc:
            logger.warning("tracking_write_failed: %s", exc)

    def get_stats(self) -> dict[str, Any]:
        if not self._initialized:
            self._init_db()
        with self._connection() as conn:
            stats = dict(conn.execute(_STATS_SQL).fetchone() or {})
            label_rows = conn.execute(_LABEL_DIST_SQL).fetchall()
            stats["label_distribution"] = {row["final_label"]: row["cnt"] for row in label_rows}
            recent_rows = conn.execute(_RECENT_SQL, (10,)).fetchall()
            stats["recent_events"] = [dict(r) for r in recent_rows]
        return stats


@lru_cache(maxsize=1)
def _get_service(db_path: str) -> TrackingService:
    svc = TrackingService(db_path)
    svc._init_db()
    return svc


def get_tracking_service(db_path: str = "data/tracking.sqlite3") -> TrackingService:
    return _get_service(db_path)


async def track_analysis_event(
    *,
    request_id: str,
    phash: str,
    file_size_bytes: int | None,
    width: int | None,
    height: int | None,
    mime_type: str | None,
    ai_probability: float | None,
    final_label: str | None,
    confidence: str | None,
    is_ai_generated: bool | None,
    input_type: str,
    source_type: str | None,
    mode: str,
    vision_models: list[str],
    metadata_ai_flag: bool,
    total_ms: float,
    cache_hit: bool,
    db_path: str = "data/tracking.sqlite3",
) -> None:
    svc = get_tracking_service(db_path)
    row: dict[str, Any] = {
        "request_id": request_id,
        "phash": phash,
        "file_size_bytes": file_size_bytes,
        "width": width,
        "height": height,
        "mime_type": mime_type,
        "ai_probability": ai_probability,
        "final_label": final_label,
        "confidence": confidence,
        "is_ai_generated": None if is_ai_generated is None else int(is_ai_generated),
        "input_type": input_type,
        "source_type": source_type,
        "mode": mode,
        "vision_models": json.dumps(vision_models, ensure_ascii=False),
        "metadata_ai_flag": int(metadata_ai_flag),
        "total_ms": total_ms,
        "cache_hit": int(cache_hit),
    }
    await svc.record(row)
