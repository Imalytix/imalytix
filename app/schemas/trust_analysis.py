from __future__ import annotations

from pydantic import BaseModel, Field


class RiskSignal(BaseModel):
    name: str = ""
    score: int = 0
    description: str = ""


class TrustAnalysisResult(BaseModel):
    theft_risk_score: int = 0
    forgery_risk_score: int = 0
    combined_risk_score: int = 0
    trust_score: int = 100
    label: str = "신뢰 가능"
    confidence: str = "low"
    evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    signals: list[RiskSignal] = Field(default_factory=list)
    source_attribution: dict | None = None
    source_trace: dict | None = None
    embedding_analysis: dict | None = None
