# Imalytix Frontend MVP

Imalytix Frontend는 백엔드 분석 결과를 카드 기반 대시보드와 상세 분석 뷰로 보여주는 React + TypeScript + Vite 앱입니다.

## Features

- 이미지 업로드 후 백엔드 `/api/v1/analyze/image` 호출
- Provider별 분석 결과 분리 표시
- Metadata 분석 카드 별도 표시
- Aggregated summary 보조 표시
- `/detail` 상세 분석 화면
- localStorage 기반 최근 결과 전달
- mock 데이터 기반 UI 테스트

## Setup

```bash
npm install
cp .env.example .env
npm run dev
```

## Environment

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Run together with backend

1. 백엔드 실행
2. 프론트 실행
3. 브라우저에서 `http://localhost:5173` 접속
4. 이미지를 업로드하고 분석 버튼을 누름
5. 상세보기 버튼으로 `/detail` 이동

## Notes

- 백엔드와 다른 포트에서 실행되므로 FastAPI CORS 설정이 필요합니다.
- 백엔드가 실행되지 않아도 샘플 데이터로 UI를 확인할 수 있습니다.

