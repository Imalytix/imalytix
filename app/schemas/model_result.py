from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    type: str = "other"
    label: str = ""
    severity: str = "low"
    description: str = ""


class SuspiciousRegion(BaseModel):
    label: str = ""
    severity: str = "low"
    description: str = ""
    bbox: dict | None = None


class VisionModelResult(BaseModel):
    provider: str = "openai"
    model_name: str = ""
    is_ai_generated: bool | None = None
    score: float = 0.5
    confidence: str = "low"
    content_type: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    suspicious_regions: list[SuspiciousRegion] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    raw_response: dict | str | None = None
    is_mock: bool = False
    error_message: str | None = None


class DetectorResult(BaseModel):
    provider: str
    detector_type: str
    is_ai_generated: bool | None = None
    score: float | None = None
    confidence: str = "low"
    raw_response: dict | str | None = None

