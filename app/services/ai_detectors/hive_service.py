from __future__ import annotations

import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

HIVE_API_URL = "https://api.thehive.ai/api/v2/task/sync"


async def analyze_with_hive(
    image_bytes: bytes,
    mime_type: str,
    settings: Settings,
) -> dict:
    if not settings.hive_api_key:
        return {
            "provider": "hive",
            "detector_type": "ai_generated_image",
            "is_ai_generated": None,
            "score": None,
            "confidence": "low",
            "error": "HIVE_API_KEY가 설정되지 않았습니다.",
            "raw_response": None,
        }

    headers = {
        "Authorization": f"Token {settings.hive_api_key}",
        "Accept": "application/json",
    }

    ext = "jpg" if "jpeg" in mime_type else mime_type.split("/")[-1]
    filename = f"image.{ext}"

    try:
        async with httpx.AsyncClient(timeout=float(settings.request_timeout_seconds)) as client:
            response = await client.post(
                HIVE_API_URL,
                headers=headers,
                files={"image": (filename, image_bytes, mime_type)},
            )
            response.raise_for_status()
            data = response.json()
        logger.info(f"[Hive] 응답 수신: {str(data)[:500]}")
    except httpx.HTTPStatusError as exc:
        logger.error(f"[Hive] HTTP 오류: {exc.response.status_code} - {exc.response.text[:200]}")
        return {
            "provider": "hive",
            "detector_type": "ai_generated_image",
            "is_ai_generated": None,
            "score": None,
            "confidence": "low",
            "error": f"Hive API HTTP 오류: {exc.response.status_code}",
            "raw_response": None,
        }
    except Exception as exc:
        return {
            "provider": "hive",
            "detector_type": "ai_generated_image",
            "is_ai_generated": None,
            "score": None,
            "confidence": "low",
            "error": f"Hive API 호출 실패: {exc}",
            "raw_response": None,
        }

    # V3 응답 파싱: status[0].response.output[0].classes
    ai_score: float | None = None
    all_classes: list = []
    try:
        classes = data["status"][0]["response"]["output"][0]["classes"]
        all_classes = classes
        ai_class_names = {"ai_generated", "ai-generated", "ai_gen", "artificial", "generated"}
        for cls in classes:
            cls_name = str(cls.get("class", "")).lower()
            if cls_name in ai_class_names:
                ai_score = float(cls["score"])
                break
        if ai_score is None:
            not_real_names = {"not_real", "fake", "synthetic", "not_ai_generated"}
            for cls in classes:
                cls_name = str(cls.get("class", "")).lower()
                if cls_name in not_real_names:
                    ai_score = 1.0 - float(cls["score"])
                    break
    except (KeyError, IndexError, TypeError, ValueError):
        pass

    if ai_score is None:
        logger.warning(f"[Hive] 클래스 파싱 실패. 반환된 클래스: {[c.get('class') for c in all_classes[:10]]}")
        return {
            "provider": "hive",
            "detector_type": "ai_generated_image",
            "is_ai_generated": None,
            "score": None,
            "confidence": "low",
            "error": f"Hive 응답 파싱 실패. 클래스: {[c.get('class') for c in all_classes[:10]]}",
            "raw_response": data,
        }

    is_ai = ai_score >= 0.5
    confidence = "high" if ai_score >= 0.8 or ai_score <= 0.2 else ("medium" if ai_score >= 0.6 or ai_score <= 0.4 else "low")

    return {
        "provider": "hive",
        "detector_type": "ai_generated_image",
        "is_ai_generated": is_ai,
        "score": round(ai_score, 4),
        "confidence": confidence,
        "error": None,
        "raw_response": None,
    }
