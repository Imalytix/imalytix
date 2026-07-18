from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PHashCacheMatch:
    phash: str
    mode: str
    distance: int
    similarity: float
    response_json: str
    created_at: str | None = None
    updated_at: str | None = None

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.response_json)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_phash(phash: str) -> str:
    return "".join(ch for ch in phash.lower().strip() if ch in "0123456789abcdef")


def hamming_distance_hex(left: str, right: str) -> int:
    a = _normalize_phash(left)
    b = _normalize_phash(right)
    if not a or not b:
        return 64

    width = max(len(a), len(b))
    a_int = int(a.zfill(width), 16)
    b_int = int(b.zfill(width), 16)
    return (a_int ^ b_int).bit_count()


class PHashAnalysisStore:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS phash_analysis_cache (
                    phash TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (phash, mode)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_phash_analysis_mode_updated
                ON phash_analysis_cache(mode, updated_at DESC)
                """
            )

    def save(self, *, phash: str, mode: str, response: dict[str, Any]) -> None:
        payload = json.dumps(response, ensure_ascii=False)
        now = _utc_now()
        normalized_phash = _normalize_phash(phash)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO phash_analysis_cache (phash, mode, response_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(phash, mode) DO UPDATE SET
                    response_json = excluded.response_json,
                    updated_at = excluded.updated_at
                """,
                (normalized_phash, mode, payload, now, now),
            )

    def find_best_match(self, *, phash: str, mode: str, max_distance: int = 0) -> PHashCacheMatch | None:
        normalized_phash = _normalize_phash(phash)
        if not normalized_phash:
            return None

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT phash, mode, response_json, created_at, updated_at
                FROM phash_analysis_cache
                WHERE mode = ?
                ORDER BY updated_at DESC
                """,
                (mode,),
            ).fetchall()

        best: PHashCacheMatch | None = None
        for row in rows:
            distance = hamming_distance_hex(normalized_phash, row["phash"])
            if distance > max_distance:
                continue
            similarity = 1.0 - (distance / 64.0)
            candidate = PHashCacheMatch(
                phash=row["phash"],
                mode=row["mode"],
                distance=distance,
                similarity=round(similarity, 4),
                response_json=row["response_json"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            if best is None or candidate.distance < best.distance or (
                candidate.distance == best.distance and candidate.updated_at > best.updated_at
            ):
                best = candidate
                if distance == 0:
                    break

        return best

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM phash_analysis_cache").fetchone()
        return int(row["count"] if row else 0)

    def count_exact(self, *, phash: str, mode: str | None = None) -> int:
        normalized_phash = _normalize_phash(phash)
        if not normalized_phash:
            return 0

        query = "SELECT COUNT(*) AS count FROM phash_analysis_cache WHERE phash = ?"
        params: tuple[Any, ...]
        if mode:
            query += " AND mode = ?"
            params = (normalized_phash, mode)
        else:
            params = (normalized_phash,)

        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row["count"] if row else 0)

    def has_phash(self, *, phash: str, mode: str | None = None) -> bool:
        return self.count_exact(phash=phash, mode=mode) > 0


@lru_cache(maxsize=8)
def get_phash_store(db_path: str) -> PHashAnalysisStore:
    return PHashAnalysisStore(db_path)
