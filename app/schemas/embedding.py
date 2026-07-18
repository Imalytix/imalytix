from __future__ import annotations

from pydantic import BaseModel, Field


class SimilarityHit(BaseModel):
    strategy: str = ""
    similarity: float = 0.0
    phash: str = ""
    source_url: str | None = None
    filename: str | None = None
    category: str | None = None
    label: str | None = None
    mode: str | None = None
    distance: float | None = None


class EmbeddingAnalysisResult(BaseModel):
    enabled: bool = False
    strategies: list[str] = Field(default_factory=list)
    top_hits: list[SimilarityHit] = Field(default_factory=list)
    best_similarity: float = 0.0
    best_strategy: str | None = None
    notes: list[str] = Field(default_factory=list)
