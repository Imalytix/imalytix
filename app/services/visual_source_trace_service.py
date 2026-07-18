from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from app.schemas.embedding import SimilarityHit
from app.schemas.source_trace import SourceMatch, VisualSourceTraceResult


def _extract_platform(source_url: str | None) -> str | None:
    if not source_url:
        return None
    try:
        parsed = urlparse(source_url)
    except Exception:
        return None
    host = (parsed.netloc or "").lower()
    if not host:
        return None
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def build_visual_source_trace(
    *,
    phash: str,
    embedding_hits: list[SimilarityHit],
    top_k: int = 5,
) -> VisualSourceTraceResult:
    if not embedding_hits:
        return VisualSourceTraceResult(enabled=True, notes=["비교 가능한 로컬 시각 인덱스가 아직 부족합니다."])

    top_matches = embedding_hits[:top_k]
    platforms: list[str] = []
    evidence: list[str] = []
    counter: Counter[str] = Counter()

    for hit in top_matches:
        platform = _extract_platform(hit.source_url)
        if platform:
            platforms.append(platform)
            counter[platform] += 1
        if hit.source_url:
            evidence.append(f"{hit.source_url}에서 유사 이미지가 발견되었습니다. similarity={hit.similarity:.2f}")
        elif hit.filename:
            evidence.append(f"{hit.filename}와 유사한 이미지가 로컬 저장소에서 발견되었습니다. similarity={hit.similarity:.2f}")

    confidence = "low"
    if len(top_matches) >= 3:
        confidence = "medium"
    if any(hit.similarity >= 0.95 for hit in top_matches):
        confidence = "high"

    return VisualSourceTraceResult(
        enabled=True,
        match_count=len(top_matches),
        top_matches=[
            SourceMatch(
                strategy=hit.strategy,
                phash=hit.phash,
                similarity=hit.similarity,
                source_url=hit.source_url,
                filename=hit.filename,
                category=hit.category,
                label=hit.label,
                mode=hit.mode,
                distance=hit.distance,
            )
            for hit in top_matches
        ],
        source_platforms=sorted([platform for platform, count in counter.items() if count > 0]),
        platform_reuse_detected=bool(top_matches),
        confidence=confidence,
        evidence=evidence[:10],
        notes=[
            "이미지 기반 출처 추적은 pHash + embedding 유사도 검색 결과를 바탕으로 추정합니다.",
            "원본 출처를 100% 단정하지 않으며, 재사용 흔적 후보를 보여주는 기능입니다.",
        ],
    )
