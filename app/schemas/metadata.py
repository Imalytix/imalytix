from __future__ import annotations

from pydantic import BaseModel, Field


class MetadataAnalysisResult(BaseModel):
    exif_found: bool = False
    png_metadata_found: bool = False
    c2pa_found: bool = False
    ai_tool_detected: bool = False
    detected_tools: list[str] = Field(default_factory=list)
    metadata_score: int = 0
    camera_make_model_found: bool = False
    evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict)

