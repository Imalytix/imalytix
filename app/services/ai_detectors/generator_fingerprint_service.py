"""
[설계 단계 스텁] 생성모델 지문(fingerprint) 기반 탐지기.

Imalytix_기술전략_회의보고서.md에서 검토된 Noiseprint/Comprint 계열,
그리고 Imalytix_기술차별화_전략분석.md의 "C. GAN/Diffusion Fingerprint DB"
항목과 같은 방향이다.

핵심 아이디어: 카메라 지문(PRNU) 탐지 기법을 응용해서, 이미지를
디노이징 필터로 한 번 거른 뒤 원본에서 빼면 "잔차(residual)"가 남는다.
이 잔차에는 어떤 카메라/생성기가 만들었는지에 대한 미세한 통계적
흔적이 남아 있어서, Midjourney / DALL-E / Stable Diffusion / Flux 등
생성기별로 구분 가능한 경우가 많다.

알려진 한계: 신규 생성기가 계속 등장하므로 DB를 지속적으로 갱신해야
하고(전략분석 문서의 "DB 유지 비용" 지적), SNS 재압축을 거치면
잔차 신호 자체가 약해진다는 문제도 있다(Comprint가 압축 상황을
다루는 이유이기도 하다).

현재 상태: 다른 ai_detectors 스텁과 동일한 응답 스펙만 제공.
실제 구현 시 예상 파이프라인 (설계안 문서 참고):
1. 디노이징(예: 웨이블릿 디노이저)으로 잔차 추출
2. 잔차를 생성기 라벨로 지도학습(다중 클래스) 또는 비지도 클러스터링
3. "AI 생성 여부"뿐 아니라 "어떤 생성기로 만들었는지" 추정치도 반환
4. detector_results에 {"provider": "generator_fingerprint", ...} 형태로 추가
"""

from __future__ import annotations


def analyze_with_generator_fingerprint(*args, **kwargs) -> dict:
    """
    TODO(설계 단계): 실제 지문(fingerprint) 기반 분류기 연동.
    지금은 다른 detector 스텁과 동일하게 "신호 없음"을 반환한다.
    """
    return {
        "provider": "generator_fingerprint",
        "detector_type": "ai_generated_image",
        "is_ai_generated": None,
        "score": None,
        "confidence": "low",
        "raw_response": None,
    }
