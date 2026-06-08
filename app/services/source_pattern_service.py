from __future__ import annotations

KNOWN_AI_PATTERNS = (
    "midjourney",
    "openai",
    "chatgpt",
    "firefly",
    "sora",
    "leonardo",
    "ideogram",
    "stability.ai",
    "stablediffusion",
    "dreamstudio",
    "playground",
    "discordapp",
)


def analyze_source_patterns(source_url: str | None) -> dict:
    if not source_url:
        return {"known_ai_cdn": False, "trusted_source": False, "evidence": []}

    lower = source_url.lower()
    evidence = []
    known_ai_cdn = any(pattern in lower for pattern in KNOWN_AI_PATTERNS)
    if known_ai_cdn:
        evidence.append("URL 패턴에서 AI 생성 서비스 흔적이 확인되었습니다.")

    return {
        "known_ai_cdn": known_ai_cdn,
        "trusted_source": False,
        "evidence": evidence,
    }

