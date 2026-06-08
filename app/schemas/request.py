from __future__ import annotations

from pydantic import BaseModel, Field


class ImageUrlRequest(BaseModel):
    image_url: str = Field(..., min_length=1)
    mode: str = Field(default="standard")
    include_child_risk: bool = Field(default=True)
    return_bbox: bool = Field(default=True)


class AnalysisFormFields(BaseModel):
    mode: str = Field(default="standard")
    include_child_risk: bool = Field(default=True)
    return_bbox: bool = Field(default=True)

