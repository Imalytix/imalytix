from PIL import Image

from app.services.aggregator_service import aggregate_analysis
from app.services.metadata_service import analyze_metadata


def test_metadata_detects_stable_diffusion_from_png_parameters():
    image = Image.new("RGB", (64, 64), color="white")
    image.info = {"parameters": "prompt: a cat\nSteps: 20\nSampler: Euler\nCFG scale: 7\nSeed: 1234\nModel hash: abc"}

    result = analyze_metadata(image)
    assert result.ai_tool_detected is True
    assert result.metadata_score >= 35
    assert any("Stable Diffusion" in item for item in result.evidence)


def test_metadata_without_signals_does_not_force_ai():
    image = Image.new("RGB", (64, 64), color="white")
    result = analyze_metadata(image)
    assert result.metadata_score == 0
    assert result.ai_tool_detected is False


def test_aggregator_caps_visual_score():
    metadata = {"metadata_score": 0, "evidence": [], "limitations": []}
    vision_results = [
        {
            "score": 0.9,
            "confidence": "high",
            "evidence": [
                {"severity": "high", "description": "a"},
                {"severity": "high", "description": "b"},
                {"severity": "high", "description": "c"},
                {"severity": "high", "description": "d"},
            ],
            "suspicious_regions": [],
            "limitations": [],
        }
    ]
    result = aggregate_analysis(metadata, [], vision_results)
    assert 0 <= result["final_result"]["ai_probability"] <= 100
    assert result["final_result"]["ai_probability"] >= 15
