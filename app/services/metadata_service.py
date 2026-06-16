from __future__ import annotations

import json
from typing import Any

from PIL import Image

from app.constants.ai_keywords import AI_SOFTWARE_KEYWORDS
from app.schemas.metadata import MetadataAnalysisResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    return str(value)


def analyze_metadata(
    image: Image.Image,
    source_url: str | None = None,
    filename: str | None = None,
    image_format: str | None = None,
) -> MetadataAnalysisResult:
    exif_found = False
    png_metadata_found = False
    ai_tool_detected = False
    detected_tools: list[str] = []
    evidence: list[str] = []
    limitations = ["메타데이터는 수정 가능하므로 단독 판정 근거로 사용하지 않습니다."]
    raw: dict[str, Any] = {}
    score = 0

    exif = {}
    try:
        exif_data = image.getexif() or {}
        for key, value in exif_data.items():
            exif[str(key)] = _to_text(value)
        if exif:
            exif_found = True
    except Exception:
        exif = {}

    software = ""
    make = ""
    model = ""
    lens_model = ""
    for key, value in exif.items():
        key_lower = key.lower()
        if "software" in key_lower:
            software = _to_text(value)
        elif "make" in key_lower:
            make = _to_text(value)
        elif "model" in key_lower:
            model = _to_text(value)
        elif "lens" in key_lower:
            lens_model = _to_text(value)

    if software:
        raw["software"] = software
        if any(keyword in software.lower() for keyword in AI_SOFTWARE_KEYWORDS):
            ai_tool_detected = True
            detected_tools.append(software)
            score += 35
            evidence.append(f"EXIF Software 태그에서 {software} 흔적이 확인되었습니다.")

    camera_fields = [make, model, lens_model]
    if make and model:
        raw["make"] = make
        raw["model"] = model
        score -= 10
        evidence.append("카메라 Make/Model 정보가 확인되어 실제 촬영 가능성을 반영했습니다.")
    if any(camera_fields):
        if lens_model:
            score -= 15
            evidence.append("LensModel 또는 촬영 정보가 확인되어 실제 카메라 촬영 흔적을 반영했습니다.")

    png_info = {}
    try:
        png_info = {k.lower(): _to_text(v) for k, v in (image.info or {}).items() if _to_text(v)}
        if (image_format or getattr(image, "format", "") or "").upper() == "PNG":
            png_metadata_found = True
        elif any(key in png_info for key in {"parameters", "prompt", "workflow", "negative_prompt"}):
            png_metadata_found = True
    except Exception:
        png_info = {}

    workflow_text = png_info.get("workflow", "")
    if "prompt" in png_info and png_info["prompt"].strip():
        score += 30
        evidence.append("PNG metadata에서 prompt 필드가 확인되었습니다.")
    if "parameters" in png_info and png_info["parameters"].strip():
        params = png_info["parameters"]
        if any(marker in params.lower() for marker in ["stable diffusion", "steps:", "sampler:", "cfg scale:", "seed:"]):
            score += 35
            ai_tool_detected = True
            detected_tools.append("Stable Diffusion")
            evidence.append("PNG parameters 필드에서 Stable Diffusion 생성 정보가 확인되었습니다.")
    if "workflow" in png_info and png_info["workflow"].strip():
        try:
            parsed = json.loads(png_info["workflow"])
            if isinstance(parsed, dict) or isinstance(parsed, list):
                score += 35
                ai_tool_detected = True
                detected_tools.append("ComfyUI")
                evidence.append("PNG workflow JSON에서 ComfyUI 흔적이 확인되었습니다.")
        except Exception:
            if workflow_text.strip():
                score += 20
                evidence.append("PNG workflow 필드가 존재합니다.")

    for key, value in png_info.items():
        if key in {"prompt", "negative_prompt", "workflow", "parameters", "seed", "sampler", "steps", "cfg scale", "model", "model hash"}:
            raw[key] = value

    if source_url:
        lower = source_url.lower()
        if any(keyword in lower for keyword in AI_SOFTWARE_KEYWORDS):
            score += 10
            evidence.append("이미지 URL 패턴에서 AI 생성 서비스 흔적이 확인되었습니다.")

    if not exif_found and not png_metadata_found:
        score += 10
        evidence.append("EXIF 및 PNG 메타데이터가 전혀 없습니다. AI 생성 이미지에서 흔히 나타나는 패턴입니다.")
        limitations.append("메타데이터 부재는 단독 근거로 충분하지 않으나 의심도를 높이는 요인입니다.")

    score = max(0, min(100, score))
    return MetadataAnalysisResult(
        exif_found=exif_found,
        png_metadata_found=png_metadata_found,
        c2pa_found=False,
        ai_tool_detected=ai_tool_detected,
        detected_tools=detected_tools,
        metadata_score=score,
        camera_make_model_found=bool(make and model),
        evidence=evidence,
        limitations=limitations,
        raw=raw,
    )
