import type { AnalysisResult } from "../types/analysis";
import { sampleImageDataUrl } from "./sampleImage";

export const sampleAnalysisResult: AnalysisResult = {
  product: "Imalytix",
  request_id: "req_mock_001",
  mode: "standard",
  input: {
    type: "file_upload",
    mime_type: "image/jpeg",
    width: 1024,
    height: 768,
    phash: "f0e1d2c3b4a59687",
  },
  final_result: {
    is_ai_generated: true,
    ai_probability: 87,
    label: "AI 생성물 가능성 높음",
    confidence: "high",
  },
  metadata_analysis: {
    exif_found: true,
    png_metadata_found: false,
    c2pa_found: false,
    ai_tool_detected: true,
    detected_tools: ["Midjourney"],
    metadata_score: 35,
    evidence: ["EXIF Software 태그에서 Midjourney 흔적이 확인되었습니다."],
    limitations: ["메타데이터는 수정 가능하므로 단독 판정 근거로 사용하지 않습니다."],
    raw: {},
  },
  detector_results: [
    {
      provider: "Sightengine",
      detector_type: "ai_generated_image",
      is_ai_generated: true,
      score: 0.92,
      confidence: "high",
    },
  ],
  vision_results: [
    {
      provider: "OpenAI",
      model_name: "gpt-4.1-mini",
      is_ai_generated: true,
      score: 0.88,
      confidence: "high",
      evidence: [
        {
          type: "background",
          label: "꽃나무 군집 경계",
          severity: "high",
          description: "꽃이 빽빽한 구간에서 가지와 하늘 경계가 다소 매끈하게 이어집니다.",
        },
        {
          type: "texture",
          label: "꽃잎 텍스처 반복",
          severity: "medium",
          description: "꽃잎 군집의 미세 패턴이 일정한 간격으로 반복되는 부분이 보입니다.",
        },
      ],
      suspicious_regions: [
        {
          label: "오른쪽 나무줄기",
          severity: "high",
          description: "나무줄기와 꽃가지가 만나는 경계가 지나치게 매끈하게 이어져 보입니다.",
          bbox: {
            x1: 0.62,
            y1: 0.45,
            x2: 0.84,
            y2: 0.76,
          },
        },
        {
          label: "하늘과 전선 부근",
          severity: "medium",
          description: "하늘과 전선이 만나는 구간에서 직선과 원근이 다소 부자연스럽게 보입니다.",
          bbox: {
            x1: 0.08,
            y1: 0.15,
            x2: 0.42,
            y2: 0.45,
          },
        },
      ],
      limitations: ["벚꽃처럼 세밀한 장면은 압축이나 리사이즈에 따라 경계 판단이 흔들릴 수 있습니다."],
    },
    {
      provider: "Gemini",
      model_name: "gemini-2.5-flash",
      is_ai_generated: null,
      score: 0.54,
      confidence: "low",
      evidence: [
        {
          type: "other",
          label: "결정적 이상 징후 부족",
          severity: "low",
          description: "벚꽃 사진의 자연스러운 요소가 많아 단정적 판단 근거는 부족합니다.",
        },
      ],
      suspicious_regions: [],
      limitations: ["추가 고해상도 분석이나 원본 이미지 확인이 있으면 더 안정적으로 판단할 수 있습니다."],
    },
  ],
  evidence_summary: [
    "메타데이터에서는 EXIF Software 태그에 AI 생성 도구 흔적이 확인되었습니다.",
    "OpenAI Vision은 전체 장면의 경계, 반복 질감, 원근감 일관성을 종합적으로 점검했습니다.",
    "Sightengine 전용 탐지기는 높은 AI 생성 가능성 점수를 반환했습니다.",
    "Gemini는 결정적 근거가 부족해 보수적인 판단을 유지했습니다.",
  ],
  suspicious_regions: [
    {
      label: "오른쪽 나무줄기",
      severity: "high",
      description: "나무줄기와 꽃가지가 만나는 경계가 지나치게 매끈하게 이어져 보입니다.",
      bbox: {
        x1: 0.62,
        y1: 0.45,
        x2: 0.84,
        y2: 0.76,
      },
    },
    {
      label: "하늘과 전선 부근",
      severity: "medium",
      description: "하늘과 전선이 만나는 구간에서 직선과 원근이 다소 부자연스럽게 보입니다.",
      bbox: {
        x1: 0.08,
        y1: 0.15,
        x2: 0.42,
        y2: 0.45,
      },
    },
  ],
  limitations: [
    "AI 생성 여부는 100% 단정할 수 없습니다.",
    "SNS나 메신저를 거친 이미지는 메타데이터가 제거되었을 수 있습니다.",
  ],
  recommended_action:
    "분석 결과는 참고용입니다. 원본 사진과 출처를 함께 확인하면 더 정확합니다.",
};

export const samplePreviewImage = sampleImageDataUrl;
