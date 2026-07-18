from __future__ import annotations

from app.constants.scoring import CONFIDENCE_WEIGHTS, FINAL_LABELS, VISUAL_EVIDENCE_POINTS


def make_recommendation(score: int) -> str:
    if score >= 80:
        return "AI 생성 이미지일 가능성이 높으므로 실제 사진처럼 공유하기 전 출처 확인이 필요합니다."
    if score >= 60:
        return "AI 생성 의심 이미지입니다. 원본 출처와 추가 정보를 확인하는 것이 좋습니다."
    if score >= 31:
        return "판단이 불확실합니다. 원본 파일, 출처, 추가 맥락 확인이 필요합니다."
    return "현재 분석 기준으로는 실제 이미지 가능성이 높습니다."


def _label_from_score(score: int) -> tuple[str, bool | None, str]:
    for threshold, label, is_ai_generated, confidence in FINAL_LABELS:
        if score >= threshold:
            return label, is_ai_generated, confidence
    return "실제 이미지 가능성 높음", False, "medium"


def _vision_multiplier(avg_score: float, confidence: str, active_signals: int) -> float:
    # 비전이 유일한 신호일 때 배율 대폭 확대
    if active_signals == 1:
        base = 65.0
    else:
        base = 48.0  # 복수 신호 시 (기존 30 → 48로 상향)

    # 신뢰도 high + 강한 확신 → 추가 부스트
    if confidence == "high" and avg_score >= 0.8:
        base *= 1.25
    elif confidence == "high" and avg_score >= 0.6:
        base *= 1.1

    return base


def aggregate_analysis(
    metadata_result: dict,
    detector_results: list[dict],
    vision_results: list[dict],
    source_result: dict | None = None,
) -> dict:
    final_score = 0.0
    evidence_summary: list[str] = []
    suspicious_regions: list[dict] = []
    limitations: list[str] = []

    # ── 1. 메타데이터 ────────────────────────────────────────────
    metadata_score = int(metadata_result.get("metadata_score", 0) or 0)
    final_score += metadata_score
    evidence_summary.extend([str(item) for item in metadata_result.get("evidence", []) if item])
    limitations.extend([str(item) for item in metadata_result.get("limitations", []) if item])

    # ── 2. 전용 탐지기 ───────────────────────────────────────────
    detector_scores = [
        float(r.get("score"))
        for r in detector_results
        if r.get("score") is not None
    ]
    if detector_scores:
        avg_detector = sum(detector_scores) / len(detector_scores)
        final_score += avg_detector * 25

    # ── 3. 비전 모델 ─────────────────────────────────────────────
    # 활성 신호 수 계산 (비전 배율 결정용)
    has_metadata  = metadata_score > 0
    has_detectors = bool(detector_scores)
    valid_vision  = [r for r in vision_results if not r.get("is_mock")]
    has_vision    = bool(valid_vision)

    active_signals = sum([has_metadata, has_detectors, has_vision])

    weighted_scores: list[float] = []
    visual_score = 0
    dominant_confidence = "low"

    for result in valid_vision:
        raw_score = result.get("score")
        score = float(raw_score) if raw_score is not None else 0.5
        score = max(0.0, min(1.0, score))
        confidence = str(result.get("confidence", "low"))
        weight = CONFIDENCE_WEIGHTS.get(confidence, 0.4)
        weighted_scores.append((score, confidence, weight))

        # 가장 높은 신뢰도 추적
        if confidence == "high":
            dominant_confidence = "high"
        elif confidence == "medium" and dominant_confidence != "high":
            dominant_confidence = "medium"

        for item in result.get("evidence", []):
            if isinstance(item, dict):
                desc = item.get("description")
                if desc:
                    evidence_summary.append(str(desc))
                severity = str(item.get("severity", "low"))
                visual_score += VISUAL_EVIDENCE_POINTS.get(severity, 1)

        suspicious_regions.extend([item for item in result.get("suspicious_regions", []) if item])
        limitations.extend([str(item) for item in result.get("limitations", []) if item])

    if weighted_scores:
        # 가중 평균 점수
        total_weight = sum(w for _, _, w in weighted_scores)
        avg_vision_score = sum(s * w for s, _, w in weighted_scores) / total_weight if total_weight else 0.0

        multiplier = _vision_multiplier(avg_vision_score, dominant_confidence, active_signals)
        vision_contribution = avg_vision_score * multiplier
        final_score += vision_contribution

        # ── 모델 합의 보너스 ─────────────────────────────────────
        # 점수 기반: 0.50 이상이면 AI 의심으로 카운트 (기존 0.60 → 0.50)
        # 판정 기반: is_ai_generated=True 필드도 함께 반영
        all_scores = [s for s, _, _ in weighted_scores]
        ai_agree_score   = sum(1 for s in all_scores if s >= 0.50)
        ai_agree_verdict = sum(1 for r in valid_vision if r.get("is_ai_generated") is True)
        ai_agree = max(ai_agree_score, ai_agree_verdict)

        real_agree = sum(1 for s in all_scores if s <= 0.30)
        if ai_agree >= 2:
            final_score += 10 * ai_agree  # 2모델 합의 +20, 3모델 합의 +30
        elif real_agree >= 2:
            final_score -= 8  # 실제 이미지 방향 합의 패널티

    # ── 4. 시각 근거 보너스 (최대 25점) ─────────────────────────
    final_score += min(visual_score, 25)

    # ── 5. 출처 패턴 ─────────────────────────────────────────────
    if source_result:
        if source_result.get("known_ai_cdn"):
            final_score += 5
        if source_result.get("trusted_source"):
            final_score -= 5
        evidence_summary.extend([str(item) for item in source_result.get("evidence", []) if item])

    final_score = max(0, min(100, round(final_score)))
    label, is_ai_generated, confidence_level = _label_from_score(final_score)

    return {
        "final_result": {
            "is_ai_generated": is_ai_generated,
            "ai_probability": final_score,
            "label": label,
            "confidence": confidence_level,
        },
        "evidence_summary": evidence_summary[:10],
        "suspicious_regions": suspicious_regions[:10],
        "limitations": list(dict.fromkeys(limitations)),
        "recommended_action": make_recommendation(final_score),
    }
