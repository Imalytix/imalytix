from __future__ import annotations

from pydantic import BaseModel, Field


class SourceAttributionResult(BaseModel):
    source_url: str | None = None
    source_type: str = "unknown"
    domain: str | None = None
    path_tokens: list[str] = Field(default_factory=list)
    filename_tokens: list[str] = Field(default_factory=list)
    known_ai_service: bool = False
    trusted_source: bool = False
    risky_patterns: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: str = "low"
    notes: list[str] = Field(default_factory=list)
