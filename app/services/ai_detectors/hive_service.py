from __future__ import annotations


def analyze_with_hive(*args, **kwargs) -> dict:
    return {
        "provider": "hive",
        "detector_type": "ai_generated_image",
        "is_ai_generated": None,
        "score": None,
        "confidence": "low",
        "raw_response": None,
    }

