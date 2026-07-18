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
from app.utils.json_parser import extract_json_object


async def analyze_with_claude(
    image_bytes: bytes,
    mime_type: str,
    prompt_type: str,
    settings: Settings,
) -> VisionModelResult:
    # If the API key is missing, keep the pipeline usable by returning
    # a deterministic mock result instead of failing the whole request.
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
            error_message="ANTHROPIC_API_KEY is not configured.",
        )

    try:
        import anthropic
    except Exception as exc:
        return normalize_model_result(
            None,
            provider="claude",
            model_name=settings.anthropic_vision_model,
            error_message=f"Failed to import anthropic SDK: {exc}",
        )

    # Match the prompt to the image style so Claude follows the same
    # analysis policy as the other vision providers.
    image_type = detect_image_type(image_bytes)
    prompt = build_prompt(prompt_type, image_type, provider="claude")

    # Claude receives image input as a base64 source block.
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    client = anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        timeout=float(settings.request_timeout_seconds),
    )

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

        # Keep the provider health counters and recent errors up to date.
        app_state.record_error("claude", f"API error: {exc}")
        return normalize_model_result(
            None,
            provider="claude",
            model_name=settings.anthropic_vision_model,
            error_message=f"Claude API request failed: {exc}",
        )

    # Claude usually returns a list of content blocks.
    # We read the first text block and then parse JSON from it.
    text = ""
    try:
        if getattr(response, "content", None):
            first_block = response.content[0]
            text = getattr(first_block, "text", "") or ""
    except Exception:
        text = ""

    if not text:
        from app.state import app_state

        app_state.record_error("claude", "Claude returned an empty response.")
        return normalize_model_result(
            None,
            provider="claude",
            model_name=settings.anthropic_vision_model,
            error_message="Claude returned an empty response.",
        )

    # The model is prompted to output JSON, but we still defensively extract
    # the first JSON object from any surrounding prose.
    parsed = extract_json_object(text)

    from app.state import app_state

    if parsed is not None:
        app_state.record_success("claude")
    else:
        app_state.record_error("claude", f"JSON parse failed: {text[:100]}")

    return normalize_model_result(
        parsed if parsed is not None else text,
        provider="claude",
        model_name=settings.anthropic_vision_model,
    )
