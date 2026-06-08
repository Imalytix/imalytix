# Imalytix Backend MVP

Frontend MVP is located in [`imalytix-frontend/`](./imalytix-frontend).

Imalytix는 AI 생성 이미지 여부를 판단하기 위해 단일 AI 모델의 판단에만 의존하지 않습니다.

먼저 EXIF, PNG metadata 등 이미지 내부 정보를 분석하고, 이후 OpenAI Vision API를 이용해 손가락 구조, 배경 왜곡, 문자 오류, 조명 불일치, 반복 텍스처 등 시각적 단서를 분석합니다.

마지막으로 Aggregator가 메타데이터 점수, Vision 모델 점수, 시각적 근거 점수를 통합하여 최종 AI 생성 가능성과 판단 근거를 반환합니다.

Imalytix의 결과는 확률적 분석 결과이며, 100% 판정이 아닙니다.

## Run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

## Endpoints

```text
GET /api/v1/health
POST /api/v1/analyze/image
POST /api/v1/analyze/image-url
```

## Notes

- `POST /api/v1/analyze/image-url` has SSRF protection for private, loopback, link-local, metadata, and non-http(s) targets.
- If `OPENAI_API_KEY` is missing and the request needs a vision call, the API returns a clear `503` error.
- If you want to prototype without keys, set `MOCK_VISION_FALLBACK=true` in `.env` and the Vision step will return a deterministic mock response.
- The MVP keeps interface stubs for C2PA, OCR, Redis, PostgreSQL, Claude, Gemini, Hive, Sightengine, and Reality Defender.
