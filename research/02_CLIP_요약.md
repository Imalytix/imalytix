# CLIP 요약

## 원문

- 논문: CLIP: Learning Transferable Visual Models From Natural Language Supervision
- 링크: https://arxiv.org/abs/2103.00020

## 한줄 요약

CLIP은 이미지와 텍스트를 같은 의미 공간에 정렬하는 방식으로, 시각 정보와 설명 텍스트를 함께 활용할 수 있게 한다.

## 왜 중요한가

- 이미지 자체 유사도뿐 아니라, 텍스트 기반 검색과 설명 생성에 연결할 수 있다.
- “이 이미지가 어떤 맥락으로 공유되었는가”를 해석하는 데 도움이 된다.
- 플랫폼 설명문, 캡션, 파일명, URL 문구와 함께 소스 단서를 묶기 좋다.

## Imalytix 접목 포인트

- 이미지-캡션 정렬 점수
- 파일명 / 게시글 텍스트 / OCR 결과와의 의미적 일치성 평가
- source attribution의 보조 신호로 사용

## 기대효과

- “공간 인테리어”, “상품 사진”, “예시 이미지”처럼 텍스트 맥락을 함께 분석 가능
- 출처 추적에서 단순 비전 유사도보다 더 풍부한 단서를 제공

## 주의점

- CLIP similarity가 높다고 원본 출처가 확정되지는 않는다.
- 텍스트 표현이 짧거나 광고성인 경우 신뢰도가 떨어질 수 있다.

## 다음 액션

- OCR / caption / filename token과 CLIP 기반 의미 정렬 점수를 분리해서 기록
- 추후 다중 모달 source attribution 모듈에 통합
