# Imalytix — Developer Guide

> **Date**: 2026-06-21  
> **Purpose**: Onboarding document for new developers  
> **Status**: Local development in progress (v0.x)

---

## 1. Project Overview

**Imalytix** is a service that automatically detects and analyzes AI-generated images.  
It helps users identify AI-synthesized images (deepfakes, fake portrait photos, etc.) increasingly spreading across social media, communities, and news platforms.

### Core Features
| Feature | Description |
|---------|-------------|
| AI Image Detection | Multi-model Vision LLM ensemble to determine AI-generation likelihood |
| Upload / URL Analysis | Direct file upload or image URL input |
| Metadata Analysis | EXIF, C2PA, AI tool trace detection |
| Suspicious Region Visualization | Bbox overlay highlighting suspicious areas on the image |
| Content Type Recognition | Dedicated analysis per type: face/body/animal/landscape/object/text |
| Browser Extension | Instant analysis via Chrome/Edge side panel |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Client Layer                       │
│                                                         │
│  imalytix-frontend (React 19 + Vite)                    │
│  imalytix-extension (Chrome/Edge MV3)                   │
│                                                         │
│  Both → POST /api/v1/analyze/image (FormData or JSON)   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────┐
│               FastAPI Backend (Python 3.13)              │
│                                                         │
│  ┌─────────────┐    ┌──────────────────────────────┐   │
│  │router_policy│    │     analysis_service.py      │   │
│  │decide_routing│──▶│    Pipeline Orchestrator     │   │
│  └─────────────┘    └──────────────────────────────┘   │
│                               │                        │
│            ┌──────────────────┼──────────────────┐     │
│            ▼                  ▼                  ▼     │
│  ┌─────────────────┐ ┌──────────────┐ ┌────────────┐  │
│  │  Vision Models  │ │AI Detectors  │ │ Aux Service│  │
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
│  │  metadata + detector + vision → final score      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

### Backend
| Item | Details |
|------|---------|
| Language | Python 3.13 |
| Framework | FastAPI + Uvicorn |
| Config Management | Pydantic-settings (`.env`) |
| Image Processing | Pillow |
| Vision LLM | OpenAI gpt-4.1-mini / Google gemini-2.5-flash / Claude claude-haiku-4-5 |
| AI Detector | Hive AI (code complete, V2 Project Key required) |
| Virtual Environment | `.venv` (pip) |

### Frontend
| Item | Details |
|------|---------|
| Framework | React 19 + TypeScript + Vite |
| Styling | Tailwind CSS |
| State Management | React hooks (no external state library) |
| API Communication | fetch (`imalytixApi.ts`) |

### Browser Extension
| Item | Details |
|------|---------|
| Target | Chrome / Edge (Manifest V3) |
| Build | Vite (`imalytix-extension/dist/` build output) |
| How It Works | Side panel sends current page image URL to backend |

---

## 4. Directory Structure

```
project-root/
├── .env                           ← API keys (DO NOT commit to Git!)
│
├── app/                           ← FastAPI application
│   ├── main.py                    ← FastAPI entry point, CORS config
│   ├── config.py                  ← Environment variable Settings class
│   ├── state.py                   ← Runtime state (per-model success/fail count)
│   │
│   ├── routers/
│   │   ├── analyze.py             ← POST /api/v1/analyze/image, /url
│   │   └── health.py              ← GET /health
│   │
│   ├── schemas/
│   │   ├── model_result.py        ← VisionModelResult, EvidenceItem, SuspiciousRegion
│   │   ├── response.py            ← AnalysisResponse (final API response schema)
│   │   ├── request.py             ← Request parameter schema
│   │   └── metadata.py            ← Metadata analysis result schema
│   │
│   ├── services/
│   │   ├── analysis_service.py    ← Core pipeline orchestrator
│   │   ├── router_policy.py       ← Routing decision (which models to call)
│   │   ├── aggregator_service.py  ← Model results → final score aggregation
│   │   ├── model_normalizer.py    ← LLM raw response → VisionModelResult
│   │   │
│   │   ├── vision_models/
│   │   │   ├── prompts.py         ← All prompt definitions (role-separated per model)
│   │   │   ├── openai_service.py
│   │   │   ├── gemini_service.py
│   │   │   └── claude_service.py
│   │   │
│   │   ├── ai_detectors/
│   │   │   ├── hive_service.py           ← Hive AI (V2 key required)
│   │   │   ├── sightengine_service.py    ← Stub (unused)
│   │   │   └── reality_defender_service.py ← Stub (unused)
│   │   │
│   │   ├── metadata_service.py    ← EXIF / AI tool name detection
│   │   ├── c2pa_service.py        ← C2PA signature verification
│   │   ├── ocr_service.py         ← Text extraction from images
│   │   ├── phash_service.py       ← Perceptual hash generation
│   │   ├── image_loader.py        ← Image bytes → PIL + validation
│   │   ├── image_preprocess.py    ← 1024px resize + JPEG normalization
│   │   ├── image_downloader.py    ← URL download + SSRF defense
│   │   └── source_pattern_service.py ← AI CDN detection via URL patterns
│   │
│   ├── constants/
│   │   ├── scoring.py             ← Score thresholds, weights, labels
│   │   ├── ai_keywords.py         ← AI tool keyword list
│   │   └── mime_types.py          ← Allowed MIME types
│   │
│   └── utils/
│       ├── bbox.py                ← Bbox coordinate normalization + validation
│       ├── json_parser.py         ← JSON extraction from LLM responses
│       ├── errors.py              ← Custom exception classes
│       ├── logger.py              ← Logging configuration
│       └── security.py            ← SSRF defense, URL validation
│
├── imalytix-frontend/             ← React web app
│   └── src/
│       ├── pages/                 ← UploadAnalysisPage, DetailAnalysisPage, DevDashboardPage
│       ├── components/
│       │   ├── detail/            ← ImageCanvasWithBoxes, SuspiciousRegionList, EvidencePanel
│       │   ├── results/           ← ScoreGauge, ProviderResultCard, AggregatedResultSummary
│       │   └── upload/            ← ImageUploader, SelectedImagePreview
│       ├── api/imalytixApi.ts     ← Backend API call functions
│       ├── types/analysis.ts      ← TypeScript type definitions
│       └── utils/                 ← bbox.ts, score.ts, storage.ts
│
├── imalytix-extension/            ← Chrome/Edge extension
│   ├── src/
│   │   ├── sidepanel/             ← Side panel UI (main interface)
│   │   ├── popup/                 ← Popup UI
│   │   └── components/            ← ScoreGauge, ProviderCard
│   └── dist/                      ← Build output (loaded into browser)
│
├── tests/                         ← pytest tests
├── scripts/                       ← Utility scripts
└── tools/                         ← Auxiliary tools (PPT generation, etc.)
```

---

## 5. Analysis Pipeline Flow

```
Image Input (file upload or URL)
        │
        ▼
[Image Validation + Preprocessing]
  - Format/size validation (max 10MB)
  - Resize to 1024px long side
  - JPEG normalization

        │
        ▼
[router_policy.decide_routing()]
  - Determines which models to call (mode + API key availability)
  - quick mode + strong metadata evidence → skips Vision models

        │
        ├──▶ [Metadata Analysis] EXIF, AI software names, C2PA → metadata score
        │
        ├──▶ [Hive AI] (when V2 Project Key present) → detector_results
        │
        ├──▶ [OpenAI GPT-4.1-mini]  anatomy & physics expert analysis
        ├──▶ [Gemini 2.5-flash]     texture & pattern & noise expert    ← parallel
        └──▶ [Claude Haiku]         consistency & context expert
                                         │
                                         ▼
                              Each model returns JSON response:
                              {
                                "content_type": "face",
                                "is_ai_generated": true,
                                "score": 0.87,
                                "confidence": "high",
                                "evidence": [...],
                                "suspicious_regions": [
                                  { "label": "fingers", "bbox": { "x1": 0.3, ... } }
                                ],
                                "limitations": [...]
                              }
                                         │
                                         ▼
                              [aggregator_service.aggregate_analysis()]
                              → Final score 0–100
                              → AnalysisResponse returned
```

---

## 6. Score Aggregation Logic

`app/services/aggregator_service.py`

| Signal | Contribution |
|--------|-------------|
| Metadata | `metadata_score` added directly |
| Hive AI | `avg_score × 25` |
| Vision models | `avg_score × multiplier(48~65)` ← 65 if sole signal, 48 if multiple |
| Visual evidence | Evidence severity sum (max 25 pts) |
| Model consensus bonus | 2 models agree AI: +16 / 3 models: +24 / real agree: -8 |
| Source pattern | AI CDN detected: +5 / trusted source: -5 |

### Final Label Criteria

| Score | Label | is_ai_generated |
|-------|-------|-----------------|
| 80+ | Very likely AI-generated | `true` |
| 60+ | Suspected AI-generated | `true` |
| 31+ | Uncertain | `null` |
| 30 or below | Likely real image | `false` |

---

## 7. Prompt Structure (3-Model Role Separation)

`app/services/vision_models/prompts.py`

All standard prompts share the common `_CONTENT_CLASSIFIER` block.

```
Step 1 — Content Type Identification
  face / body / animal / landscape / object / text / other
  → Applies content-type-specific checklist automatically

Step 2 — Model-Specific Expert Analysis (role-separated)
  OpenAI GPT : Anatomy + physics laws (fingers, lighting, reflection, depth)
  Gemini     : Texture + noise + color patterns (uniformity, repetition, HDR)
  Claude     : Style consistency + subject-background interaction

Step 3 — Judgment → JSON output
  content_type, is_ai_generated, score, confidence,
  evidence[], suspicious_regions[{bbox}], limitations[]
```

| Prompt Variable | When Used |
|----------------|----------|
| `QUICK_PROMPT` | `mode=quick` |
| `OPENAI_STANDARD_PROMPT` | `mode=deep`, `provider=openai` |
| `GEMINI_STANDARD_PROMPT` | `mode=deep`, `provider=gemini` |
| `CLAUDE_STANDARD_PROMPT` | `mode=deep`, `provider=claude` |
| `ILLUSTRATION_PROMPT` | Auto-detected pixel art / illustration |

---

## 8. Environment Variables

`.env` file (project root) — **NEVER commit to Git**

```env
# Vision LLM API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...

# AI Detector (optional)
HIVE_API_KEY=...        # V2 Project Key required (Playground key does not support AI image detection)

# Server Config
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

## 9. Local Setup

### Backend

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start server
uvicorn app.main:app --reload --port 8000

# Health check
curl http://localhost:8000/health
```

### Frontend

```bash
cd imalytix-frontend

npm install      # first time only
npm run dev      # http://localhost:5173
```

### Load Browser Extension

1. Chrome/Edge → `chrome://extensions` → Enable Developer Mode
2. "Load unpacked" → select `imalytix-extension/dist/`
3. Click extension icon → Open side panel

> Backend (`localhost:8000`) must be running first for the extension to work.  
> No rebuild needed for backend-only changes. For extension UI changes, run `npm run build` then reload.

---

## 10. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Server health check |
| POST | `/api/v1/analyze/image` | Analyze uploaded image file |
| POST | `/api/v1/analyze/url` | Analyze image from URL |

### Request Parameters (multipart/form-data)

```
file        : Image file (jpg/png/webp/gif, max 10MB)
mode        : "quick" | "deep"   (default: deep)
return_bbox : true | false       (default: true)
```

### Response Structure (AnalysisResponse)

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
    "label": "Very likely AI-generated",
    "confidence": "high"
  },
  "metadata_analysis": { "metadata_score": 0, "evidence": [], "..." : "..." },
  "detector_results": [],
  "vision_results": [
    {
      "provider": "openai",
      "model_name": "gpt-4.1-mini",
      "content_type": "face",
      "score": 0.88,
      "confidence": "high",
      "evidence": [
        { "type": "anatomy", "label": "Finger distortion", "severity": "high", "description": "..." }
      ],
      "suspicious_regions": [
        { "label": "Left hand", "severity": "high", "description": "...",
          "bbox": { "x1": 0.3, "y1": 0.6, "x2": 0.5, "y2": 0.9 } }
      ],
      "limitations": ["..."]
    }
  ],
  "evidence_summary": ["Finger distortion detected", "Overly perfect skin texture"],
  "suspicious_regions": ["..."],
  "limitations": ["AI generation cannot be determined with 100% certainty.", "..."],
  "recommended_action": "This image has a high likelihood of being AI-generated. Verify the source before sharing."
}
```

---

## 11. Development Status

### Completed
- [x] FastAPI backend structure (routers, schemas, service layer)
- [x] 3-model Vision ensemble (OpenAI / Gemini / Claude)
- [x] Metadata analysis (EXIF, C2PA, AI tool name detection)
- [x] Score aggregation algorithm (weighted average + consensus bonus)
- [x] Image preprocessing pipeline (resize + JPEG normalization)
- [x] React web UI (upload / results / detailed analysis pages)
- [x] Bbox overlay visualization (numbered + color-coded suspicious regions)
- [x] Chrome/Edge browser extension (side panel)
- [x] Role-separated prompts per model
- [x] Automatic content type classification (face/body/animal/landscape/object/text)
- [x] Hive AI integration code (activates immediately upon key provisioning)
- [x] OpenAI content policy refusal auto-handling

### Planned
- [ ] Test image dataset construction
- [ ] RAG-based AI generator fingerprint DB
- [ ] Performance benchmarking (accuracy / processing speed)
- [ ] Deployment environment setup

---

## 12. Known Issues & Notes

| Item | Details |
|------|---------|
| Hive API Key | Playground V3 key does not support AI image detection. Obtain V2 Project Key from Hive dashboard Projects tab |
| Missing bbox | If a model doesn't return coordinates for a region, it won't appear on the image overlay. List shows "No location info" badge |
| OpenAI Content Policy | GPT-4 may refuse to analyze certain images → automatically handled as error |
| `.env` file | Contains API keys. **NEVER commit to Git** |
| Extension rebuild | Not required for backend-only changes. Run `npm run build` and reload for extension UI changes |

---

## 13. External Services

| Service | Purpose | Status |
|---------|---------|--------|
| OpenAI API | GPT-4.1-mini Vision analysis | Active |
| Google Gemini API | Gemini 2.5-flash Vision analysis | Active |
| Anthropic API | Claude Haiku Vision analysis | Active |
| Hive AI | Dedicated AI image detector | Code complete, awaiting V2 key |
