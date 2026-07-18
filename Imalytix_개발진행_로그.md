# Imalytix 개발 진행 로그

## 원칙

- 외부 유료 API, 비용 발생 작업, 개인정보 접근 가능성이 있는 작업은 사전 승인 후 진행
- 원본 이미지는 저장하지 않음
- 로컬에서 재현 가능한 구조를 우선 구현

## 현재 목표

- 이미지 신뢰성, 위변조, 도용 문제를 다루는 분석 엔진 고도화
- 3개 AI 모델 앙상블 중심 구조를 넘어, pHash 기반 재사용 계층을 통해 비용 절감

## 오늘 진행한 내용

- pHash 캐시 저장소 설계
- SQLite 기반 로컬 분석 재사용 계층 추가
- 설정값에 pHash DB 경로 및 유사도 임계치 추가
- API 응답에 캐시 정보 필드 추가
- 이미지 도용 탐지 로직 추가
- 이미지 위조 탐지 로직 추가
- 도용/위조를 통합한 신뢰성 스코어링 추가
- 응답 스키마에 `trust_analysis` 추가
- 캐시 재사용 경로와 신뢰성 분석 경로에 대한 테스트 추가
- 유사 pHash 재사용까지 도용 탐지에 반영
- 실제 서버 기동 및 헬스 체크 확인
- 웹/익스텐션에 분석 진행 현황 UI 추가
- 익스텐션 사이드패널을 단계형 로더로 개선

## 다음 작업

- exact / similar 이미지 재사용 정책 정교화
- 분석 결과를 pHash DB에 저장하는 흐름 검증
- 캐시 히트 시 응답 품질과 안전성 테스트
- 필요 시 메타데이터 / source pattern / detector 결과를 더 세분화
- 프론트 화면에 도용 / 위조 / 신뢰성 지표 노출 여부 검토

## 테스트 현황

- `python -m pytest -q`
- 결과: `25 passed`
- `GET /api/v1/health` 정상 응답 확인
- `GET /api/v1/health/usage` 정상 응답 확인
- 웹 프론트 `npm run build` 성공
- 익스텐션 `npm run build` 성공
- 익스텐션 zip 재생성 완료

## 웹 / 익스텐션 테스트 절차

### 1) 백엔드 실행

```bash
python -m uvicorn app.main:app --reload
```

### 2) 웹 프론트 실행

```bash
cd imalytix-frontend
npm install
npm run dev
```

- 접속 주소: `http://localhost:5173`
- 직접 업로드 테스트 후 `상세보기`로 `/detail` 확인

### 3) 익스텐션 빌드

```bash
cd imalytix-extension
npm install
npm run build
```

### 4) 크롬에 로드

- `chrome://extensions` 접속
- 개발자 모드 켜기
- `압축해제된 확장 프로그램 로드`
- `C:\Users\cubix\Desktop\성윤\imalytix-extension\dist` 선택

### 5) 익스텐션 테스트

- 웹페이지의 이미지에서 우클릭
- `Imalytix AI로 분석하기` 메뉴 선택
- 결과가 side panel 또는 저장된 화면으로 표시되는지 확인

## 현재 상태 요약

- 같은 이미지 재분석 시 pHash DB에서 바로 재사용 가능
- 도용 위험은 중복 pHash, 출처 패턴, 파일명 패턴으로 판단
- 위조 위험은 메타데이터, 전용 탐지기, Vision 결과, 시각 근거로 판단
- 유사 pHash까지 포함해 크롭/재압축된 재사용 흔적도 일부 포착 가능
- 최종적으로 `trust_score`와 `combined_risk_score`를 함께 제공

## 이번 검증 결과 요약

- 백엔드 서버 기동 성공
- 웹 프론트 생산 빌드 성공
- 익스텐션 생산 빌드 성공
- 자동 테스트 통과
- 도용 / 위조 / 신뢰성 분석 경로 정상 동작 확인
- 분석 중 진행 현황 UI 확인 가능
- OpenAI / Gemini / Claude 사용량 조회 API 추가

## 프로젝트 가동 상태

- 백엔드: `http://127.0.0.1:8000`
- 웹 UI: `http://localhost:5173`
- 크롬 익스텐션: unpacked dist 로드 상태
- 확인 시점에 웹 UI와 백엔드 헬스 체크 모두 응답 정상

## 배포용 압축본

- 최신 익스텐션 압축본 생성 완료
- 경로: `deliverables/imalytix-extension-dist.zip`
- 용도: 전달 / 업로드 / 배포
- 주의: 크롬 로컬 로드는 여전히 `dist` 폴더를 직접 선택해야 함

## 메모

- 현재 구현은 로컬 파일시스템과 SQLite만 사용
- 외부 서비스 호출은 기존 백엔드 설정에 따름
- 추가 비용이 발생하는 작업은 진행 전 사용자 승인 요청
## 2026-07-03 로컬 실행 완료

- `.env`의 `MOCK_VISION_FALLBACK=true`로 변경해 로컬 안전 모드 활성화
- 백엔드: `http://127.0.0.1:8000`
- 프론트: `http://localhost:5173`
- 백엔드 헬스체크 정상 확인
- 프론트 개발 서버 정상 확인
- `python -m pytest -q` 결과: `25 passed`
- `npm.cmd run build` 결과: 프론트/익스텐션 모두 성공
- 로그 파일:
  - `logs/backend.out.log`
  - `logs/backend.err.log`
  - `logs/frontend.out.log`
  - `logs/frontend.err.log`

## 2026-07-03 실제 AI API 모드 전환

- `MOCK_VISION_FALLBACK=false` 유지로 실제 AI API 호출 모드 활성화
- 라우팅 정책을 OpenAI Vision 우선 1개 호출로 축소해 비용 절감
- 프론트 상단에 `실제 AI API 모드` 배지 표시 추가
- `/api/v1/health/usage` 응답에 `real_api_mode`와 `mock_vision_fallback` 추가
- 실제 분석 테스트 1건 수행:
  - 입력: `https://picsum.photos/seed/imalytix-unique-123/800/600.jpg`
  - 결과: API 호출 성공
  - OpenAI 응답은 콘텐츠 정책 사유로 거절 메시지를 반환했지만, 실제 외부 호출은 정상 수행됨
  - 응답 자체와 에러 메시지는 백엔드 로그에 기록됨

## 2026-07-05 지시서 재정렬 및 Phase A 체크리스트 작성

- 첨부된 `Imalytix 개발 지시서`를 기준으로 현재 구현 상태 재점검
- 현재 완료 축:
  - FastAPI 서버
  - 업로드/URL 분석 API
  - 메타데이터 분석
  - pHash 저장소
  - 도용/위조 신뢰성 점수화
  - 프론트 UI
  - Chrome Extension 빌드
- 아직 남은 축:
  - embedding 기반 유사도 검색
  - DINOv2 / CLIP 비교
  - pgvector 또는 동등한 벡터 저장소
  - benchmark 데이터셋/리포트
  - source attribution 강화
- 새 파일 생성:
  - `Imalytix_PhaseA_체크리스트.md`
- 다음 구현 우선순위:
  1. embedding 서비스 인터페이스
  2. vector store 인터페이스
  3. pHash + embedding 후보군 검색
  4. 벤치마크 포맷 정의
  5. benchmark report MD 자동화

## 2026-07-05 Phase A 1차 구현 및 벤치마크 실행

- `embedding_service.py` 추가
  - `dino` / `clip` baseline embedding 전략 구현
- `vector_store.py` 추가
  - SQLite 기반 embedding 저장/검색 계층 구현
- `source_attribution_service.py` 추가
  - URL, 파일명, 도메인, AI 서비스 패턴, 신뢰 단서 구조화
- `AnalysisResponse` / `trust_analysis`에 Phase A 결과 필드 추가
  - `source_attribution`
  - `embedding_analysis`
- `trust_analysis_service.py`를 도용/위조/출처/embedding 신호를 반영하도록 재정리
- 샘플셋 벤치마크 스크립트 추가:
  - `scripts/run_phase_a_benchmark.py`
  - `benchmarks/phase_a_manifest.json`
  - `reports/phase_a_benchmark_report.md`
- 벤치마크 결과 요약:
  - DINO baseline label accuracy: `0.3667`
  - CLIP baseline label accuracy: `0.4667`
  - 이 baseline은 실제 DINOv2/CLIP이 아니라 교체 가능한 Phase A 어댑터로 동작
## 2026-07-05 이미지 기반 출처 추적 및 데이터셋 구축기 착수

- `source_attribution`와 별도로 이미지 유사도 기반 역검색 결과를 내는 `visual_source_trace` 축을 추가함
- 현재 동작 방식
  - pHash + embedding 유사도 검색 결과를 이용해
  - 다른 저장소/플랫폼에 존재하는 유사 이미지 후보를 보여줌
  - Google Lens처럼 "이 이미지가 다른 플랫폼에 등장한 흔적"을 설명하는 방향
- 새로 추가한 파일
  - `app/schemas/source_trace.py`
  - `app/services/visual_source_trace_service.py`
  - `scripts/build_validation_dataset.py`
  - `research/06_데이터셋_구축_가이드.md`
- 검증 결과
  - 전체 pytest: `30 passed`
  - `visual_source_trace` 단위 확인 성공
  - 데이터셋 생성 스크립트 경량 실행 성공

## 2026-07-05 데이터셋 생성 완료

- `samples_test`를 기반으로 5GB 제한 내 로컬 검증 데이터셋을 생성함
- 생성 경로:
  - `dataset/validation`
- 생성 결과:
  - `rows=30`
- 용도:
  - 이미지 유사도 검색 검증
  - 도용/재업로드 흔적 검증
  - DINO / CLIP / source trace / trust analysis 공통 벤치마크
- 중요한 해석:
  - 현재의 `visual_source_trace`는 외부 웹 전체를 직접 검색하는 기능이 아니라
    - 내부에 쌓인 이미지 인덱스와의 유사도 검색으로
    - “다른 플랫폼에 쓰였을 가능성이 있는 후보”를 찾는 구조이다.

## 2026-07-05 데이터셋 라벨 규칙 보정

- 초기 자동 라벨링이 너무 느슨해서 파일명 일부 문자열 때문에 오탐이 생길 수 있었음
- 라벨 규칙을 토큰 기준으로 보정함
  - `REAL`
  - `AI`
- 데이터셋을 다시 생성했고, 현재 `dataset/validation`은 라벨이 정상 반영됨
- 최종 확인:
  - `pytest`: `30 passed`

## 2026-07-12 실제 DINOv2/CLIP 임베딩 레이어 + pHash→임베딩→3-LLM 라우팅 연동

- 목적: "이 baseline은 실제 DINOv2/CLIP이 아니라 교체 가능한 Phase A 어댑터로
  동작" 상태를 벗어나, 실제 모델을 붙이고 임베딩 레이어가 3-LLM(OpenAI/Gemini/
  Claude) 앙상블 호출 판단에도 반영되도록 흐름을 정리
- 새 파일:
  - `app/services/embedding_models/dinov2_model.py`
    - Hugging Face `facebook/dinov2-small`(ViT-S/14, 384dim) 래퍼
    - CLS 토큰 임베딩 추출 + L2 정규화
  - `app/services/embedding_models/clip_model.py`
    - OpenCLIP `ViT-B-32`(openai pretrained) 래퍼
    - 이미지 임베딩 추출 + L2 정규화
  - 두 모듈 모두 torch/transformers/open_clip을 함수 내부에서 지연 import
    → `EMBEDDING_MODEL_BACKEND=legacy`(기본값)일 때는 무거운 라이브러리가
    전혀 로드되지 않음
- 수정 파일:
  - `app/services/embedding_service.py`
    - `build_embedding()`이 `settings.embedding_model_backend`에 따라
      real(실모델) / legacy(기존 baseline) 분기
    - real 모드에서 로딩/추론 실패 시 legacy로 안전 폴백 + 로그 남김
    - 기존 baseline 로직은 `_legacy_baseline_embedding()`으로 이름만 정리(동작 동일)
  - `app/config.py`
    - `EMBEDDING_MODEL_BACKEND`(기본 `legacy`), `DINOV2_MODEL_NAME`,
      `CLIP_MODEL_NAME`, `CLIP_PRETRAINED_TAG`, `EMBEDDING_DEVICE` 추가
    - `EMBEDDING_ROUTING_SHORTCUT_ENABLED`(기본 `false`), `EMBEDDING_STRONG_
      SIMILARITY_THRESHOLD`(기본 `0.97`) 추가 — 비용/오탐 리스크 때문에 기본 OFF
  - `.env.example`, `requirements.txt`에 위 설정/의존성(`torch`, `transformers`,
    `open_clip_torch`) 반영 (선택 설치, 팀 검토 후 설치 권장)
  - `app/services/router_policy.py`
    - `has_strong_embedding_evidence()` 신규: `has_strong_metadata_evidence()`와
      같은 자리에 임베딩 레이어 게이트 추가
    - `decide_routing()`에 `embedding_result`, `embedding_routing_shortcut_enabled`,
      `embedding_strong_similarity_threshold` 파라미터 추가 (모두 기본값 有 → 하위 호환)
  - `app/services/analysis_service.py`
    - 3번 단계 주석에 "pHash → DINOv2/CLIP 임베딩 → 3-LLM" 흐름 명시
    - `build_embedding()` 호출에 `settings` 명시적으로 전달
    - 8번 단계 `decide_routing()` 호출에 `embedding_analysis` 결과 전달
      → quick 모드 + 옵트인 시, 임베딩이 이미 라벨링된 이미지와 거의
      동일하다고 판단되면 3-LLM 호출 생략 가능
- 정리한 흐름: `pHash 생성 → DINOv2/CLIP 임베딩 → (게이팅) → 3-LLM 앙상블`
  (임베딩 결과가 라우팅 판단에 실제로 쓰이도록 연결됨)
- 추가 탐지 레이어 설계:
  - `Imalytix_추가탐지레이어_설계안.md` 신규 작성
    - 픽셀(공간) 기반 NPR(CVPR 2024), 주파수(FFT) 기반, 생성모델 지문
      기반 세 레이어의 원리/강약점/aggregator 반영 방식/데이터셋/로드맵 정리
  - 대응 스텁 파일 3개 추가(기존 sightengine/reality_defender 스텁과 동일 패턴):
    - `app/services/ai_detectors/npr_pixel_service.py`
    - `app/services/ai_detectors/frequency_spectrum_service.py`
    - `app/services/ai_detectors/generator_fingerprint_service.py`
  - 아직 `analysis_service.py`의 실제 provider 호출에는 연결하지 않음(설계 단계)
- 검증:
  - 이 세션의 샌드박스 환경에서 mount 동기화 이슈로 수정된 기존 파일이
    bash에서 즉시 반영되지 않는 문제가 있어(신규 파일 생성은 정상 동기화),
    변경된 파일 4개(`config.py`, `embedding_service.py`, `router_policy.py`,
    `analysis_service.py`)를 별도 임시 디렉터리에 동일 내용으로 재구성해
    `pytest`를 실행함
  - 결과: `30 passed` (기존 테스트 전부 통과, Pillow `getdata` deprecation
    경고만 존재하며 이번 변경과 무관)
  - 로컬 개발 환경에서 다시 한번 `python -m pytest -q`로 재확인 권장
- 다음 작업:
  - `EMBEDDING_MODEL_BACKEND=real`로 전환 후 실제 다운로드/추론 지연시간 실측
  - `data/embedding_store.sqlite3`의 기존 baseline 벡터는 차원이 달라 실모델
    벡터와 비교되지 않음(코사인 유사도가 0으로 처리되어 안전하지만 무의미한
    행이 쌓여있는 상태) → 재생성 또는 마이그레이션 필요
  - `Imalytix_추가탐지레이어_설계안.md` 로드맵 1단계(주파수 레이어 프로토타입)부터 착수
  - 임베딩 라우팅 숏컷(`EMBEDDING_ROUTING_SHORTCUT_ENABLED`)은 팀 검토 후 on/off 결정
