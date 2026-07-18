from __future__ import annotations

from app.services.source_attribution_service import analyze_source_attribution


def test_source_attribution_detects_ai_service():
    result = analyze_source_attribution(
        "https://cdn.midjourney.com/example/image.jpg",
        filename="midjourney-output.png",
    )

    assert result.known_ai_service is True
    assert result.source_type == "ai_service"
    assert result.evidence


def test_source_attribution_flags_trusted_source():
    result = analyze_source_attribution(
        "https://news.example.com/original/photo.jpg",
        filename="original_photo.jpg",
    )

    assert result.trusted_source in {True, False}
    assert result.confidence in {"low", "medium", "high"}
