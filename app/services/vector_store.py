from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.embedding_service import EmbeddingCandidate, cosine_similarity


@dataclass(slots=True)
class VectorRecord:
    phash: str
    strategy: str
    embedding: list[float]
    source_url: str | None = None
    filename: str | None = None
    category: str | None = None
    label: str | None = None
    mode: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EmbeddingVectorStore:
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
                CREATE TABLE IF NOT EXISTS image_embeddings (
                    phash TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    source_url TEXT,
                    filename TEXT,
                    category TEXT,
                    label TEXT,
                    mode TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (phash, strategy, mode)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_image_embeddings_strategy_updated
                ON image_embeddings(strategy, updated_at DESC)
                """
            )

    def save(
        self,
        *,
        phash: str,
        strategy: str,
        embedding: list[float],
        source_url: str | None = None,
        filename: str | None = None,
        category: str | None = None,
        label: str | None = None,
        mode: str | None = None,
    ) -> None:
        now = _utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO image_embeddings (
                    phash, strategy, embedding_json, source_url, filename, category, label, mode, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(phash, strategy, mode) DO UPDATE SET
                    embedding_json = excluded.embedding_json,
                    source_url = excluded.source_url,
                    filename = excluded.filename,
                    category = excluded.category,
                    label = excluded.label,
                    updated_at = excluded.updated_at
                """,
                (
                    phash,
                    strategy,
                    json.dumps(embedding),
                    source_url,
                    filename,
                    category,
                    label,
                    mode,
                    now,
                    now,
                ),
            )

    def count(self, strategy: str | None = None) -> int:
        query = "SELECT COUNT(*) AS count FROM image_embeddings"
        params: tuple[Any, ...] = ()
        if strategy:
            query += " WHERE strategy = ?"
            params = (strategy,)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row["count"] if row else 0)

    def search(
        self,
        *,
        phash: str,
        strategy: str,
        embedding: list[float],
        top_k: int = 5,
        exclude_phash: str | None = None,
    ) -> list[EmbeddingCandidate]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT phash, strategy, embedding_json, source_url, filename, category, label, mode
                FROM image_embeddings
                WHERE strategy = ?
                ORDER BY updated_at DESC
                """,
                (strategy,),
            ).fetchall()

        matches: list[EmbeddingCandidate] = []
        for row in rows:
            row_phash = str(row["phash"])
            if exclude_phash and row_phash == exclude_phash:
                continue
            try:
                stored_embedding = json.loads(row["embedding_json"])
            except Exception:
                continue
            similarity = cosine_similarity(embedding, stored_embedding)
            matches.append(
                EmbeddingCandidate(
                    phash=row_phash,
                    strategy=str(row["strategy"]),
                    similarity=round(similarity, 6),
                    source_url=row["source_url"],
                    filename=row["filename"],
                    category=row["category"],
                    label=row["label"],
                    mode=row["mode"],
                )
            )

        matches.sort(key=lambda item: item.similarity, reverse=True)
        return matches[:top_k]


@lru_cache(maxsize=4)
def get_embedding_store(db_path: str) -> EmbeddingVectorStore:
    return EmbeddingVectorStore(db_path)

