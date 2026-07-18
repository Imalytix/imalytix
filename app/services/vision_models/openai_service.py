from __future__ import annotations

import base64

from app.config import Settings
from app.schemas.model_result import VisionModelResult
from app.services.model_normalizer import normalize_model_result
from app.services.vision_models.prompts import (
    build_mock_response,
    build_prompt,
    detect_image_type,
)
from app.utils.errors import OpenAIServiceError
from app.utils.json_parser import extract_json_object


async def analyze_with_openai(
    image_bytes: bytes,
    mime_type: str,
    prompt_type: str,
    settings: Settings,
) -> VisionModelResult:
    # Prototype mode: if the API key is missing, return a deterministic mock
    # response so the rest of the pipeline can still be exercised locally.
    if not settings.openai_api_key:
        if settings.mock_vision_fallback:
            return normalize_model_result(
                build_mock_response(prompt_type),
                provider="openai",
                model_name=settings.openai_vision_model,
                is_mock=True,
            )
        raise OpenAIServiceError("OPENAI_API_KEY가 설정되지 않았습니다.")

    try:
        from openai import AsyncOpenAI
    except Exception as exc:
        raise OpenAIServiceError("openai 패키지를 사용할 수 없습니다.") from exc

    # Choose a prompt variant that matches the image type.
    image_type = detect_image_type(image_bytes)
    prompt = build_prompt(prompt_type, image_type, provider="openai")

    # The OpenAI Responses API accepts image data as a base64 data URL.
    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=float(settings.request_timeout_seconds))
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{image_base64}"

    try:
        # Ask for a JSON-formatted forensic analysis.
        response = await client.responses.create(
            model=settings.openai_vision_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )
    except Exception as exc:
        # Record provider failures so they appear in the debug dashboard/logs.
        from app.state import app_state

        app_state.record_error("openai", f"API 호출 실패: {exc}")
        return normalize_model_result(
            None,
            provider="openai",
            model_name=settings.openai_vision_model,
            error_message=f"OpenAI API 호출 실패: {exc}",
        )

    # Some SDK responses expose `output_text`; others require manual traversal.
    text = getattr(response, "output_text", None) or ""
    if not text:
        try:
            for item in (response.output or []):
                for content in (getattr(item, "content", None) or []):
                    t = getattr(content, "text", None)
                    if t:
                        text = t
                        break
                if text:
                    break
        except Exception:
            pass
    if not text:
        from app.state import app_state

        app_state.record_error("openai", "응답 텍스트가 없습니다.")
        return normalize_model_result(
            None,
            provider="openai",
            model_name=settings.openai_vision_model,
            error_message="OpenAI 응답 텍스트가 없습니다.",
        )

    # Refusal patterns are handled as non-usable outputs.
    refusal_patterns = ["i'm sorry", "i cannot", "i can't", "i am unable", "as an ai", "sorry, i"]
    if any(p in text.lower() for p in refusal_patterns) and len(text) < 300:
        from app.state import app_state

        app_state.record_error("openai", f"콘텐츠 정책 거절: {text[:100]}")
        return normalize_model_result(
            None,
            provider="openai",
            model_name=settings.openai_vision_model,
            error_message="OpenAI가 요청을 분석할 수 없습니다. (콘텐츠 정책)",
        )

    # Extract the first JSON object from the raw text response.
    parsed = extract_json_object(text)
    from app.state import app_state

    if parsed is not None:
        app_state.record_success("openai")
    else:
        app_state.record_error("openai", f"JSON 파싱 실패: {text[:100]}")

    return normalize_model_result(
        parsed if parsed is not None else text,
        provider="openai",
        model_name=settings.openai_vision_model,
    )
