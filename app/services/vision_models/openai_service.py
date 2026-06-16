from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image

from app.config import Settings
from app.schemas.model_result import VisionModelResult
from app.services.model_normalizer import normalize_model_result
from app.utils.errors import OpenAIServiceError
from app.utils.json_parser import extract_json_object

# ──────────────────────────────────────────────────────────────────────────────
# 이미지 타입 감지
# ──────────────────────────────────────────────────────────────────────────────

def detect_image_type(image_bytes: bytes) -> str:
    """
    픽셀 분석으로 이미지 타입 판별.
    반환값: "photo" | "illustration" | "pixel_art"
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # 팔레트 모드 → 픽셀 아트 가능성
            if img.mode == "P":
                return "pixel_art"

            rgb = img.convert("RGB").resize((100, 100), Image.Resampling.NEAREST)
            pixels = list(rgb.getdata())
            unique_colors = len(set(pixels))

            # 고유 색상 수가 매우 적으면 픽셀 아트 / 단순 일러스트
            if unique_colors < 64:
                return "pixel_art"
            if unique_colors < 400:
                return "illustration"
            return "photo"
    except Exception:
        return "photo"


# ──────────────────────────────────────────────────────────────────────────────
# 프롬프트
# ──────────────────────────────────────────────────────────────────────────────

QUICK_PROMPT = """너는 이미지 AI 생성 여부를 점검하는 보조 모델이다.

기본 원칙: score는 0.5에서 시작한다. 실제 촬영 증거가 명확할 때만 낮춰라.

이미지에서 다음 6가지를 확인하라:
1. 손/관절 이상
2. 문자/로고 왜곡
3. 배경 구조 오류
4. 빛/그림자 불일치
5. 반복 텍스처
6. 과도한 완벽함 (피부, 머리카락 등)

아래 JSON만 반환하라.

{
  "is_ai_generated": true | false | null,
  "score": 0.0,
  "confidence": "low | medium | high",
  "evidence": [
    {
      "type": "anatomy | text | background | lighting | texture | perfection | other",
      "label": "근거 제목",
      "severity": "low | medium | high",
      "description": "짧은 설명"
    }
  ],
  "limitations": []
}

근거가 부족하면 score는 0.5로 유지하고 null을 사용하라."""

STANDARD_PROMPT = """너는 Imalytix의 AI 생성 이미지 탐지 전문가다.
Midjourney, DALL-E, Stable Diffusion, FLUX, Firefly 등 최신 AI 이미지 생성 도구의 특성을 깊이 알고 있다.

## 핵심 원칙
현대 AI 이미지는 사람 눈에도 실제처럼 보인다. "자연스러워 보인다"는 것은 AI가 아니라는 증거가 아니다.
**기본 score를 0.5로 시작하고, 실제 카메라 촬영 증거가 명확할 때만 낮춰라.**

## AI 이미지의 과완벽성 신호 (가장 중요)
- 피부가 지나치게 매끄럽고 모공/잡티/혈관이 전혀 없음
- 머리카락 한 올 한 올이 비현실적으로 완벽하게 표현됨
- 눈동자가 과도하게 선명하고 광채가 완벽하게 대칭
- 전체적으로 "필터를 과도하게 쓴 것보다 더 완벽한" 느낌
- 배경이 피사체를 위해 존재하는 것처럼 너무 완벽하게 구성됨

## 해부학적 이상
- 손가락 개수/관절/길이 이상
- 귀, 치아 구조 불자연스러움
- 머리카락이 배경에 녹아들거나 경계 처리 부자연스러움

## 물리적/광학적 이상
- 조명 방향이 그림자와 불일치
- 실제 카메라로 불가능한 심도 (배경 흐림이 비물리적)
- 반사/굴절이 물리 법칙에 어긋남
- 노이즈가 없거나 균일하게 분포 (실제 사진엔 항상 노이즈 있음)

## 텍스트/배경 이상
- 글자, 숫자, 로고가 왜곡되거나 읽을 수 없음
- 배경 원근감 오류, 반복 텍스처

## 판단 기준
- score 0.7 이상: AI 생성 가능성 높음
- score 0.4~0.7: 불확실 (명확한 증거 없음)
- score 0.4 미만: 실제 촬영 증거가 명확한 경우만

반드시 아래 JSON만 출력하라.

{
  "is_ai_generated": true | false | null,
  "score": 0.0,
  "confidence": "low | medium | high",
  "evidence": [
    {
      "type": "anatomy | texture | lighting | background | text | camera | edge | symmetry | perfection | other",
      "label": "근거 제목",
      "severity": "low | medium | high",
      "description": "구체적 근거"
    }
  ],
  "suspicious_regions": [
    {
      "label": "의심 부위",
      "severity": "low | medium | high",
      "description": "의심 이유",
      "bbox": { "x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0 }
    }
  ],
  "limitations": ["분석 한계"]
}

규칙:
- score 기본값은 0.5. 실제 증거로 올리거나 내려라
- bbox 좌표는 0~1 정규화. 모르면 null
- 응답은 JSON만 출력한다"""

ILLUSTRATION_PROMPT = """너는 Imalytix의 디지털 아트 / 일러스트 AI 생성 탐지 전문 모델이다.
이 이미지는 사진이 아니라 디지털 아트, 픽셀 아트, 일러스트, 2D/3D 렌더링 등의 비사진 이미지다.

일반 사진 기준이 아닌, 디지털 아트 특성에 맞는 기준으로 AI 생성 여부를 판단하라.

## 디지털 아트·일러스트에서 AI 생성을 나타내는 단서

### AI 생성 아트의 특징 (고배점)
- 스타일이 일관되지 않음 (한 그림에서 여러 화풍이 혼재)
- 세부 요소(손, 발, 얼굴)가 전체 스타일과 어울리지 않음
- 배경과 캐릭터의 화풍 불일치
- 텍스트나 기호가 의미 없이 왜곡됨
- 색상 팔레트가 인위적으로 완벽하거나 AI 특유의 색상 조합
- 반복되는 패턴이나 대칭이 지나치게 완벽함

### 픽셀 아트 특이 사항
- 픽셀 아트는 의도적으로 단순화한 예술 형식이므로, 단순함 자체가 AI 증거는 아님
- 하지만 픽셀 아트도 Claude, Midjourney, DALL-E 등으로 생성 가능
- 픽셀 배치 패턴이 손으로 그린 것과 다르게 너무 수학적으로 완벽한지 확인
- 그림자나 하이라이트가 픽셀 아트 관례에 맞지 않는지 확인

### 렌더링 특징
- 3D 렌더링 특유의 과도하게 완벽한 조명
- 텍스처가 반복되거나 타일링됨
- 물리적으로 불가능한 반사/굴절 표현

## 핵심 판단 원칙
- 이 이미지가 AI 도구(Midjourney, DALL-E, Stable Diffusion, Claude, Firefly 등)로 생성되었을 가능성을 판단하라
- 디지털 아트이므로 "실제 사진처럼 보이는가"는 판단 기준이 아님
- AI로 생성된 디지털 아트는 대부분 score 0.7 이상임

반드시 아래 JSON만 반환하라.

{
  "is_ai_generated": true | false | null,
  "score": 0.0,
  "confidence": "low | medium | high",
  "evidence": [
    {
      "type": "style | anatomy | text | pattern | rendering | color | other",
      "label": "근거 제목",
      "severity": "low | medium | high",
      "description": "구체적 근거"
    }
  ],
  "suspicious_regions": [
    {
      "label": "의심 부위",
      "severity": "low | medium | high",
      "description": "의심 이유",
      "bbox": { "x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0 }
    }
  ],
  "limitations": ["분석 한계"]
}

규칙:
- score: 0.0(사람이 직접 그린 아트) ~ 1.0(AI 생성 아트)
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


def build_mock_response(prompt_type: str) -> dict:
    if prompt_type == "quick":
        return {
            "is_ai_generated": None,
            "score": 0.45,
            "confidence": "low",
            "evidence": [{"type": "other", "label": "Mock Vision Response", "severity": "low",
                          "description": "프로토타입 모드에서 생성된 모의 응답입니다."}],
            "suspicious_regions": [],
            "limitations": ["이 응답은 실제 OpenAI Vision 호출이 아닌 프로토타입 모의 응답입니다."],
        }
    return {
        "is_ai_generated": False,
        "score": 0.32,
        "confidence": "low",
        "evidence": [{"type": "background", "label": "Mock Scene Check", "severity": "low",
                      "description": "프로토타입 모드에서 시각적 이상 징후를 모의 판정했습니다."}],
        "suspicious_regions": [{"label": "central region", "severity": "low",
                                 "description": "프로토타입 모드의 예시 의심 영역입니다.",
                                 "bbox": {"x1": 0.25, "y1": 0.25, "x2": 0.75, "y2": 0.75}}],
        "limitations": ["이 응답은 실제 OpenAI Vision 호출이 아닌 프로토타입 모의 응답입니다."],
    }


def build_prompt(prompt_type: str, image_type: str = "photo") -> str:
    if prompt_type == "quick":
        return QUICK_PROMPT
    if prompt_type == "region":
        return REGION_PROMPT
    # standard 모드: 이미지 타입에 따라 프롬프트 선택
    if image_type in ("pixel_art", "illustration"):
        return ILLUSTRATION_PROMPT
    return STANDARD_PROMPT


async def analyze_with_openai(
    image_bytes: bytes,
    mime_type: str,
    prompt_type: str,
    settings: Settings,
) -> VisionModelResult:
    if not settings.openai_api_key:
        if settings.mock_vision_fallback:
            return normalize_model_result(
                build_mock_response(prompt_type),
                provider="openai",
                model_name=settings.openai_vision_model,
                is_mock=True,
            )
        raise OpenAIServiceError("OPENAI_API_KEY가 설정되지 않았습니다.")

    try:
        from openai import AsyncOpenAI
    except Exception as exc:
        raise OpenAIServiceError("openai 패키지를 사용할 수 없습니다.") from exc

    # 이미지 타입 감지 → 적절한 프롬프트 선택
    image_type = detect_image_type(image_bytes)
    prompt = build_prompt(prompt_type, image_type)

    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=float(settings.request_timeout_seconds))
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{image_base64}"

    try:
        response = await client.responses.create(
            model=settings.openai_vision_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )
    except Exception as exc:
        from app.state import app_state
        app_state.record_error("openai", f"API 호출 실패: {exc}")
        return normalize_model_result(
            None,
            provider="openai",
            model_name=settings.openai_vision_model,
            error_message=f"OpenAI API 호출 실패: {exc}",
        )

    # output_text 외에 output 배열에서도 텍스트 추출 시도
    text = getattr(response, "output_text", None) or ""
    if not text:
        try:
            for item in (response.output or []):
                for content in (getattr(item, "content", None) or []):
                    t = getattr(content, "text", None)
                    if t:
                        text = t
                        break
                if text:
                    break
        except Exception:
            pass
    if not text:
        from app.state import app_state
        app_state.record_error("openai", "응답이 비어 있습니다.")
        return normalize_model_result(
            None,
            provider="openai",
            model_name=settings.openai_vision_model,
            error_message="OpenAI 응답이 비어 있습니다.",
        )

    parsed = extract_json_object(text)
    from app.state import app_state
    if parsed is not None:
        app_state.record_success("openai")
    else:
        app_state.record_error("openai", f"JSON 파싱 실패: {text[:100]}")
    return normalize_model_result(
        parsed if parsed is not None else text,
        provider="openai",
        model_name=settings.openai_vision_model,
    )
