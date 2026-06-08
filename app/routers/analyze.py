from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import Settings, get_settings
from app.schemas.request import ImageUrlRequest
from app.services.analysis_service import analyze_image_from_url, analyze_uploaded_file

router = APIRouter(tags=["analyze"])


def _normalize_mode(mode: str | None) -> str:
    value = (mode or "standard").strip().lower()
    if value not in {"quick", "standard", "deep"}:
        return "standard"
    return value


@router.post("/analyze/image")
async def analyze_image(
    file: UploadFile | None = File(None),
    mode: str = Form("standard"),
    include_child_risk: bool = Form(True),
    return_bbox: bool = Form(True),
    settings: Settings = Depends(get_settings),
):
    return await analyze_uploaded_file(
        file=file,
        mode=_normalize_mode(mode),
        include_child_risk=include_child_risk,
        return_bbox=return_bbox,
        settings=settings,
    )


@router.post("/analyze/image-url")
async def analyze_image_url(
    request: ImageUrlRequest,
    settings: Settings = Depends(get_settings),
):
    return await analyze_image_from_url(
        image_url=request.image_url,
        mode=_normalize_mode(request.mode),
        include_child_risk=request.include_child_risk,
        return_bbox=request.return_bbox,
        settings=settings,
    )
