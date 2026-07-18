from __future__ import annotations

from typing import Any

from app.schemas.trust_analysis import RiskSignal, TrustAnalysisResult
from app.services.phash_store import PHashAnalysisStore


THEFT_KEYWORDS = (
    "repost",
    "reupload",
    "copy",
    "duplicate",
    "screenshot",
    "mirror",
    "scrape",
    "download",
    "share",
    "crop",
    "resized",
)


def _to_text(value: Any) -> str:
    return "" if value is None else str(value)


def _extract_strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_to_text(v) for v in values if _to_text(v)]


def analyze_image_theft_risk(
    *,
    phash: str,
    mode: str,
    source_url: str | None,
    filename: str | None,
    metadata_result: dict,
    source_result: dict | None,
    source_attribution: dict | None,
    source_trace: dict | None,
    embedding_analysis: dict | None,
    phash_store: PHashAnalysisStore | None,
) -> tuple[int, list[str], list[RiskSignal]]:
    evidence: list[str] = []
    signals: list[RiskSignal] = []
    score = 0

    exact_count = phash_store.count_exact(phash=phash, mode=mode) if phash_store else 0
    if exact_count > 0:
        duplicate_bonus = min(40, 15 + (exact_count - 1) * 10)
        score += duplicate_bonus
        evidence.append(f"동일 pHash 이미지가 {exact_count}건 존재합니다. 재사용 가능성이 높습니다.")
        signals.append(
            RiskSignal(
                name="pHash 중복",
                score=duplicate_bonus,
                description="같은 이미지 또는 거의 같은 이미지가 반복 분석되었습니다.",
            )
        )

    if phash_store:
        similar_match = phash_store.find_best_match(phash=phash, mode=mode, max_distance=6)
        if similar_match and similar_match.distance > 0:
            similarity_bonus = max(6, 22 - (similar_match.distance * 2))
            score += similarity_bonus
            evidence.append(
                f"유사 pHash 이미지가 발견되었습니다. distance={similar_match.distance}, similarity={similar_match.similarity:.2f}"
            )
            signals.append(
                RiskSignal(
                    name="pHash 유사",
                    score=similarity_bonus,
                    description="리사이즈, 크롭, 약한 편집된 재사용 이미지일 수 있습니다.",
                )
            )

    if source_result and source_result.get("known_ai_cdn"):
        score += 15
        evidence.append("이미지 출처 URL에서 AI 생성 서비스 패턴이 감지되었습니다.")
        signals.append(
            RiskSignal(
                name="출처 패턴",
                score=15,
                description="출처 URL이 AI 생성/공유 서비스와 연관되어 보입니다.",
            )
        )

    if source_attribution:
        if source_attribution.get("known_ai_service"):
            score += 12
            evidence.extend(_extract_strings(source_attribution.get("evidence", [])))
            signals.append(
                RiskSignal(
                    name="출처 귀속",
                    score=12,
                    description="파일명 또는 URL이 AI 서비스 흐름과 연결됩니다.",
                )
            )
        if source_attribution.get("trusted_source"):
            score = max(0, score - 5)
            evidence.extend(_extract_strings(source_attribution.get("evidence", [])))

    joined = " ".join(
        [
            _to_text(source_url),
            _to_text(filename),
            " ".join(_extract_strings(metadata_result.get("evidence", []))),
        ]
    ).lower()
    if any(keyword in joined for keyword in THEFT_KEYWORDS):
        score += 10
        evidence.append("파일명 또는 출처 문자열에 재업로드/복사/편집 신호가 있습니다.")
        signals.append(
            RiskSignal(
                name="복제/재업로드",
                score=10,
                description="파일명 또는 URL에 재사용 흔적이 있습니다.",
            )
        )

    if metadata_result.get("camera_make_model_found"):
        score = max(0, score - 5)
        evidence.append("카메라 Make/Model 정보가 있어 원본 촬영 이미지일 가능성을 일부 반영했습니다.")

    if embedding_analysis:
        best_similarity = float(embedding_analysis.get("best_similarity") or 0.0)
        top_hits = embedding_analysis.get("top_hits") or []
        if best_similarity >= 0.96:
            bonus = 20
        elif best_similarity >= 0.92:
            bonus = 15
        elif best_similarity >= 0.88:
            bonus = 10
        else:
            bonus = 0
        if bonus and top_hits:
            score += bonus
            top_hit = top_hits[0]
            evidence.append(
                f"embedding 유사도 검색에서 유사 후보를 확인했습니다. strategy={top_hit.get('strategy')}, similarity={best_similarity:.2f}"
            )
            signals.append(
                RiskSignal(
                    name="embedding 유사도",
                    score=bonus,
                    description="크롭/리사이즈/재압축된 재업로드를 탐지하는 신호입니다.",
                )
            )

    if source_trace:
        match_count = int(source_trace.get("match_count") or 0)
        if match_count > 0:
            reuse_bonus = min(18, 6 + match_count * 3)
            score += reuse_bonus
            evidence.extend(_extract_strings(source_trace.get("evidence", [])))
            signals.append(
                RiskSignal(
                    name="이미지 기반 출처 추적",
                    score=reuse_bonus,
                    description="유사 이미지가 다른 저장소/플랫폼에 존재하는 흔적이 관찰되었습니다.",
                )
            )

    score = max(0, min(100, score))
    return score, evidence, signals


def analyze_image_forgery_risk(
    *,
    metadata_result: dict,
    detector_results: list[dict],
    vision_results: list[dict],
    source_result: dict | None,
    source_attribution: dict | None,
) -> tuple[int, list[str], list[RiskSignal]]:
    evidence: list[str] = []
    signals: list[RiskSignal] = []
    score = 0

    if metadata_result.get("ai_tool_detected"):
        score += 35
        evidence.extend(_extract_strings(metadata_result.get("evidence", [])))
        signals.append(
            RiskSignal(
                name="생성형 메타데이터",
                score=35,
                description="EXIF 또는 PNG metadata에서 AI 생성 도구 흔적이 확인되었습니다.",
            )
        )

    detector_scores = [float(r.get("score")) for r in detector_results if r.get("score") is not None]
    if detector_scores:
        detector_score = round((sum(detector_scores) / len(detector_scores)) * 25)
        score += detector_score
        evidence.append("전용 AI 탐지 API 결과가 생성 가능성을 지지합니다.")
        signals.append(
            RiskSignal(
                name="전용 탐지기",
                score=detector_score,
                description="전용 AI 이미지 탐지기의 평균 점수를 반영했습니다.",
            )
        )

    vision_scores: list[float] = []
    visual_evidence_score = 0
    for result in vision_results:
        raw_score = result.get("score")
        if raw_score is not None:
            try:
                vision_scores.append(max(0.0, min(1.0, float(raw_score))))
            except Exception:
                vision_scores.append(0.5)

        for item in result.get("evidence", []):
            if isinstance(item, dict):
                desc = item.get("description")
                if desc:
                    evidence.append(str(desc))
                severity = str(item.get("severity", "low"))
                if severity == "high":
                    visual_evidence_score += 5
                elif severity == "medium":
                    visual_evidence_score += 3
                else:
                    visual_evidence_score += 1

    if vision_scores:
        model_score = round((sum(vision_scores) / len(vision_scores)) * 30)
        score += model_score
        signals.append(
            RiskSignal(
                name="Vision 모델",
                score=model_score,
                description="시각적 이상 징후에 대한 모델 신뢰도를 반영했습니다.",
            )
        )

    visual_evidence_score = min(15, visual_evidence_score)
    if visual_evidence_score:
        score += visual_evidence_score
        signals.append(
            RiskSignal(
                name="시각적 근거",
                score=visual_evidence_score,
                description="손상, 반복 패턴, 조명 불일치 같은 시각적 근거를 반영했습니다.",
            )
        )

    if source_result and source_result.get("known_ai_cdn"):
        score += 10
        evidence.append("출처 URL 자체가 생성형 플랫폼과 연결될 수 있습니다.")

    if source_attribution and source_attribution.get("known_ai_service"):
        score += 10
        evidence.extend(_extract_strings(source_attribution.get("evidence", [])))

    score = max(0, min(100, score))
    return score, evidence, signals


def build_trust_analysis(
    *,
    phash: str,
    mode: str,
    source_url: str | None,
    filename: str | None,
    metadata_result: dict,
    detector_results: list[dict],
    vision_results: list[dict],
    source_result: dict | None,
    source_attribution: dict | None = None,
    source_trace: dict | None = None,
    embedding_analysis: dict | None = None,
    phash_store: PHashAnalysisStore | None,
) -> TrustAnalysisResult:
    theft_risk, theft_evidence, theft_signals = analyze_image_theft_risk(
        phash=phash,
        mode=mode,
        source_url=source_url,
        filename=filename,
        metadata_result=metadata_result,
        source_result=source_result,
        source_attribution=source_attribution,
        source_trace=source_trace,
        embedding_analysis=embedding_analysis,
        phash_store=phash_store,
    )
    forgery_risk, forgery_evidence, forgery_signals = analyze_image_forgery_risk(
        metadata_result=metadata_result,
        detector_results=detector_results,
        vision_results=vision_results,
        source_result=source_result,
        source_attribution=source_attribution,
    )

    combined_risk = round((theft_risk * 0.4) + (forgery_risk * 0.6))
    trust_score = max(0, min(100, 100 - combined_risk))

    if trust_score >= 80:
        label = "신뢰 가능"
        confidence = "high"
    elif trust_score >= 60:
        label = "추가 검토 권장"
        confidence = "medium"
    elif trust_score >= 40:
        label = "주의 필요"
        confidence = "medium"
    else:
        label = "불확실"
        confidence = "high"

    evidence = list(dict.fromkeys([*theft_evidence, *forgery_evidence]))
    limitations = [
        "전용 탐지기와 출처 정보가 부족하면 판별 정확도가 낮아집니다.",
        "후처리, 크롭, 재압축에 의해 신호가 약해질 수 있습니다.",
    ]

    return TrustAnalysisResult(
        theft_risk_score=theft_risk,
        forgery_risk_score=forgery_risk,
        combined_risk_score=combined_risk,
        trust_score=trust_score,
        label=label,
        confidence=confidence,
        evidence=evidence,
        limitations=limitations,
        signals=[*theft_signals, *forgery_signals],
        source_attribution=source_attribution,
        source_trace=source_trace,
        embedding_analysis=embedding_analysis,
    )
