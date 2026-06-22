from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, UploadFile

from app.config import Settings
from app.schemas.response import AnalysisResponse, FinalResult, InputInfo
from app.services.aggregator_service import aggregate_analysis
from app.services.image_downloader import download_image_from_url
from app.services.image_loader import validate_image_bytes
from app.services.image_preprocess import preprocess_image
from app.services.metadata_service import analyze_metadata
from app.services.phash_service import generate_phash
from app.services.router_policy import decide_routing, has_strong_metadata_evidence
from app.services.source_pattern_service import analyze_source_patterns
from app.services.vision_models.claude_service import analyze_with_claude
from app.services.vision_models.gemini_service import analyze_with_gemini
from app.services.ai_detectors.hive_service import analyze_with_hive
from app.services.vision_models.openai_service import analyze_with_openai
from app.utils.errors import ImageValidationError, SecurityViolationError


def make_request_id() -> str:
    return f"req_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def _strip_bbox(regions: list[dict], return_bbox: bool) -> list[dict]:
    if return_bbox:
        return regions
    stripped: list[dict] = []
    for region in regions:
        if isinstance(region, dict):
            copied = dict(region)
            copied["bbox"] = None
            stripped.append(copied)
        else:
            stripped.append(region)
    return stripped


def build_final_response(
    *,
    request_id: str,
    mode: str,
    input_type: str,
    loaded_image: Any,
    phash: str,
    metadata_result,
    detector_results: list[dict],
    vision_results: list[dict],
    source_result: dict | None,
    aggregate_result: dict,
    return_bbox: bool,
) -> AnalysisResponse:
    final_result = aggregate_result["final_result"]
    vision_results = [
        {
            **result,
            "suspicious_regions": _strip_bbox(
                [dict(item) if isinstance(item, dict) else item for item in result.get("suspicious_regions", [])],
                return_bbox,
            ),
        }
        for result in vision_results
    ]

    return AnalysisResponse(
        product="Imalytix",
        request_id=request_id,
        mode=mode,
        input=InputInfo(
            type=input_type,
            mime_type=loaded_image.mime_type,
            width=loaded_image.width,
            height=loaded_image.height,
            phash=phash,
        ),
        final_result=FinalResult(
            is_ai_generated=final_result["is_ai_generated"],
            ai_probability=final_result["ai_probability"],
            label=final_result["label"],
            confidence=final_result["confidence"],
        ),
        metadata_analysis=metadata_result,
        detector_results=detector_results,
        vision_results=vision_results,
        evidence_summary=aggregate_result["evidence_summary"],
        suspicious_regions=_strip_bbox(
            [dict(item) if isinstance(item, dict) else item for item in aggregate_result["suspicious_regions"]],
            return_bbox,
        ),
        limitations=[
            "AI 생성 여부는 100% 단정할 수 없습니다.",
            "SNS를 거친 이미지는 메타데이터가 제거되었을 수 있습니다.",
            "메타데이터는 수정 가능하므로 단독 판정 근거로 사용하지 않습니다.",
            *aggregate_result["limitations"],
        ],
        recommended_action=aggregate_result["recommended_action"],
    )


async def analyze_image_bytes(
    *,
    image_bytes: bytes,
    mode: str,
    include_child_risk: bool,
    return_bbox: bool,
    source_url: str | None,
    filename: str | None,
    settings: Settings,
    input_type: str,
) -> AnalysisResponse:
    try:
        loaded = validate_image_bytes(image_bytes, filename=filename)
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    normalized_image, normalized_bytes, _ = preprocess_image(loaded.image, settings)
    phash = generate_phash(normalized_image)
    metadata_result = analyze_metadata(
        loaded.image,
        source_url=source_url,
        filename=filename,
        image_format=loaded.format_name,
    )
    source_result = analyze_source_patterns(source_url)

    routing = decide_routing(
        mode,
        metadata_result.model_dump(),
        cache_hit=False,
        has_openai_key=bool(settings.openai_api_key),
        has_gemini_key=bool(settings.gemini_api_key),
        has_claude_key=bool(settings.anthropic_api_key),
        has_hive_key=bool(settings.hive_api_key),
    )
    detector_results: list[dict] = []
    vision_results: list[dict] = []

    if routing.get("call_hive"):
        hive_result = await analyze_with_hive(
            image_bytes=normalized_bytes,
            mime_type="image/jpeg",
            settings=settings,
        )
        detector_results.append(hive_result)

    if routing.get("call_openai"):
        vision_result = await analyze_with_openai(
            image_bytes=normalized_bytes,
            mime_type="image/jpeg",
            prompt_type=routing["prompt_type"],
            settings=settings,
        )
        vision_results.append(vision_result.model_dump())

    if routing.get("call_gemini"):
        gemini_result = await analyze_with_gemini(
            image_bytes=normalized_bytes,
            mime_type="image/jpeg",
            prompt_type=routing["prompt_type"],
            settings=settings,
        )
        vision_results.append(gemini_result.model_dump())

    if routing.get("call_claude"):
        claude_result = await analyze_with_claude(
            image_bytes=normalized_bytes,
            mime_type="image/jpeg",
            prompt_type=routing["prompt_type"],
            settings=settings,
        )
        vision_results.append(claude_result.model_dump())

    aggregate_result = aggregate_analysis(
        metadata_result=metadata_result.model_dump(),
        detector_results=detector_results,
        vision_results=vision_results,
        source_result=source_result,
    )

    return build_final_response(
        request_id=make_request_id(),
        mode=mode,
        input_type=input_type,
        loaded_image=loaded,
        phash=phash,
        metadata_result=metadata_result,
        detector_results=detector_results,
        vision_results=vision_results,
        source_result=source_result,
        aggregate_result=aggregate_result,
        return_bbox=return_bbox,
    )


async def analyze_uploaded_file(
    file: UploadFile | None,
    mode: str,
    include_child_risk: bool,
    return_bbox: bool,
    settings: Settings,
) -> AnalysisResponse:
    if not file:
        raise HTTPException(status_code=400, detail="file이 필요합니다.")

    image_bytes = await file.read()
    if len(image_bytes) > settings.max_file_size_bytes:
        raise HTTPException(status_code=400, detail="이미지 파일이 너무 큽니다.")

    return await analyze_image_bytes(
        image_bytes=image_bytes,
        mode=mode,
        include_child_risk=include_child_risk,
        return_bbox=return_bbox,
        source_url=None,
        filename=file.filename,
        settings=settings,
        input_type="file_upload",
    )


async def analyze_image_from_url(
    image_url: str,
    mode: str,
    include_child_risk: bool,
    return_bbox: bool,
    settings: Settings,
) -> AnalysisResponse:
    try:
        downloaded = await download_image_from_url(image_url, settings)
    except SecurityViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return await analyze_image_bytes(
        image_bytes=downloaded.loaded.image_bytes,
        mode=mode,
        include_child_risk=include_child_risk,
        return_bbox=return_bbox,
        source_url=downloaded.source_url,
        filename=None,
        settings=settings,
        input_type="image_url",
    )
