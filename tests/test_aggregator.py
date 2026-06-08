from app.services.aggregator_service import aggregate_analysis, make_recommendation


def test_final_score_clamped_to_100():
    metadata = {"metadata_score": 100, "evidence": ["x"], "limitations": []}
    vision_results = [
        {
            "score": 1.0,
            "confidence": "high",
            "evidence": [{"severity": "high", "description": "x"}],
            "suspicious_regions": [],
            "limitations": [],
        }
    ]
    result = aggregate_analysis(metadata, [], vision_results, {"known_ai_cdn": True, "evidence": []})
    assert result["final_result"]["ai_probability"] == 100


def test_recommendation_text_changes_with_score():
    assert "출처 확인" in make_recommendation(85)
    assert "판단" in make_recommendation(45)

