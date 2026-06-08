from __future__ import annotations


def analyze_with_reality_defender(*args, **kwargs) -> dict:
    return {
        "provider": "reality_defender",
        "detector_type": "ai_generated_image",
        "is_ai_generated": None,
        "score": None,
        "confidence": "low",
        "raw_response": None,
    }

