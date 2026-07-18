from __future__ import annotations

import io

from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

from app.config import get_settings
from app.main import app
from app.schemas.model_result import EvidenceItem, SuspiciousRegion, VisionModelResult
from app.services import analysis_service

client = TestClient(app)


def make_image_bytes() -> bytes:
    img = Image.new("RGB", (32, 32), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_png_with_metadata() -> bytes:
    img = Image.new("RGB", (32, 32), color="blue")
    info = PngImagePlugin.PngInfo()
    info.add_text("parameters", "prompt: a cat\nSteps: 20\nSampler: Euler\nCFG scale: 7\nSeed: 1234")
    buf = io.BytesIO()
    img.save(buf, format="PNG", pnginfo=info)
    return buf.getvalue()


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "imalytix-api"}


def test_health_usage():
    response = client.get("/api/v1/health/usage")
    assert response.status_code == 200
    payload = response.json()
    assert "providers" in payload
    assert {item["provider"] for item in payload["providers"]} == {"openai", "gemini", "claude"}


def test_analyze_image_rejects_missing_file():
    response = client.post("/api/v1/analyze/image")
    assert response.status_code in {400, 422}


def test_analyze_image_url_rejects_ssrf():
    response = client.post(
        "/api/v1/analyze/image-url",
        json={"image_url": "http://127.0.0.1/image.jpg", "mode": "standard", "include_child_risk": True, "return_bbox": True},
    )
    assert response.status_code == 400


def test_analyze_image_quick_mode_with_strong_metadata_skips_openai():
    files = {"file": ("sample.png", make_png_with_metadata(), "image/png")}
    data = {"mode": "quick", "include_child_risk": "true", "return_bbox": "true"}
    response = client.post("/api/v1/analyze/image", files=files, data=data)
    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata_analysis"]["ai_tool_detected"] is True
    assert payload["metadata_analysis"]["metadata_score"] >= 35


def test_analyze_image_uses_mock_vision_when_enabled(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "mock_vision_fallback", True)

    files = {"file": ("sample.jpg", make_image_bytes(), "image/jpeg")}
    data = {"mode": "standard", "include_child_risk": "true", "return_bbox": "true"}
    response = client.post("/api/v1/analyze/image", files=files, data=data)
    assert response.status_code == 200
    payload = response.json()
    assert payload["vision_results"]
    assert payload["vision_results"][0]["limitations"]


def test_analyze_image_uses_phash_cache_on_repeat_requests(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    monkeypatch.setattr(settings, "phash_cache_enabled", True)
    monkeypatch.setattr(settings, "phash_db_path", str(tmp_path / "cache.sqlite3"))
    monkeypatch.setattr(settings, "phash_similarity_threshold", 0)

    async def fake_openai(*args, **kwargs):
        return VisionModelResult(
            provider="openai",
            model_name="gpt-4.1-mini",
            is_ai_generated=True,
            score=0.91,
            confidence="high",
            evidence=[
                EvidenceItem(
                    type="texture",
                    label="반복 패턴",
                    severity="high",
                    description="배경 패턴이 지나치게 균질합니다.",
                )
            ],
            suspicious_regions=[
                SuspiciousRegion(
                    label="배경",
                    severity="medium",
                    description="배경의 반복 텍스처가 의심됩니다.",
                    bbox={"x1": 0.1, "y1": 0.1, "x2": 0.4, "y2": 0.4},
                )
            ],
            limitations=["고해상도 원본이 아니면 판단이 달라질 수 있습니다."],
        )

    monkeypatch.setattr(analysis_service, "decide_routing", lambda *args, **kwargs: {"call_openai": True, "call_gemini": False, "call_claude": False, "prompt_type": "standard"})
    monkeypatch.setattr(analysis_service, "analyze_with_openai", fake_openai)

    files = {"file": ("sample.jpg", make_image_bytes(), "image/jpeg")}
    data = {"mode": "standard", "include_child_risk": "true", "return_bbox": "true"}
    first = client.post("/api/v1/analyze/image", files=files, data=data)
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["cache_info"]["hit"] is False

    async def should_not_run(*args, **kwargs):
        raise AssertionError("cached request should not call model")

    monkeypatch.setattr(analysis_service, "analyze_with_openai", should_not_run)
    second = client.post("/api/v1/analyze/image", files=files, data=data)
    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["cache_info"]["hit"] is True
    assert second_payload["cache_info"]["distance"] == 0
