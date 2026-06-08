from __future__ import annotations


def has_strong_metadata_evidence(metadata_result: dict) -> bool:
    score = int(metadata_result.get("metadata_score", 0) or 0)
    if score >= 35:
        return True
    if metadata_result.get("ai_tool_detected"):
        return True
    evidence = metadata_result.get("evidence") or []
    return any("Stable Diffusion" in str(item) or "ComfyUI" in str(item) or "EXIF Software" in str(item) for item in evidence)


def decide_routing(
    mode: str,
    metadata_result: dict,
    cache_hit: bool = False,
    has_openai_key: bool = True,
    has_gemini_key: bool = False,
    has_claude_key: bool = False,
) -> dict:
    if cache_hit:
        return {
            "call_openai": False,
            "call_claude": False,
            "call_gemini": False,
            "call_hive": False,
            "call_sightengine": False,
            "prompt_type": "quick",
            "use_cache": True,
        }

    prompt_type = "standard"
    if mode == "quick":
        prompt_type = "quick"
        if has_strong_metadata_evidence(metadata_result):
            return {
                "call_openai": False,
                "call_claude": False,
                "call_gemini": False,
                "call_hive": False,
                "call_sightengine": False,
                "prompt_type": prompt_type,
                "use_cache": False,
            }
    elif mode == "deep":
        prompt_type = "standard"

    return {
        "call_openai": has_openai_key,
        "call_claude": has_claude_key,
        "call_gemini": has_gemini_key,
        "call_hive": False,
        "call_sightengine": False,
        "prompt_type": prompt_type,
        "use_cache": False,
    }
