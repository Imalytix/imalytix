from __future__ import annotations


def analyze_with_sightengine(*args, **kwargs) -> dict:
    return {
        "provider": "sightengine",
        "detector_type": "ai_generated_image",
        "is_ai_generated": None,
        "score": None,
        "confidence": "low",
        "raw_response": None,
    }

