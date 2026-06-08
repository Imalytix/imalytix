from app.services.model_normalizer import normalize_model_result


def test_normalizer_parses_and_clamps_bbox():
    raw = {
        "is_ai_generated": True,
        "score": 1.4,
        "confidence": "high",
        "evidence": [{"type": "anatomy", "label": "손", "severity": "high", "description": "이상"}],
        "suspicious_regions": [{"label": "손", "severity": "high", "description": "이상", "bbox": {"x1": 0, "y1": 0, "x2": 1.2, "y2": 0.5}}],
        "limitations": ["a"],
    }
    result = normalize_model_result(raw, "openai", "gpt-4.1-mini")
    assert result.score == 1.0
    assert result.suspicious_regions[0].bbox is None


def test_normalizer_fallback_on_bad_json_string():
    result = normalize_model_result("not json", "openai", "gpt-4.1-mini")
    assert result.is_ai_generated is None
    assert result.score == 0.5

