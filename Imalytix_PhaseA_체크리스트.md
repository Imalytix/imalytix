# Imalytix Phase A 체크리스트

이 문서는 "이미지 도용 탐지"와 "이미지 위조 탐지"를 분리한 뒤, 최종적으로 신뢰성 점수로 합치는 구조를 Phase A 관점에서 정리한 실행 체크리스트다.

## 현재 완료 상태

| 항목 | 상태 | 메모 |
|---|---|---|
| FastAPI 서버 | 완료 | `/api/v1/health`, `/api/v1/analyze/image`, `/api/v1/analyze/image-url` 동작 |
| 이미지 전처리 | 완료 | 리사이즈, pHash 생성 포함 |
| EXIF / PNG metadata 분석 | 완료 | AI 도구 흔적, prompt, workflow 탐지 |
| pHash 저장소 | 완료 | SQLite 기반 cache/store 구현 |
| 도용 탐지 기초 | 완료 | 동일/유사 pHash, URL/파일명 패턴, 출처 신호 반영 |
| 위조 탐지 기초 | 완료 | metadata, Vision evidence, detector score 반영 |
| 신뢰도 점수화 | 완료 | `trust_score`, `combined_risk_score` 산출 |
| 프론트 UI | 완료 | 업로드, 결과, 상세 화면 동작 |
| Chrome Extension | 완료 | build 및 sidepanel 결과 표시 가능 |
| pHash 기반 캐시 | 완료 | 동일 이미지 재분석 회피 가능 |

## Phase A에서 아직 남은 것

| 우선순위 | 항목 | 이유 |
|---|---|---|
| P0 | 이미지 유사도 벡터 저장소 설계 | 단순 pHash보다 더 넓은 재사용/도용 패턴 추적 필요 |
| P0 | DINOv2 또는 CLIP embedding 비교 | 같은 장면의 재업로드, 크롭, 리사이즈 탐지 강화 |
| P0 | pgvector 또는 유사 벡터 DB 연결 | 대규모 유사 이미지 검색을 위한 저장 계층 필요 |
| P1 | benchmark 데이터셋 정리 | 정확도/재현율 측정 기준이 필요 |
| P1 | benchmark report 생성기 | DINOv2 vs CLIP, kNN vs linear probe 비교용 |
| P1 | source attribution 신호 강화 | 출처 URL, 도메인, CDN, 재업로드 흔적 정교화 |
| P2 | 외부 이미지 검색 연동 인터페이스 | TinEye / Google Vision Web Detection 추후 연결 대비 |
| P2 | 모델 선택 정책 정교화 | 비용과 정확도의 균형 조정 |

## 바로 다음 실행 순서

1. `embedding_service.py` 또는 동등한 모듈 추가
2. `vector_store` 인터페이스 정의
3. pHash와 embedding을 함께 쓰는 1차 후보군 검색 구현
4. 벤치마크 데이터 포맷 정의
5. benchmark 실행 결과를 MD로 남기기

## 현재 원칙

- LLM은 최종 설명과 요약에만 쓴다.
- 판별 핵심은 pHash, embedding, source pattern, metadata다.
- 비용이 드는 작업은 승인 전까지 최소화한다.
- 개인정보/원본 이미지 저장은 하지 않는다.

## 2026-07-05 1차 착수 결과

- embedding baseline 서비스 구현 완료
- SQLite vector store 구현 완료
- source attribution 서비스 구현 완료
- benchmark 실행 스크립트 및 리포트 생성 완료
- 현재 benchmark는 DINOv2/CLIP 실모델이 아니라 교체 가능한 baseline adapter로 동작
