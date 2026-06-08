from __future__ import annotations

import base64

from app.config import Settings
from app.schemas.model_result import VisionModelResult
from app.services.model_normalizer import normalize_model_result
from app.utils.json_parser import extract_json_object
from app.services.vision_models.openai_service import (
    detect_image_type,
    build_prompt,
    build_mock_response,
)

# Gemini용 프롬프트는 OpenAI 프롬프트와 동일한 내용을 재사용


async def analyze_with_gemini(
    image_bytes: bytes,
    mime_type: str,
    prompt_type: str,
    settings: Settings,
) -> VisionModelResult:
    if not settings.gemini_api_key:
        if settings.mock_vision_fallback:
            return normalize_model_result(
                build_mock_response(prompt_type),
                provider="gemini",
                model_name=settings.gemini_vision_model,
                is_mock=True,
            )
        return normalize_model_result(
            None,
            provider="gemini",
            model_name=settings.gemini_vision_model,
            error_message="GEMINI_API_KEY가 설정되지 않았습니다.",
        )

    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        return normalize_model_result(
            None,
            provider="gemini",
            model_name=settings.gemini_vision_model,
            error_message=f"google-genai 패키지를 사용할 수 없습니다: {exc}",
        )

    image_type = detect_image_type(image_bytes)
    prompt = build_prompt(prompt_type, image_type)

    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = await client.aio.models.generate_content(
            model=settings.gemini_vision_model,
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1024,
            ),
        )
    except Exception as exc:
        return normalize_model_result(
            None,
            provider="gemini",
            model_name=settings.gemini_vision_model,
            error_message=f"Gemini API 호출 실패: {exc}",
        )

    text = ""
    try:
        text = response.text or ""
    except Exception:
        pass

    if not text:
        return normalize_model_result(
            None,
            provider="gemini",
            model_name=settings.gemini_vision_model,
            error_message="Gemini 응답이 비어 있습니다.",
        )

    parsed = extract_json_object(text)
    return normalize_model_result(
        parsed if parsed is not None else text,
        provider="gemini",
        model_name=settings.gemini_vision_model,
    )
