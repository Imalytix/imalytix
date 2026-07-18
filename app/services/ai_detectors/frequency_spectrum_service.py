"""
[설계 단계 스텁] 주파수(Fourier/웨이블릿) 기반 AI 생성 이미지 탐지기.

Imalytix_기술차별화_전략분석.md의 "B. Frequency Artifact 분석기" 항목과
동일한 방향이다. GAN/Diffusion의 업샘플링 연산은 자연 사진과 다른
고주파 스펙트럼 패턴(격자 모양 피크)을 남기는데, 사람 눈에는 안 보이지만
2D FFT를 적용하면 드러나는 경우가 많다.

알려진 한계(전략분석 문서에서도 지적됨): GAN에는 비교적 잘 통하지만
Diffusion 계열(Midjourney, Stable Diffusion 등)은 자연 이미지에 더 가까운
스펙트럼 분포를 만들어내서 탐지력이 떨어진다. 따라서 이 신호는 단독
판정용이 아니라 다른 신호(NPR, LLM 비전, 지문 기반)와의 융합용으로
설계한다.

현재 상태: 다른 ai_detectors 스텁과 동일한 응답 스펙만 제공.
실제 구현 시 예상 파이프라인 (설계안 문서 참고):
1. 그레이스케일 변환 → 2D FFT → 로그 스케일 파워 스펙트럼
2. 방위각 평균(azimuthal average)으로 1D 프로파일 추출
3. 경량 분류기(SVM 또는 얕은 MLP)로 real/fake 이진 판정
4. detector_results에 {"provider": "frequency_spectrum", ...} 형태로 추가
"""

from __future__ import annotations


def analyze_with_frequency_spectrum(*args, **kwargs) -> dict:
    """
    TODO(설계 단계): 실제 FFT 기반 스펙트럼 분류기 연동.
    지금은 다른 detector 스텁과 동일하게 "신호 없음"을 반환한다.
    """
    return {
        "provider": "frequency_spectrum",
        "detector_type": "ai_generated_image",
        "is_ai_generated": None,
        "score": None,
        "confidence": "low",
        "raw_response": None,
    }
