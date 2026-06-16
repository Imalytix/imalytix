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


async def analyze_with_claude(
    image_bytes: bytes,
    mime_type: str,
    prompt_type: str,
    settings: Settings,
) -> VisionModelResult:
    if not settings.anthropic_api_key:
        if settings.mock_vision_fallback:
            return normalize_model_result(
                build_mock_response(prompt_type),
                provider="claude",
                model_name=settings.anthropic_vision_model,
                is_mock=True,
            )
        return normalize_model_result(
            None,
            provider="claude",
            model_name=settings.anthropic_vision_model,
            error_message="ANTHROPIC_API_KEY가 설정되지 않았습니다.",
        )

    try:
        import anthropic
    except Exception as exc:
        return normalize_model_result(
            None,
            provider="claude",
            model_name=settings.anthropic_vision_model,
            error_message=f"anthropic 패키지를 사용할 수 없습니다: {exc}",
        )

    image_type = detect_image_type(image_bytes)
    prompt = build_prompt(prompt_type, image_type)
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        response = await client.messages.create(
            model=settings.anthropic_vision_model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": image_base64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
    except Exception as exc:
        from app.state import app_state
        app_state.record_error("claude", str(exc)[:200])
        return normalize_model_result(
            None,
            provider="claude",
            model_name=settings.anthropic_vision_model,
            error_message=f"Claude API 호출 실패: {exc}",
        )

    text = ""
    try:
        text = response.content[0].text if response.content else ""
    except Exception:
        pass

    if not text:
        return normalize_model_result(
            None,
            provider="claude",
            model_name=settings.anthropic_vision_model,
            error_message="Claude 응답이 비어 있습니다.",
        )

    parsed = extract_json_object(text)
    from app.state import app_state
    if parsed is not None:
        app_state.record_success("claude")
    else:
        app_state.record_error("claude", f"JSON 파싱 실패: {text[:100]}")
    return normalize_model_result(
        parsed if parsed is not None else text,
        provider="claude",
        model_name=settings.anthropic_vision_model,
    )
