from __future__ import annotations

import base64
import time

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.state import app_state

router = APIRouter(tags=["health"])

# 1x1 픽셀 PNG (검증된 최소 이미지)
_TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
_TINY_PNG_BYTES = base64.b64decode(_TINY_PNG_B64)
_TINY_MIME = "image/png"


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "imalytix-api"}


@router.get("/health/models")
async def model_status(settings: Settings = Depends(get_settings)) -> dict:
    """각 모델의 API 키 설정 여부 및 누적 통계 반환"""
    stats = app_state.get_stats()
    return {
        "openai": {
            "configured": bool(settings.openai_api_key),
            "model": settings.openai_vision_model,
            **stats.get("openai", {}),
        },
        "gemini": {
            "configured": bool(settings.gemini_api_key),
            "model": settings.gemini_vision_model,
            **stats.get("gemini", {}),
        },
        "claude": {
            "configured": bool(settings.anthropic_api_key),
            "model": settings.anthropic_vision_model,
            **stats.get("claude", {}),
        },
    }


@router.post("/health/test/{provider}")
async def test_model(provider: str, settings: Settings = Depends(get_settings)) -> dict:
    """특정 모델에 최소 테스트 요청을 보내 실제 연결 여부 확인"""
    if provider not in ("openai", "gemini", "claude"):
        return {"provider": provider, "status": "error", "message": "알 수 없는 프로바이더"}

    start = time.perf_counter()

    try:
        if provider == "openai":
            result = await _test_openai(settings)
        elif provider == "gemini":
            result = await _test_gemini(settings)
        else:
            result = await _test_claude(settings)
    except Exception as exc:
        elapsed = round((time.perf_counter() - start) * 1000)
        return {"provider": provider, "status": "error", "message": str(exc), "latency_ms": elapsed}

    elapsed = round((time.perf_counter() - start) * 1000)
    result["latency_ms"] = elapsed
    return result


async def _test_openai(settings: Settings) -> dict:
    if not settings.openai_api_key:
        return {"provider": "openai", "status": "not_configured", "message": "API 키 없음"}
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=15.0)
        data_url = f"data:{_TINY_MIME};base64,{_TINY_PNG_B64}"
        resp = await client.responses.create(
            model=settings.openai_vision_model,
            input=[{"role": "user", "content": [
                {"type": "input_text", "text": "이 이미지가 AI 생성인지 답하라. JSON: {\"ok\": true}"},
                {"type": "input_image", "image_url": data_url},
            ]}],
        )
        text = getattr(resp, "output_text", "") or ""
        return {"provider": "openai", "status": "ok", "message": f"응답 수신 ({len(text)}자)"}
    except Exception as exc:
        return {"provider": "openai", "status": "error", "message": str(exc)}


async def _test_gemini(settings: Settings) -> dict:
    if not settings.gemini_api_key:
        return {"provider": "gemini", "status": "not_configured", "message": "API 키 없음"}
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.gemini_api_key)
        image_part = types.Part.from_bytes(data=_TINY_PNG_BYTES, mime_type=_TINY_MIME)
        resp = await client.aio.models.generate_content(
            model=settings.gemini_vision_model,
            contents=["OK라고만 답하라.", image_part],
            config=types.GenerateContentConfig(
                max_output_tokens=10,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        text = resp.text or ""
        return {"provider": "gemini", "status": "ok", "message": f"응답 수신 ({len(text)}자)"}
    except Exception as exc:
        msg = str(exc)
        status = "quota_exceeded" if "429" in msg or "EXHAUSTED" in msg else "error"
        return {"provider": "gemini", "status": status, "message": msg[:200]}


async def _test_claude(settings: Settings) -> dict:
    if not settings.anthropic_api_key:
        return {"provider": "claude", "status": "not_configured", "message": "API 키 없음"}
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        resp = await client.messages.create(
            model=settings.anthropic_vision_model,
            max_tokens=10,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": _TINY_MIME, "data": _TINY_PNG_B64}},
                {"type": "text", "text": "OK라고만 답하라."},
            ]}],
        )
        text = resp.content[0].text if resp.content else ""
        return {"provider": "claude", "status": "ok", "message": f"응답 수신 ({len(text)}자)"}
    except Exception as exc:
        return {"provider": "claude", "status": "error", "message": str(exc)[:200]}


@router.get("/health/errors")
async def recent_errors() -> dict:
    """최근 에러 로그 반환"""
    return {"errors": app_state.get_recent_errors(20)}
