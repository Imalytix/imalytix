from __future__ import annotations

from typing import Any

from app.schemas.model_result import EvidenceItem, SuspiciousRegion, VisionModelResult
from app.utils.bbox import normalize_bbox
from app.utils.json_parser import extract_json_object


def _clamp_score(score: Any) -> float:
    try:
        value = float(score)
    except Exception:
        value = 0.5
    return max(0.0, min(1.0, value))


def _normalize_evidence(items: Any) -> list[EvidenceItem]:
    normalized: list[EvidenceItem] = []
    if not isinstance(items, list):
        return normalized
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append(
            EvidenceItem(
                type=str(item.get("type", "other")),
                label=str(item.get("label", "")),
                severity=str(item.get("severity", "low")),
                description=str(item.get("description", "")),
            )
        )
    return normalized


def _normalize_regions(items: Any) -> list[SuspiciousRegion]:
    normalized: list[SuspiciousRegion] = []
    if not isinstance(items, list):
        return normalized
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append(
            SuspiciousRegion(
                label=str(item.get("label", "")),
                severity=str(item.get("severity", "low")),
                description=str(item.get("description", "")),
                bbox=normalize_bbox(item.get("bbox")),
            )
        )
    return normalized


def normalize_model_result(raw_result: dict[str, Any] | str | None, provider: str, model_name: str, is_mock: bool = False, error_message: str | None = None) -> VisionModelResult:
    parsed: dict[str, Any] | None = None
    raw_response: dict[str, Any] | str | None = raw_result

    if isinstance(raw_result, str):
        parsed = extract_json_object(raw_result)
    elif isinstance(raw_result, dict):
        parsed = raw_result

    if parsed is None:
        return VisionModelResult(
            provider=provider,
            model_name=model_name,
            is_ai_generated=None,
            score=0.5,
            confidence="low",
            evidence=[],
            suspicious_regions=[],
            limitations=["모델 응답 JSON 파싱에 실패했습니다."],
            raw_response=raw_response,
            is_mock=is_mock,
            error_message=error_message,
        )

    return VisionModelResult(
        provider=provider,
        model_name=model_name,
        is_ai_generated=parsed.get("is_ai_generated"),
        score=_clamp_score(parsed.get("score", 0.5)),
        confidence=str(parsed.get("confidence", "low")),
        evidence=_normalize_evidence(parsed.get("evidence")),
        suspicious_regions=_normalize_regions(parsed.get("suspicious_regions")),
        limitations=[str(item) for item in parsed.get("limitations", []) if item],
        raw_response=raw_response,
        is_mock=is_mock,
        error_message=error_message,
    )

