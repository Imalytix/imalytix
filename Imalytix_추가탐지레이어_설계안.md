# Imalytix 추가 탐지 레이어 설계안 — 픽셀 CNN / 주파수 / 생성모델 지문

작성일: 2026-07-12
관련 문서: `Imalytix_기술전략_회의보고서.md`, `Imalytix_기술차별화_전략분석.md`,
`AI_이미지탐지_기술조사_2024-2025.md`, `Imalytix_PhaseA_체크리스트.md`

이 문서는 pHash → DINOv2/CLIP 임베딩 → 3-LLM 앙상블로 이어지는 현재
분석 파이프라인에, "이미지 자체의 저수준 신호"만으로 AI 생성 여부를
판단하는 세 가지 보조 탐지 레이어를 추가하기 위한 설계/기획 문서다.
세 레이어 모두 기존 `app/services/ai_detectors/` 구조(hive, sightengine,
reality_defender와 동일한 응답 스펙)를 따르도록 스텁 파일을 이미
만들어 두었다 (`npr_pixel_service.py`, `frequency_spectrum_service.py`,
`generator_fingerprint_service.py`). 이 문서는 그 스텁들을 실제로
채울 때의 방향을 정리한 것이다.

---

## 1. 왜 필요한가

현재 원칙(PhaseA 체크리스트에 명시): "LLM은 최종 설명과 요약에만 쓴다.
판별 핵심은 pHash, embedding, source pattern, metadata다." 여기에 더해,
저수준 픽셀 신호 기반 탐지기를 추가하면:

- LLM 3사(OpenAI/Gemini/Claude)는 범용 멀티모달 모델이라 서로 blind
  spot을 공유할 수 있다(기술전략 문서에서도 지적된 리스크). 완전히
  다른 원리로 동작하는 신호를 섞으면 앙상블의 다양성이 커진다.
- 비용: 저수준 탐지기는 로컬 추론이라 LLM 호출보다 훨씬 저렴하다.
  quick 모드에서 LLM 호출 여부를 판단하는 추가 게이트로도 쓸 수 있다
  (지금 막 추가한 `has_strong_embedding_evidence`와 같은 자리).
- 특허/차별화: 기술차별화 문서의 "E. Multi-evidence Fusion 알고리즘"과
  직결된다 — 신호 자체는 공개 연구 기반이어도, 신호들을 어떻게
  가중치·불일치 처리하는지의 융합 로직은 자체 설계 영역이다.

단, 검증 결과(memory 기준)로 알려진 현실: 2026년 벤치마크에서 최신
생성기(Flux Dev, Midjourney v7, Firefly v4)는 기존 탐지기들의 평균
탐지 정확도가 18~30%에 불과했다. 즉 이 세 레이어는 **주 판정 신호가
아니라 보조 신호**로 설계해야 하며, 아래 4장의 스코어링 반영 방식도
이 전제를 따른다.

## 2. 파이프라인 상 위치

```
pHash 생성
  → DINOv2 / CLIP 임베딩 (유사도 검색, 도용/재업로드 탐지)
  → [신규] 픽셀 CNN(NPR) / 주파수(FFT) / 생성모델 지문
        └ 세 레이어는 서로 독립적으로 병렬 실행 가능 (LLM 호출과 동시에)
  → 3-LLM 비전 앙상블 (OpenAI, Gemini, Claude) — 설명/요약 담당
  → aggregator_service.aggregate_analysis() 에서 전체 신호 합산
```

`analysis_service.py`의 9번 단계(provider 호출)에서 `analyze_with_hive`와
나란히 `provider_tasks`에 추가하는 구조를 그대로 재사용하면 된다.
즉 LLM 호출과 병렬로 실행되므로 전체 지연시간에 큰 영향을 주지 않는다.

## 3. 레이어별 설계

### 3.1 픽셀(공간) 기반 — `npr_pixel_service.py`

| 항목 | 내용 |
|---|---|
| 근거 논문 | Tan et al., NPR (CVPR 2024) — 기술전략 문서에서 이미 검토됨 |
| 원리 | GAN/Diffusion의 업샘플링이 이웃 픽셀 관계에 남기는 규칙적 흔적을 탐지 |
| 강점 | 여러 생성기에 걸쳐 일반화가 비교적 잘 됨(논문 주장) |
| 약점 | 최신 diffusion 모델·후처리(재압축)에는 정확도가 크게 떨어짐(위 18~30% 벤치마크) |
| 구현 방식 | 처음부터 학습하지 않고 공개 GitHub 구현체를 그대로 채택 → `dataset/validation` + GenImage로 벤치마크 |
| 출력 | `score`(0~1 AI 확률), `confidence` |

### 3.2 주파수 기반 — `frequency_spectrum_service.py`

| 항목 | 내용 |
|---|---|
| 근거 | 기술차별화 문서 "B. Frequency Artifact 분석기" |
| 원리 | 그레이스케일 → 2D FFT → 로그 스펙트럼 → 방위각 평균 1D 프로파일 |
| 분류기 | 얕은 MLP 또는 SVM(스펙트럼 프로파일만으로 충분, CNN 불필요) |
| 강점 | 구현 난이도 낮음(오픈소스 연구 기반), 연산 가벼움 |
| 약점 | GAN에는 강하나 Diffusion에는 약함(문서에도 명시된 한계) → 단독 판정 금지, 융합 전용 |
| 출력 | `score`, `confidence`, (선택) 스펙트럼 이상 부위 bbox |

### 3.3 생성모델 지문(fingerprint) 기반 — `generator_fingerprint_service.py`

| 항목 | 내용 |
|---|---|
| 근거 | 기술전략 문서의 Noiseprint/Comprint, 기술차별화 문서 "C. Fingerprint DB" |
| 원리 | 디노이징 후 잔차(residual) 추출 → 생성기별 통계적 지문 학습 |
| 강점 | "AI 여부"뿐 아니라 "어떤 생성기로 만들었는지"까지 추정 가능 → 설명 근거로 활용도 높음 |
| 약점 | 신규 생성기 등장 속도가 빨라 DB 유지비용 큼, SNS 재압축에 취약(Comprint가 이 문제를 다룸) |
| 구현 단계 | 1) Noiseprint 공개 구현체로 잔차 추출 → 2) 지도학습(다중 클래스) 또는 비지도 클러스터링 |
| 출력 | `score`, `confidence`, (선택) `suspected_generator`(예: "stable-diffusion") |

## 4. aggregator 반영 방식 (제안)

`aggregator_service.aggregate_analysis()`는 이미 `detector_results` 리스트를
평균 내어 `final_score`에 25점 비중으로 반영하는 구조를 갖고 있다
(`avg_detector * 25`). 세 레이어를 추가하면 이 리스트에 항목이 늘어나며,
설계 시 아래를 반드시 고려해야 한다.

1. **가중치 재조정 필요**: 현재 25점 비중은 Hive 1개 기준으로 잡힌
   값이다. detector가 4개(Hive + 신규 3개)로 늘면 평균이 희석되면서
   개별 강한 신호가 묻힐 수 있다. 단순 평균 대신 "가장 확신 있는
   detector의 신뢰도"를 가중치로 쓰는 방식(비전 모델에 이미 적용된
   `CONFIDENCE_WEIGHTS` 패턴)을 detector_results에도 도입할 것을 제안.
2. **불일치 처리**: 세 레이어가 서로 다른 결론을 낼 때(예: 주파수는
   AI, 지문은 실제) 단순 평균이 아니라 "합의 보너스/패널티"
   (`ai_agree`, `real_agree` 로직) 를 detector 레벨에도 확장하는 것을
   고려. 이게 기술차별화 문서의 "자체 설계 신뢰도 융합 알고리즘"의
   실체가 된다.
3. **설명 가능성**: `evidence_summary`에 "어떤 레이어가 왜 의심했는지"를
   자연어로 남겨서, LLM 설명 단계(3-LLM)가 이 근거를 요약에 활용할 수
   있게 한다(Imalytix 핵심 차별점인 "판단 근거 제시"와 직결).

## 5. 데이터셋 계획

memory/PhaseA 체크리스트에서 이미 계획된 4단 데이터셋 구성을 그대로 재사용한다.

- 공개 벤치마크: GenImage, CIFAKE, NTIRE 2026, X-AIGD
- 최신 생성기별 데이터셋: Stable Diffusion, FLUX 자체 생성분
- 자체 도메인 데이터: `dataset/validation`, `dataset/validation_test`
- C2PA/EXIF 인증된 실제 이미지: `c2pa-org/public-testfiles`

세 레이어 모두 같은 데이터셋으로 벤치마크해서 `benchmarks/` 아래
비교 리포트(`benchmark_report.md` 관례를 따름)를 남기는 것을 권장한다.

## 6. 단계별 로드맵 (제안)

| 단계 | 내용 | 산출물 |
|---|---|---|
| 0 (완료) | 스텁 서비스 3개 생성, 설계 문서 작성 | 이 문서 + 3개 stub 파일 |
| 1 | 주파수 레이어 프로토타입(구현 난이도 최저) → `dataset/validation`으로 1차 벤치마크 | `benchmarks/frequency_report.md` |
| 2 | NPR 픽셀 분류기 공개 구현체 연동 → 벤치마크 | `benchmarks/npr_report.md` |
| 3 | 세 레이어를 `analyze_image_bytes()` 9번 단계에 실제로 연결(병렬 호출) | PR + pytest 추가 |
| 4 | aggregator 가중치/합의 로직 재설계(4장 반영) | `aggregator_service.py` 개편 |
| 5 | 지문 기반 레이어(가장 유지비용 큼) → 생성기 라벨 데이터 축적 후 착수 | `generator_fingerprint_service.py` 실구현 |

## 7. 리스크 / 열린 질문

- 세 레이어 모두 로컬 추론이라도 모델 로딩(특히 NPR)은 GPU가 있으면
  유리하다 — 현재 서버 환경(CPU 전용 가정)에서 지연시간 실측 필요.
- 주파수/지문 레이어는 SNS 재압축에 약하다는 게 공통 약점이다.
  Imalytix의 실사용 맥락(당근마켓 등 재압축이 일상적인 플랫폼)과
  정면으로 충돌하는 지점이므로, 벤치마크 시 반드시 "재압축 후"
  성능을 함께 측정해야 한다(기존 embedding 파이프라인에 적용 중인
  원칙과 동일).
- 지문 기반 DB는 신규 생성기 대응 주기를 어떻게 운영할지 결정 필요
  (수동 업데이트 vs. 준지도 학습 파이프라인).
- KAIST 연구자 미팅에서 논의 예정이었던 "fusion weighting methodology"
  질문과 이 문서의 4장이 직접 연결되므로, 미팅 결과를 이 문서에
  반영해서 갱신할 것.
