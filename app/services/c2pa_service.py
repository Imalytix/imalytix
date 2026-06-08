from __future__ import annotations


def analyze_c2pa(*args, **kwargs) -> dict:
    return {
        "c2pa_found": False,
        "signature_valid": False,
        "claim_generator": None,
        "ai_generated": False,
        "actions": [],
        "evidence": [],
    }

