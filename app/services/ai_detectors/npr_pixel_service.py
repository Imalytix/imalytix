"""
[설계 단계 스텁] 픽셀(공간) 기반 AI 생성 이미지 탐지기.

참고 논문: Tan et al., "Rethinking the Up-Sampling Operations in
CNN-based Generative Network for Generalizable Deepfake Detection"
(NPR, CVPR 2024) — Imalytix_기술전략_회의보고서.md에서 이미 검토됨.

NPR(Neighboring Pixel Relationships)의 핵심 아이디어:
GAN/Diffusion의 업샘플링 연산은 이웃 픽셀 간 관계에 특유의 규칙적인
흔적을 남긴다. 이 관계를 특징으로 뽑아 CNN 분류기에 넣으면,
개별 생성기에 과적합되지 않고 여러 생성기에 걸쳐 일반화가 잘 된다는
것이 논문의 주장이다.

현재 상태: 이 파일은 sightengine_service.py / reality_defender_service.py와
동일한 "응답 스텁" 패턴만 제공한다. 실제 모델 가중치/추론 로직은
Imalytix_추가탐지레이어_설계안.md의 로드맵에 따라 별도로 붙인다.

향후 실제 구현 시 넣을 것 (analysis_service.py 9번 단계에서
analyze_with_hive와 나란히 호출하는 그림):
1. NPR 논문 공개 구현체(GitHub)를 fine-tuning 없이 우선 그대로 사용
2. dataset/validation, GenImage 등으로 정확도 벤치마크
3. detector_results 리스트에 {"provider": "npr_pixel", ...} 형태로 추가
   → aggregator_service.aggregate_analysis()가 자동으로 점수에 반영
"""

from __future__ import annotations


def analyze_with_npr_pixel(*args, **kwargs) -> dict:
    """
    TODO(설계 단계): 실제 NPR 기반 픽셀 분류기 연동.
    지금은 다른 detector 스텁과 동일하게 "신호 없음"을 반환한다.
    """
    return {
        "provider": "npr_pixel",
        "detector_type": "ai_generated_image",
        "is_ai_generated": None,
        "score": None,
        "confidence": "low",
        "raw_response": None,
    }
