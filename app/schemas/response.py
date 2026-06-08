from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.metadata import MetadataAnalysisResult
from app.schemas.model_result import DetectorResult, SuspiciousRegion, VisionModelResult


class InputInfo(BaseModel):
    type: str
    mime_type: str
    width: int
    height: int
    phash: str


class FinalResult(BaseModel):
    is_ai_generated: bool | None = None
    ai_probability: int = 0
    label: str = ""
    confidence: str = "low"


class AnalysisResponse(BaseModel):
    product: str = "Imalytix"
    request_id: str
    mode: str
    input: InputInfo
    final_result: FinalResult
    metadata_analysis: MetadataAnalysisResult
    detector_results: list[DetectorResult] = Field(default_factory=list)
    vision_results: list[VisionModelResult] = Field(default_factory=list)
    evidence_summary: list[str] = Field(default_factory=list)
    suspicious_regions: list[SuspiciousRegion] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    recommended_action: str = ""

