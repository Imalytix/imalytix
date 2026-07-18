# DINOv2 요약

## 원문

- 논문: DINOv2: Learning Robust Visual Features without Supervision
- 링크: https://arxiv.org/abs/2304.07193

## 한줄 요약

DINOv2는 라벨 없이도 강한 비전 표현을 학습할 수 있음을 보여주는 self-supervised visual representation 모델이다.

## 왜 중요한가

- 이미지 검색과 유사도 탐색의 기본 backbone으로 쓰기 좋다.
- 동일 이미지, 재압축 이미지, 리사이즈된 이미지, 유사 구도 이미지를 묶는 데 유리하다.
- Imalytix의 pHash 뒤에 오는 2차 similarity layer로 적합하다.

## Imalytix 접목 포인트

- 업로드 이미지의 embedding 생성
- pgvector 또는 유사 벡터 저장소에 저장
- 과거 분석 이미지와 top-k 유사도 검색
- 도용 가능성, 재업로드 가능성, 원본 후보 추적에 활용

## 기대효과

- AI 생성 여부와 별개로 이미지 재사용/도용 패턴을 찾을 수 있다.
- pHash가 놓치는 semantic similarity를 보완할 수 있다.

## 주의점

- 임베딩 유사도만으로 출처를 단정할 수 없다.
- 제품 사진, 풍경, 인물처럼 시각적으로 비슷한 카테고리에서 오탐이 생길 수 있다.

## 다음 액션

- DINOv2 계열 embedding adapter를 별도 서비스로 추상화
- 이미지 크롭, 본문, 배경 등의 region-level embedding 확장
