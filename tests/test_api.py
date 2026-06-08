from __future__ import annotations

import io

from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

from app.config import get_settings
from app.main import app

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
    assert "모의 응답" in payload["vision_results"][0]["limitations"][0]
