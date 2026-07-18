# Imalytix 기술전략 회의보고서

## 1. 개요

Imalytix는 이미지가 실제 촬영물인지, 편집된 이미지인지, 생성형 AI로 만들어진 이미지인지, 또는 타인의 콘텐츠를 재사용한 도용 이미지인지까지 함께 판단하는 이미지 신뢰성 분석 서비스다.

이 서비스의 핵심 방향은 단일 모델 판정이 아니라, 여러 기술 계층을 결합한 신뢰성 판단 아키텍처를 만드는 것이다.

현재의 목표는 다음과 같다.

- 이미지 내부 신호를 먼저 본다.
- 출처와 재사용 패턴을 함께 본다.
- 시각적 이상 징후를 별도로 본다.
- 마지막에 이 신호를 종합해 설명 가능한 리포트를 만든다.

즉, Imalytix는 “AI 이미지다 / 아니다”를 단정하는 도구가 아니라, “왜 그렇게 보이는지”를 근거와 함께 설명하는 신뢰성 분석 엔진이다.

## 2. 현재까지의 개발현황

### 2-1. 현재 아키텍처 구조

```text
[Input Layer]
  ├─ 웹 업로드
  └─ URL 입력

        ↓

[Validation & Normalization]
  ├─ 파일 형식 검증
  ├─ 이미지 디코딩 검증
  ├─ EXIF orientation 보정
  └─ 리사이즈 / JPEG 정규화

        ↓

[Evidence Extraction]
  ├─ pHash 생성
  ├─ EXIF / PNG metadata 분석
  ├─ Source Attribution 분석
  ├─ pHash 저장소 검색
  └─ Embedding 유사도 검색

        ↓

[AI / Forensic Inference]
  ├─ OpenAI Vision
  ├─ Gemini / Claude 인터페이스
  ├─ 전용 detector 인터페이스
  └─ 시각적 근거 해석

        ↓

[Risk Integration]
  ├─ 도용 위험도
  ├─ 위조 위험도
  ├─ trust_score
  └─ 최종 라벨 / 권장 조치

        ↓

[Delivery Layer]
  ├─ FastAPI JSON 응답
  ├─ React Web UI
  └─ Chrome Extension Side Panel
```

### 2-2. 서비스 플로우

1. 사용자가 이미지를 업로드하거나 URL을 입력한다.
2. 서버가 입력 파일을 검증한다.
3. 이미지를 전처리하고 pHash를 생성한다.
4. EXIF, PNG metadata, 파일명, URL 패턴을 분석한다.
5. Source Attribution으로 출처 단서를 구조화한다.
6. pHash 저장소와 embedding 저장소에서 유사 이미지를 찾는다.
7. 필요 시 Vision 모델과 전용 탐지기를 호출한다.
8. 도용 위험도와 위조 위험도를 따로 계산한다.
9. trust_score와 최종 라벨을 생성한다.
10. 웹 UI와 익스텐션으로 결과를 보여준다.

### 2-3. 현재 구현된 핵심 모듈

- FastAPI 서버 및 라우터
- 이미지 업로드 / URL 분석 API
- 이미지 검증 및 전처리
- pHash 기반 저장소
- metadata 분석
- trust analysis
- source attribution
- baseline embedding retrieval
- SQLite 기반 vector store
- benchmark 스크립트
- React Web UI
- Chrome Extension Side Panel

### 2-4. 현재 아키텍처의 의미

현재 구조의 장점은 다음과 같다.

- pHash로 빠르게 동일 이미지를 잡는다.
- embedding으로 편집된 유사 이미지를 확장 탐지한다.
- metadata로 생성형 도구 흔적을 본다.
- source attribution으로 재배포와 원출처 단서를 본다.
- Vision 모델은 최종 설명과 시각적 근거만 보강한다.

즉, 비용이 높은 LLM 중심이 아니라, 구조화된 증거 중심 아키텍처다.

## 3. 앞으로의 개선사항

### 3-1. Phase A: 유사도 검색 고도화

- 현재 baseline embedding을 실제 DINOv2 또는 CLIP 어댑터로 교체
- `pgvector` 기반 저장소로 확장
- top-k 유사 이미지 검색을 운영 수준으로 고도화
- 크롭 / 리사이즈 / 재압축 / 색감 변경 이미지 재탐지 강화

### 3-2. Phase B: 위조 탐지 정교화

- TruFor / Noiseprint 계열 아이디어를 반영한 forensic branch 도입
- 지역 단위 이상 징후를 patch-level로 설명
- 조명, 반사, 텍스처, 경계, 노이즈 패턴을 별도 점수화
- 이미지 상세 영역의 bbox 또는 heatmap 근거 강화

### 3-3. Phase C: 출처 추적과 증거 결합

- C2PA / Content Credentials 파싱 연동
- 파일명 / 도메인 / CDN / 공유 경로 기반 attribution 강화
- SNS / 커뮤니티 재업로드 패턴 추적
- OCR 결과와 출처 단서를 결합해 뉴스 / 쇼핑 / 인테리어 레퍼런스 이미지 검증 강화

### 3-4. Phase D: 벤치마크와 평가 체계

- 공용 데이터셋과 내부 샘플셋을 함께 사용
- 도용 탐지 / 위조 탐지 / 출처 추적 성능을 분리 측정
- precision / recall / F1 / AUROC를 기록
- 모델별 비교 리포트를 정기적으로 생성

### 3-5. Phase E: 운영 효율화

- pHash / embedding 캐시 전략 최적화
- 모델 호출 라우팅 정책 강화
- 실패한 케이스를 재학습 후보로 분류
- 사용자 피드백을 통한 threshold tuning

## 4. 주요 기술스택

### Backend

- Python 3.11+
- FastAPI
- Pydantic
- Pillow
- imagehash
- SQLite

### Analysis / Retrieval

- pHash
- embedding retrieval
- cosine similarity
- vector store
- source attribution

### AI / Forensics

- OpenAI Vision
- Gemini interface
- Claude interface
- TruFor-inspired forensic reasoning
- Noiseprint-inspired anomaly cues

### Frontend / Extension

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Chrome Extension Side Panel

### Evaluation

- benchmark dataset manifest
- markdown report generation
- reproducible local runs

## 5. 제한사항 / 추진사항

### 제한사항

- LLM은 도구이고, 포렌식의 최종 답이 아니다.
- 메타데이터는 삭제 또는 변조될 수 있다.
- pHash는 편집 강도가 커지면 약해진다.
- embedding은 의미 유사성을 주지만 출처를 직접 증명하지는 못한다.
- C2PA는 달려 있지 않은 콘텐츠가 아직 많다.
- 외부 AI API는 비용과 정책 제약이 있다.

### 추진사항

- 벡터 저장 계층을 SQLite baseline에서 PostgreSQL / pgvector로 확장
- DINOv2와 CLIP을 실제 모델로 연결
- forensic branch를 별도 서비스로 분리
- benchmark report를 정례화
- source attribution을 C2PA와 연결
- 사용자 피드백을 통해 threshold를 조정

## 6. 주요 논문별 기술과 우리 서비스 접목사항

| 논문 / 표준 | 핵심 아이디어 | Imalytix 접목 방식 |
|---|---|---|
| [DINOv2: Learning Robust Visual Features without Supervision](https://arxiv.org/abs/2304.07193) | 자기지도 비전 표현 학습 | 도용 탐지용 이미지 embedding backbone 후보 |
| [CLIP: Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020) | 이미지-텍스트 공통 표현 공간 | 의미 유사도, 검색, 설명 보조용 embedding backbone 후보 |
| [TruFor](https://arxiv.org/abs/2212.10957) | RGB와 노이즈 단서를 결합한 forgery detection | 위조 탐지 branch 설계의 직접적 참고 모델 |
| [Noiseprint](https://arxiv.org/abs/1808.08396) | 카메라 모델 fingerprint / 노이즈 단서 | 이미지 내부 노이즈 패턴과 불일치 탐지에 활용 |
| [Comprint](https://arxiv.org/abs/2210.02227) | 압축 fingerprint 기반 forensic | SNS 재압축 / 재업로드 상황에서의 약한 신호 추적 |
| [ManTra-Net](https://arxiv.org/abs/1901.08971) | 일반화 가능한 manipulation tracing | 지역 단위 변형 흔적 탐지의 개념적 기반 |
| [C2PA Specifications](https://spec.c2pa.org/specifications/specifications/2.4/index.html) | provenance / authenticity 표준 | 출처 추적과 신뢰성 증명의 표준 축 |
| [C2PA Guidance](https://spec.c2pa.org/specifications/specifications/2.4/guidance/Guidance.html) | provenance 워크플로 가이드 | 향후 Content Credentials 해석 로직의 기준 |

### 해석

이 서비스의 고유 아키텍처는 단일 모델 중심이 아니라 다음 네 축의 결합이다.

1. Similarity Layer: pHash + embedding retrieval
2. Provenance Layer: source attribution + C2PA
3. Forensic Layer: metadata + noise / anomaly / visual cues
4. Reasoning Layer: trust score + explanation

이 네 축을 합치면, “AI 이미지인지”뿐 아니라 “왜 그렇게 판단했는지”, “출처가 어디인지”, “얼마나 신뢰할 수 있는지”까지 설명할 수 있다.

## 7. 회의용 결론

Imalytix는 앞으로 단순 AI 이미지 탐지 서비스가 아니라, 이미지 신뢰성 검증 인프라로 확장할 수 있다.

우리가 만드는 차별점은 다음과 같다.

- pHash로 빠른 동일성 탐지
- embedding으로 편집된 유사 이미지 탐지
- metadata와 source attribution으로 출처 검증
- forensic cues로 위조 흔적 분석
- trust score로 사용자가 이해할 수 있는 결과 제공

즉, “무슨 모델을 썼는가”보다 “어떤 증거를 어떻게 조합하는가”가 핵심 경쟁력이다.

---

## 부록: 읽을거리

- [논문 리서치 인덱스](./research/00_논문리서치_인덱스.md)
- [DINOv2 요약](./research/01_DINOv2_요약.md)
- [CLIP 요약](./research/02_CLIP_요약.md)
- [이미지 포렌식 요약](./research/03_이미지포렌식_요약.md)
- [C2PA / 출처추적 요약](./research/04_C2PA_출처추적_요약.md)
- [벤치마크 데이터셋 메모](./research/05_벤치마크_데이터셋_메모.md)
