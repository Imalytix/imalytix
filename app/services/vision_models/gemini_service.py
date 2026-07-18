from __future__ import annotations

import base64

from app.config import Settings
from app.schemas.model_result import VisionModelResult
from app.services.model_normalizer import normalize_model_result
from app.utils.json_parser import extract_json_object
from app.services.vision_models.prompts import (
    build_mock_response,
    build_prompt,
    detect_image_type,
)


async def analyze_with_gemini(
    image_bytes: bytes,
    mime_type: str,
    prompt_type: str,
    settings: Settings,
) -> VisionModelResult:
    # Prototype fallback when Gemini credentials are not configured.
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
        # Import lazily so the package is only required when Gemini is used.
        import importlib

        genai = importlib.import_module("google.genai")
        genai_types = importlib.import_module("google.genai.types")
    except Exception as exc:
        return normalize_model_result(
            None,
            provider="gemini",
            model_name=settings.gemini_vision_model,
            error_message=f"google-genai 패키지를 사용할 수 없습니다: {exc}",
        )

    # Select prompt style according to the detected image type.
    image_type = detect_image_type(image_bytes)
    prompt = build_prompt(prompt_type, image_type, provider="gemini")

    client = genai.Client(api_key=settings.gemini_api_key)

    try:
        # Gemini accepts the prompt text plus a binary image part.
        image_part = genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = await client.aio.models.generate_content(
            model=settings.gemini_vision_model,
            contents=[prompt, image_part],
            config=genai_types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2048,
                thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
            ),
        )
    except Exception as exc:
        from app.state import app_state

        app_state.record_error("gemini", str(exc)[:200])
        return normalize_model_result(
            None,
            provider="gemini",
            model_name=settings.gemini_vision_model,
            error_message=f"Gemini API 호출 실패: {exc}",
        )

    # Most Gemini responses expose plain text directly.
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
            error_message="Gemini 응답 텍스트가 없습니다.",
        )

    # Parse the first JSON object from the model output.
    parsed = extract_json_object(text)
    from app.state import app_state

    if parsed is not None:
        app_state.record_success("gemini")
    else:
        app_state.record_error("gemini", f"JSON 파싱 실패: {text[:100]}")

    return normalize_model_result(
        parsed if parsed is not None else text,
        provider="gemini",
        model_name=settings.gemini_vision_model,
    )
