from __future__ import annotations

from pydantic import BaseModel, Field


class SourceMatch(BaseModel):
    strategy: str = ""
    phash: str = ""
    similarity: float = 0.0
    source_url: str | None = None
    filename: str | None = None
    category: str | None = None
    label: str | None = None
    mode: str | None = None
    distance: float | None = None


class VisualSourceTraceResult(BaseModel):
    enabled: bool = False
    match_count: int = 0
    top_matches: list[SourceMatch] = Field(default_factory=list)
    source_platforms: list[str] = Field(default_factory=list)
    platform_reuse_detected: bool = False
    confidence: str = "low"
    evidence: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
