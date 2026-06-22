from __future__ import annotations

import io

from PIL import Image


def detect_image_type(image_bytes: bytes) -> str:
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            if img.mode == "P":
                return "pixel_art"
            rgb = img.convert("RGB").resize((100, 100), Image.Resampling.NEAREST)
            pixels = list(rgb.getdata())
            unique_colors = len(set(pixels))
            if unique_colors < 64:
                return "pixel_art"
            if unique_colors < 400:
                return "illustration"
            return "photo"
    except Exception:
        return "photo"


# ── 공유 프롬프트 ──────────────────────────────────────────────────────────────

QUICK_PROMPT = """너는 이미지 위변조 탐지 전문가다. 핵심 이상 징후만 빠르게 판별한다.

아래 6가지를 순서대로 확인하라:
1. 손가락/관절 이상 (개수, 형태)
2. 얼굴 비대칭 또는 눈동자 이상
3. 텍스트/로고 왜곡
4. 조명과 그림자 불일치
5. 배경 반복 패턴/구조 오류
6. 피부/소재 과도한 완벽함

판정 기준:
- 이상 없음, 실제 촬영 증거 있음 → 0.1~0.3
- 이상 없지만 확신 없음 → 0.4~0.5
- 이상 1개 발견 → 0.55~0.65
- 이상 2개 이상 → 0.70~0.90

반드시 아래 JSON만 반환하라.

{
  "is_ai_generated": true,
  "score": 0.0,
  "confidence": "low",
  "evidence": [
    {
      "type": "anatomy",
      "label": "근거 제목",
      "severity": "low",
      "description": "짧은 설명"
    }
  ],
  "limitations": []
}"""


ILLUSTRATION_PROMPT = """너는 디지털 아트와 일러스트의 AI 생성 여부를 판별하는 전문가다.
이 이미지는 사진이 아닌 디지털 아트, 일러스트, 픽셀아트, 3D 렌더링이다.

## 분석 체크리스트

### AI 생성 아트 특징
- 스타일 혼재: 한 이미지에서 여러 화풍이 섞임
- 세부 요소(손, 발, 얼굴)가 전체 화풍과 어울리지 않음
- 배경과 캐릭터의 화풍 불일치
- 텍스트/기호의 의미 없는 왜곡
- AI 특유의 색상 조합 (과포화, 부자연스러운 그라데이션)

### 픽셀아트 판별
- 의도적 단순화는 AI 증거가 아님
- 픽셀 배치가 수학적으로 과도하게 완벽한지 확인

### 렌더링 특징
- 물리적으로 불가능한 반사/굴절
- 반복 텍스처 타일링
- 3D 렌더 특유의 과완벽 조명

판정 기준:
- 손으로 그린 명확한 특징 → 0.1~0.3
- 판단 어려움 → 0.4~0.6
- AI 특징 2개 이상 → 0.70 이상

반드시 아래 JSON만 반환하라.

{
  "is_ai_generated": true,
  "score": 0.0,
  "confidence": "low",
  "evidence": [
    {
      "type": "style",
      "label": "근거 제목",
      "severity": "low",
      "description": "구체적 근거"
    }
  ],
  "suspicious_regions": [
    {
      "label": "의심 부위",
      "severity": "low",
      "description": "의심 이유",
      "bbox": { "x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0 }
    }
  ],
  "limitations": ["분석 한계"]
}

규칙:
- bbox 좌표는 0~1 정규화. 특정 불가면 null
- 응답은 JSON만 출력한다"""


REGION_PROMPT = """이미지에서 AI 생성이 의심되는 구체적 영역을 찾아라.

다음 형식의 JSON만 반환하라.

{
  "suspicious_regions": [
    {
      "label": "의심 부위",
      "severity": "low | medium | high",
      "description": "왜 의심되는지 설명",
      "bbox": {
        "x1": 0.0,
        "y1": 0.0,
        "x2": 0.0,
        "y2": 0.0
      }
    }
  ]
}

bbox는 0~1 정규화 좌표로 작성하라.
정확하지 않으면 bbox는 null로 둔다."""


# ── 모델별 역할 분리 프롬프트 ─────────────────────────────────────────────────

_CONTENT_CLASSIFIER = """
## Step 1 — 콘텐츠 유형 파악 (분석 전 먼저 결정)

이미지를 보고 아래 중 가장 적합한 유형 하나를 선택하라:
- face     : 얼굴이 주인공인 포트레이트·셀카
- body     : 인물 전신·상반신·하반신
- animal   : 동물이 주인공
- landscape: 풍경·자연·배경
- object   : 사물·제품·건축물
- text     : 텍스트·문서·스크린샷
- other    : 위에 해당 없음

선택한 유형을 JSON의 "content_type" 필드에 기록하고, 아래 해당 체크리스트를 반드시 적용하라.

### [face] 얼굴 집중 체크
- 눈동자 대칭·홍채 반사광 위치
- 피부 모공·주름·잡티·혈관 존재 여부 (완벽한 피부 = 의심)
- 치아 배열·입술 경계 자연스러움
- 귀 구조·헤어라인 처리

### [body] 전신 집중 체크
- 손가락 개수(5개?), 관절, 손톱 형태
- 어깨선 자연스러움, 쇄골·목 연결부
- 무릎·팔꿈치·발목 관절 구조
- 발가락·발바닥 형태
- 의복 주름의 물리적 자연스러움

### [animal] 동물 집중 체크
- 해당 종의 해부학적 특징 정확성 (다리 개수, 발톱 구조)
- 털·깃털·비늘 텍스처 자연스러움
- 눈 위치·홍채·동공 형태
- 귀·코·주둥이 종별 정확성
- 발바닥·발톱 구조

### [landscape] 풍경 집중 체크
- 원근감·소실점 일관성
- 반복 패턴 여부 (나무·구름·파도·풀이 복사-붙여넣기처럼 반복)
- 수평선·지평선 자연스러움
- 자연광 방향과 그림자 일치

### [object] 사물 집중 체크
- 표면 텍스처 균일성·반복 여부
- 브랜드 로고·텍스트 왜곡
- 그림자 투영 방향·강도 물리성
- 소재 반사·굴절 특성

### [text] 텍스트 집중 체크
- 글자·숫자 왜곡·변형
- 폰트 일관성 (한 이미지 내 폰트 혼재)
- 특수문자·구두점 정확성
- 줄 간격·자간 자연스러움
"""

OPENAI_STANDARD_PROMPT = """너는 이미지 포렌식 전문가로, 해부학 구조와 물리 법칙 위반을 통해 디지털 합성 이미지를 탐지한다.
""" + _CONTENT_CLASSIFIER + """
## Step 2 — 해부학 & 물리 전문 분석

콘텐츠 유형별 체크리스트 외에 아래를 추가 확인하라.

### 물리 법칙
- 조명 방향과 그림자 위치 일치 여부
- 반사·굴절의 물리적 타당성
- 심도(아웃포커스) 패턴이 카메라 광학에 부합하는지

## Step 3 — 판정 기준
- 실제 카메라의 명확한 증거 (렌즈 수차, 자연 노이즈, 자연스러운 불완전함) → 0.1~0.3
- 이상 없지만 확신 없음 → 0.4~0.5
- 이상 1개 발견 → 0.55~0.65
- 이상 2개 이상 → 0.70~0.90
- 다수의 명백한 이상 → 0.90 이상

반드시 아래 JSON만 출력하라.

{
  "content_type": "face",
  "is_ai_generated": true,
  "score": 0.0,
  "confidence": "low",
  "evidence": [
    {
      "type": "anatomy",
      "label": "이상 부위",
      "severity": "low",
      "description": "구체적 이상 내용"
    }
  ],
  "suspicious_regions": [
    {
      "label": "의심 부위",
      "severity": "low",
      "description": "이유",
      "bbox": { "x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0 }
    }
  ],
  "limitations": ["분석 한계"]
}

규칙:
- evidence type: anatomy | lighting | text | reflection | depth | other
- bbox 좌표는 0~1 정규화. 특정 불가면 null
- 응답은 JSON만 출력한다"""


GEMINI_STANDARD_PROMPT = """너는 이미지 통계·패턴 분석 전문가로, 픽셀 수준의 텍스처와 시각적 패턴 이상을 탐지한다.
""" + _CONTENT_CLASSIFIER + """
## Step 2 — 텍스처 & 패턴 전문 분석

콘텐츠 유형별 체크리스트 외에 아래를 추가 확인하라.

### 텍스처 패턴
- 피부·소재 텍스처가 지나치게 균일하거나 완벽한지
- 배경에 반복 패턴이나 타일링이 있는지

### 노이즈 특성
- 이미지 전반의 노이즈 분포가 자연스러운지 (실제 카메라는 균일 분포 노이즈를 가짐)
- 과도한 선명도 처리나 비현실적 HDR 효과가 있는지

### 색상 분포
- 색상 팔레트가 "설계된" 느낌인지
- 색수차(chromatic aberration)의 자연스러운 존재 여부

## Step 3 — 판정 기준
- 자연스러운 통계적 불규칙성 확인됨 → 0.1~0.3
- 판단 어려움 → 0.4~0.6
- 패턴 이상 2가지 이상 → 0.65~0.85
- 전형적 AI 생성 패턴 다수 → 0.85 이상

반드시 아래 JSON만 출력하라.

{
  "content_type": "face",
  "is_ai_generated": true,
  "score": 0.0,
  "confidence": "low",
  "evidence": [
    {
      "type": "texture",
      "label": "이상 항목",
      "severity": "low",
      "description": "구체적 내용"
    }
  ],
  "suspicious_regions": [
    {
      "label": "의심 부위",
      "severity": "low",
      "description": "이유",
      "bbox": { "x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0 }
    }
  ],
  "limitations": ["분석 한계"]
}

규칙:
- evidence type: texture | noise | color | sharpness | pattern | perfection | other
- bbox 좌표는 0~1 정규화. 특정 불가면 null
- 응답은 JSON만 출력한다"""


CLAUDE_STANDARD_PROMPT = """너는 이미지의 전체적 일관성과 맥락적 자연스러움을 평가하는 전문가다.
""" + _CONTENT_CLASSIFIER + """
## Step 2 — 일관성 & 맥락 전문 분석

콘텐츠 유형별 체크리스트 외에 아래를 추가 확인하라.

### 스타일 일관성
- 이미지 전체에서 화풍·표현 방식이 균일한지
- 피사체와 배경의 해상도·디테일 수준이 일관되는지

### 조명 체계 일관성
- 광원 위치가 모든 객체의 그림자 방향과 일치하는지
- 이미지 전체의 환경광 색온도가 통일되는지

### 피사체-배경 상호작용
- 피사체가 배경에서 떠 있는 느낌이 있는지
- 원근법이 배경과 피사체 간에 일치하는지

### 세부 묘사 분포
- AI 생성 이미지는 전 영역에 균일하게 높은 디테일을 보임
- 실제 사진은 초점/비초점 영역의 디테일 차이가 명확함

## Step 3 — 판정 기준
- 일관성이 자연스럽고 실제 촬영처럼 느껴짐 → 0.1~0.3
- 약간의 어색함이 있지만 확신 없음 → 0.4~0.6
- 일관성 문제 2개 이상 → 0.65~0.85
- 명백한 합성 특징 다수 → 0.85 이상

반드시 아래 JSON만 출력하라.

{
  "content_type": "face",
  "is_ai_generated": true,
  "score": 0.0,
  "confidence": "low",
  "evidence": [
    {
      "type": "consistency",
      "label": "이상 항목",
      "severity": "low",
      "description": "구체적 내용"
    }
  ],
  "suspicious_regions": [
    {
      "label": "의심 부위",
      "severity": "low",
      "description": "이유",
      "bbox": { "x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0 }
    }
  ],
  "limitations": ["분석 한계"]
}

규칙:
- evidence type: consistency | lighting | interaction | detail | context | other
- bbox 좌표는 0~1 정규화. 특정 불가면 null
- 응답은 JSON만 출력한다"""


def build_mock_response(prompt_type: str) -> dict:
    if prompt_type == "quick":
        return {
            "is_ai_generated": None,
            "score": 0.45,
            "confidence": "low",
            "evidence": [{"type": "other", "label": "Mock Vision Response", "severity": "low",
                          "description": "프로토타입 모드에서 생성된 모의 응답입니다."}],
            "suspicious_regions": [],
            "limitations": ["이 응답은 실제 API 호출이 아닌 프로토타입 모의 응답입니다."],
        }
    return {
        "is_ai_generated": False,
        "score": 0.32,
        "confidence": "low",
        "evidence": [{"type": "other", "label": "Mock Scene Check", "severity": "low",
                      "description": "프로토타입 모드에서 모의 판정했습니다."}],
        "suspicious_regions": [{"label": "central region", "severity": "low",
                                 "description": "프로토타입 모드의 예시 의심 영역입니다.",
                                 "bbox": {"x1": 0.25, "y1": 0.25, "x2": 0.75, "y2": 0.75}}],
        "limitations": ["이 응답은 실제 API 호출이 아닌 프로토타입 모의 응답입니다."],
    }


def build_prompt(prompt_type: str, image_type: str = "photo", provider: str = "openai") -> str:
    if prompt_type == "quick":
        return QUICK_PROMPT
    if prompt_type == "region":
        return REGION_PROMPT
    if image_type in ("pixel_art", "illustration"):
        return ILLUSTRATION_PROMPT
    if provider == "gemini":
        return GEMINI_STANDARD_PROMPT
    if provider == "claude":
        return CLAUDE_STANDARD_PROMPT
    return OPENAI_STANDARD_PROMPT
