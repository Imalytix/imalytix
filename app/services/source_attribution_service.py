from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import urlparse

from app.schemas.source_attribution import SourceAttributionResult


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
    "runway",
    "krea",
    "recraft",
)

RISKY_TOKENS = (
    "repost",
    "reupload",
    "screenshot",
    "download",
    "mirror",
    "copy",
    "edited",
    "generated",
    "ai",
)

TRUSTED_TOKENS = (
    "raw",
    "original",
    "official",
    "press",
    "editorial",
)


def _tokenize(value: str | None) -> list[str]:
    if not value:
        return []
    normalized = value.replace("-", " ").replace("_", " ").replace(".", " ")
    return [token for token in normalized.lower().split() if token]


def analyze_source_attribution(source_url: str | None, filename: str | None = None) -> SourceAttributionResult:
    if not source_url and not filename:
        return SourceAttributionResult(source_type="unknown", confidence="low", notes=["출처 정보가 없습니다."])

    evidence: list[str] = []
    risky_patterns: list[str] = []
    notes: list[str] = []
    path_tokens: list[str] = []
    filename_tokens: list[str] = _tokenize(filename)

    domain = None
    source_type = "unknown"
    trusted_source = False
    known_ai_service = False

    if source_url:
        parsed = urlparse(source_url)
        domain = parsed.netloc.lower() or None
        path_tokens = _tokenize(PurePosixPath(parsed.path).name or parsed.path)
        combined = " ".join([domain or "", parsed.path.lower(), filename.lower() if filename else ""])
        known_ai_service = any(pattern in combined for pattern in KNOWN_AI_PATTERNS)
        if known_ai_service:
            source_type = "ai_service"
            evidence.append("URL 또는 경로에서 AI 서비스 관련 패턴이 확인되었습니다.")

        if parsed.scheme in {"http", "https"} and domain:
            if any(token in combined for token in TRUSTED_TOKENS) and not known_ai_service:
                trusted_source = True
                source_type = "publisher"
                evidence.append("공식/원본 계열로 보이는 출처 단서가 있습니다.")

        if any(token in combined for token in RISKY_TOKENS):
            risky_patterns.extend([token for token in RISKY_TOKENS if token in combined])
            evidence.append("URL 또는 파일명에 재업로드/편집 가능성을 시사하는 단서가 있습니다.")

    if filename and not filename_tokens:
        notes.append("파일명 해석이 불가능합니다.")

    confidence = "low"
    if known_ai_service or trusted_source:
        confidence = "medium"
    if known_ai_service and risky_patterns:
        confidence = "high"

    return SourceAttributionResult(
        source_url=source_url,
        source_type=source_type,
        domain=domain,
        path_tokens=path_tokens,
        filename_tokens=filename_tokens,
        known_ai_service=known_ai_service,
        trusted_source=trusted_source,
        risky_patterns=list(dict.fromkeys(risky_patterns)),
        evidence=evidence,
        confidence=confidence,
        notes=notes,
    )

