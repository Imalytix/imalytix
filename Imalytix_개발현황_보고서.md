# Imalytix — 개발현황 보고서

> **작성일**: 2026-06-21  
> **목적**: 신규 합류 개발자 온보딩용 프로젝트 소개서  
> **현재 상태**: 로컬 개발 진행 중 (v0.x)

---

## 1. 프로젝트 개요

**Imalytix**는 AI가 생성한 이미지를 자동으로 탐지·분석하는 서비스다.  
SNS·커뮤니티·뉴스에서 급증하는 AI 합성 이미지(딥페이크, 가짜 인물 사진 등)를 사용자가 쉽게 판별할 수 있도록 돕는다.

### 핵심 기능
| 기능 | 설명 |
|------|------|
| AI 이미지 탐지 | 복수 Vision LLM 앙상블로 AI 생성 여부 판별 |
| 이미지 업로드 / URL 분석 | 파일 직접 업로드 또는 이미지 URL 입력 |
| 메타데이터 분석 | EXIF, C2PA, AI 도구 흔적 탐지 |
| 의심 영역 시각화 | Bbox 오버레이로 이미지 위 의심 영역 표시 |
| 콘텐츠 유형 인식 | face/body/animal/landscape/object/text 별 전용 분석 |
| 브라우저 확장 프로그램 | Chrome / Edge 사이드패널에서 즉시 분석 |

---

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                     클라이언트 레이어                      │
│                                                         │
│  imalytix-frontend (React 19 + Vite)                    │
│  imalytix-extension (Chrome/Edge MV3)                   │
│                                                         │
│  둘 다 → POST /api/v1/analyze/image (FormData or JSON)  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI 백엔드 (Python 3.13)             │
│                                                         │
│  ┌─────────────┐    ┌──────────────────────────────┐   │
│  │router_policy│    │     analysis_service.py      │   │
│  │decide_routing│──▶│  전체 파이프라인 오케스트레이터  │   │
│  └─────────────┘    └──────────────────────────────┘   │
│                               │                        │
│            ┌──────────────────┼──────────────────┐     │
│            ▼                  ▼                  ▼     │
│  ┌─────────────────┐ ┌──────────────┐ ┌────────────┐  │
│  │  Vision Models  │ │AI Detectors  │ │  기타 서비스 │  │
│  │ ┌─────────────┐ │ │ ┌──────────┐ │ │ metadata   │  │
│  │ │ openai_svc  │ │ │ │ hive_svc │ │ │ phash      │  │
│  │ │ gemini_svc  │ │ │ └──────────┘ │ │ c2pa       │  │
│  │ │ claude_svc  │ │ │              │ │ ocr        │  │
│  │ └─────────────┘ │ └──────────────┘ └────────────┘  │
│  └─────────────────┘                                   │
│            │                                           │
│            ▼                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │          aggregator_service.py                   │  │
│  │  메타데이터 + 탐지기 + Vision → 최종 점수 집계     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 기술 스택

### 백엔드
| 항목 | 내용 |
|------|------|
| 언어 | Python 3.13 |
| 프레임워크 | FastAPI + Uvicorn |
| 설정 관리 | Pydantic-settings (`.env`) |
| 이미지 처리 | Pillow |
| Vision LLM | OpenAI gpt-4.1-mini / Google gemini-2.5-flash / Claude claude-haiku-4-5 |
| AI 탐지기 | Hive AI (코드 완성, V2 Project Key 필요) |
| 가상환경 | `.venv` (pip) |

### 프론트엔드
| 항목 | 내용 |
|------|------|
| 프레임워크 | React 19 + TypeScript + Vite |
| 스타일 | Tailwind CSS |
| 상태 관리 | React hooks (별도 상태 라이브러리 없음) |
| API 통신 | fetch (`imalytixApi.ts`) |

### 브라우저 확장
| 항목 | 내용 |
|------|------|
| 대상 | Chrome / Edge (Manifest V3) |
| 빌드 | Vite (`imalytix-extension/dist/` 빌드 결과물) |
| 동작 방식 | 사이드패널에서 현재 페이지 이미지 URL을 백엔드로 전송 |

---

## 4. 디렉토리 구조

```
성윤/                              ← 프로젝트 루트
├── .env                           ← API 키 (Git 커밋 금지!)
│
├── app/                           ← FastAPI 애플리케이션
│   ├── main.py                    ← FastAPI 앱 진입점, CORS 설정
│   ├── config.py                  ← 환경변수 Settings 클래스
│   ├── state.py                   ← 런타임 상태 (모델별 성공/실패 카운트)
│   │
│   ├── routers/
│   │   ├── analyze.py             ← POST /api/v1/analyze/image, /url
│   │   └── health.py              ← GET /health
│   │
│   ├── schemas/
│   │   ├── model_result.py        ← VisionModelResult, EvidenceItem, SuspiciousRegion
│   │   ├── response.py            ← AnalysisResponse (최종 API 응답 스키마)
│   │   ├── request.py             ← 요청 파라미터 스키마
│   │   └── metadata.py            ← 메타데이터 분석 결과 스키마
│   │
│   ├── services/
│   │   ├── analysis_service.py    ← 핵심 파이프라인 오케스트레이터
│   │   ├── router_policy.py       ← 호출 모델 라우팅 결정
│   │   ├── aggregator_service.py  ← 각 모델 결과 → 최종 점수 집계
│   │   ├── model_normalizer.py    ← LLM raw 응답 → VisionModelResult 정규화
│   │   │
│   │   ├── vision_models/
│   │   │   ├── prompts.py         ← 모든 프롬프트 정의 (모델별 역할 분리)
│   │   │   ├── openai_service.py
│   │   │   ├── gemini_service.py
│   │   │   └── claude_service.py
│   │   │
│   │   ├── ai_detectors/
│   │   │   ├── hive_service.py           ← Hive AI (V2 키 필요)
│   │   │   ├── sightengine_service.py    ← 스텁 (미사용)
│   │   │   └── reality_defender_service.py ← 스텁 (미사용)
│   │   │
│   │   ├── metadata_service.py    ← EXIF / AI 도구명 탐지
│   │   ├── c2pa_service.py        ← C2PA 서명 확인
│   │   ├── ocr_service.py         ← 이미지 내 텍스트 추출
│   │   ├── phash_service.py       ← 지각 해시 생성 (중복 탐지용)
│   │   ├── image_loader.py        ← 이미지 바이트 → PIL + 검증
│   │   ├── image_preprocess.py    ← 장축 1024px 리사이즈 + JPEG 변환
│   │   ├── image_downloader.py    ← URL 다운로드 + SSRF 방어
│   │   └── source_pattern_service.py ← URL 패턴으로 AI CDN 판단
│   │
│   ├── constants/
│   │   ├── scoring.py             ← 점수 임계값, 가중치, 레이블
│   │   ├── ai_keywords.py         ← AI 도구 관련 키워드 목록
│   │   └── mime_types.py          ← 허용 MIME 타입 목록
│   │
│   └── utils/
│       ├── bbox.py                ← Bbox 좌표 정규화 + 유효성 검사
│       ├── json_parser.py         ← LLM 응답에서 JSON 추출
│       ├── errors.py              ← 커스텀 예외 클래스
│       ├── logger.py              ← 로깅 설정
│       └── security.py            ← SSRF 방어, URL 검증
│
├── imalytix-frontend/             ← React 웹 앱
│   └── src/
│       ├── pages/                 ← UploadAnalysisPage, DetailAnalysisPage, DevDashboardPage
│       ├── components/
│       │   ├── detail/            ← ImageCanvasWithBoxes, SuspiciousRegionList, EvidencePanel
│       │   ├── results/           ← ScoreGauge, ProviderResultCard, AggregatedResultSummary
│       │   └── upload/            ← ImageUploader, SelectedImagePreview
│       ├── api/imalytixApi.ts     ← 백엔드 API 호출 함수
│       ├── types/analysis.ts      ← TypeScript 타입 정의
│       └── utils/                 ← bbox.ts, score.ts, storage.ts
│
├── imalytix-extension/            ← Chrome/Edge 확장
│   ├── src/
│   │   ├── sidepanel/             ← 사이드패널 UI (메인 인터페이스)
│   │   ├── popup/                 ← 팝업 UI
│   │   └── components/            ← ScoreGauge, ProviderCard
│   └── dist/                      ← 빌드 결과물 (브라우저에 로드)
│
├── tests/                         ← pytest 테스트
├── scripts/                       ← 유틸리티 스크립트
└── tools/                         ← PPT 생성 등 보조 도구
```

---

## 5. 분석 파이프라인 흐름

```
이미지 입력 (파일 업로드 or URL)
        │
        ▼
[이미지 검증 + 전처리]
  - 포맷·사이즈 검증 (최대 10MB)
  - 장축 1024px 리사이즈
  - JPEG 정규화

        │
        ▼
[router_policy.decide_routing()]
  - mode (quick/deep) + API 키 보유 여부로 호출 모델 결정
  - quick mode + 강한 메타데이터 증거 → Vision 모델 건너뜀

        │
        ├──▶ [메타데이터 분석] EXIF, AI 소프트웨어명, C2PA → 메타 점수
        │
        ├──▶ [Hive AI] (V2 Project Key 있을 때) → detector_results
        │
        ├──▶ [OpenAI GPT-4.1-mini]  해부학·물리 법칙 전문 분석
        ├──▶ [Gemini 2.5-flash]     텍스처·패턴·노이즈 전문 분석  ← 병렬 실행
        └──▶ [Claude Haiku]         일관성·맥락 전문 분석
                                         │
                                         ▼
                              각 모델 JSON 응답 수신
                              {
                                "content_type": "face",
                                "is_ai_generated": true,
                                "score": 0.87,
                                "confidence": "high",
                                "evidence": [...],
                                "suspicious_regions": [
                                  { "label": "손가락", "bbox": { "x1": 0.3, ... } }
                                ],
                                "limitations": [...]
                              }
                                         │
                                         ▼
                              [aggregator_service.aggregate_analysis()]
                              → 최종 점수 0~100 산출
                              → AnalysisResponse 반환
```

---

## 6. 점수 집계 로직

`app/services/aggregator_service.py`

| 신호 | 기여 방식 |
|------|---------|
| 메타데이터 | `metadata_score` 직접 합산 |
| Hive AI | `avg_score × 25` |
| Vision 모델 | `avg_score × 배율(48~65)` ← 단독 신호면 배율 65, 복수면 48 |
| 시각 근거 | evidence severity 합산 (최대 25점) |
| 모델 합의 보너스 | 2개 AI 동의 +16 / 3개 동의 +24 / 실제 동의 -8 |
| 출처 패턴 | AI CDN 감지 +5 / 신뢰 소스 -5 |

### 최종 레이블 기준

| 점수 | 레이블 | is_ai_generated |
|------|--------|-----------------|
| 80 이상 | AI 생성 가능성 매우 높음 | `true` |
| 60 이상 | AI 생성 의심 | `true` |
| 31 이상 | 판단 불확실 | `null` |
| 30 이하 | 실제 이미지 가능성 높음 | `false` |

---

## 7. 프롬프트 구조 (3모델 역할 분리)

`app/services/vision_models/prompts.py`

모든 표준 프롬프트는 공통 `_CONTENT_CLASSIFIER` 블록을 포함한다.

```
Step 1 — 콘텐츠 유형 파악
  face / body / animal / landscape / object / text / other
  → content_type 별 전용 체크리스트 자동 적용

Step 2 — 모델별 전문 분석 (역할 분리)
  OpenAI GPT : 해부학 + 물리 법칙 (손가락, 조명, 반사, 심도)
  Gemini     : 텍스처 + 노이즈 + 색상 패턴 (균일성, 반복, HDR)
  Claude     : 스타일 일관성 + 피사체-배경 상호작용

Step 3 — 판정 → JSON 출력
  content_type, is_ai_generated, score, confidence,
  evidence[], suspicious_regions[{bbox}], limitations[]
```

| 프롬프트 변수 | 사용 시점 |
|-------------|---------|
| `QUICK_PROMPT` | `mode=quick` |
| `OPENAI_STANDARD_PROMPT` | `mode=deep`, `provider=openai` |
| `GEMINI_STANDARD_PROMPT` | `mode=deep`, `provider=gemini` |
| `CLAUDE_STANDARD_PROMPT` | `mode=deep`, `provider=claude` |
| `ILLUSTRATION_PROMPT` | 픽셀아트/일러스트 자동 감지 시 |

---

## 8. 환경 변수 설정

`.env` 파일 (루트 디렉토리) — **절대 Git에 커밋하지 말 것**

```env
# Vision LLM API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...

# AI 탐지기 (선택)
HIVE_API_KEY=...        # V2 Project Key 필요 (Playground 키는 AI 이미지 탐지 미지원)

# 서버 설정
APP_ENV=local           # local | dev | staging | prod
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=10
IMAGE_LONG_SIDE=1024
REQUEST_TIMEOUT_SECONDS=60
MOCK_VISION_FALLBACK=false

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## 9. 로컬 실행 방법

### 백엔드

```bash
# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 의존성 설치 (최초 1회)
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --port 8000

# 헬스체크
curl http://localhost:8000/health
```

### 프론트엔드

```bash
cd imalytix-frontend

npm install      # 최초 1회
npm run dev      # http://localhost:5173
```

### 브라우저 확장 로드

1. Chrome/Edge → `chrome://extensions` → 개발자 모드 ON
2. "압축 해제된 확장 프로그램 로드" → `imalytix-extension/dist/` 선택
3. 익스텐션 아이콘 클릭 → 사이드패널 열기

> 백엔드(`localhost:8000`)가 먼저 실행되어 있어야 확장이 동작한다.  
> 백엔드만 변경 시 확장 재빌드 불필요 (확장 UI 변경 시 `npm run build` 후 재로드).

---

## 10. API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 서버 상태 확인 |
| POST | `/api/v1/analyze/image` | 이미지 파일 업로드 분석 |
| POST | `/api/v1/analyze/url` | 이미지 URL 분석 |

### 요청 파라미터 (multipart/form-data)

```
file        : 이미지 파일 (jpg/png/webp/gif, 최대 10MB)
mode        : "quick" | "deep"  (default: deep)
return_bbox : true | false      (default: true)
```

### 응답 구조 (AnalysisResponse)

```json
{
  "product": "Imalytix",
  "request_id": "req_20260621_120000_abc123",
  "mode": "deep",
  "input": {
    "type": "file_upload",
    "mime_type": "image/jpeg",
    "width": 1024,
    "height": 768,
    "phash": "a1b2c3d4..."
  },
  "final_result": {
    "is_ai_generated": true,
    "ai_probability": 87,
    "label": "AI 생성 가능성 매우 높음",
    "confidence": "high"
  },
  "metadata_analysis": { "metadata_score": 0, "evidence": [], ... },
  "detector_results": [],
  "vision_results": [
    {
      "provider": "openai",
      "model_name": "gpt-4.1-mini",
      "content_type": "face",
      "score": 0.88,
      "confidence": "high",
      "evidence": [
        { "type": "anatomy", "label": "손가락 왜곡", "severity": "high", "description": "..." }
      ],
      "suspicious_regions": [
        { "label": "왼손", "severity": "high", "description": "...",
          "bbox": { "x1": 0.3, "y1": 0.6, "x2": 0.5, "y2": 0.9 } }
      ],
      "limitations": [...]
    }
  ],
  "evidence_summary": ["손가락 왜곡 발견", "피부 과완벽성"],
  "suspicious_regions": [...],
  "limitations": ["AI 생성 여부는 100% 단정할 수 없습니다.", ...],
  "recommended_action": "AI 생성 이미지일 가능성이 높으므로 출처 확인이 필요합니다."
}
```

---

## 11. 개발 현황

### 완료
- [x] FastAPI 백엔드 기본 구조 (라우터, 스키마, 서비스 레이어)
- [x] 3모델 Vision 앙상블 (OpenAI / Gemini / Claude)
- [x] 메타데이터 분석 (EXIF, C2PA, AI 도구명 탐지)
- [x] 점수 집계 알고리즘 (가중 평균 + 합의 보너스)
- [x] 이미지 전처리 파이프라인 (리사이즈 + JPEG 정규화)
- [x] React 웹 UI (업로드 / 결과 / 상세 분석 페이지)
- [x] Bbox 오버레이 시각화 (의심 영역 번호 + 색상 표시)
- [x] Chrome/Edge 확장 프로그램 (사이드패널)
- [x] 모델별 역할 분리 프롬프트
- [x] 콘텐츠 유형 자동 분류 (face/body/animal/landscape/object/text)
- [x] Hive AI 연동 코드 (키 발급 즉시 활성화 가능)
- [x] OpenAI 콘텐츠 정책 거부 자동 처리

### 진행 예정
- [ ] Hive AI V2 Project Key 발급 및 연동 완료
- [ ] 테스트 이미지 데이터셋 구축
- [ ] RAG 기반 AI 생성기 핑거프린트 DB
- [ ] 성능 벤치마킹 (정확도 / 처리 속도)
- [ ] 배포 환경 구성

---

## 12. 알려진 이슈 및 주의사항

| 항목 | 내용 |
|------|------|
| Hive API 키 | Playground V3 키는 AI 이미지 탐지 미지원. Hive 대시보드 Projects 탭에서 V2 Project Key 발급 필요 |
| bbox 누락 | 모델이 특정 region 좌표를 반환하지 않으면 이미지에 표시 안 됨. 목록에는 "위치 정보 없음" 배지로 표시 |
| OpenAI 콘텐츠 정책 | 일부 이미지에서 GPT-4가 분석 거부 가능 → 자동 에러 처리됨 |
| `.env` 파일 | API 키 포함. **절대 Git 커밋 금지** |
| 확장 재빌드 | 백엔드만 변경 시 불필요. 확장 UI 변경 시 `npm run build` 후 재로드 필요 |

---

## 13. 연동 외부 서비스

| 서비스 | 용도 | 상태 |
|--------|------|------|
| OpenAI API | GPT-4.1-mini Vision 분석 | 운영 중 |
| Google Gemini API | Gemini 2.5-flash Vision 분석 | 운영 중 |
| Anthropic API | Claude Haiku Vision 분석 | 운영 중 |
| Hive AI | 전용 AI 이미지 탐지기 | 코드 완성, V2 키 발급 대기 |
