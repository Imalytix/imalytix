export type Confidence = "low" | "medium" | "high";
export type Severity = "low" | "medium" | "high";

export interface BBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Evidence {
  type: string;
  label: string;
  severity: Severity;
  description: string;
}

export interface SuspiciousRegion {
  label: string;
  severity: Severity;
  description: string;
  bbox?: BBox | null;
}

export interface VisionResult {
  provider: string;
  model_name?: string;
  is_ai_generated: boolean | null;
  score: number;
  confidence: Confidence;
  evidence: Evidence[];
  suspicious_regions: SuspiciousRegion[];
  limitations: string[];
  raw_response?: unknown;
  is_mock?: boolean;
  error_message?: string | null;
}

export interface DetectorResult {
  provider: string;
  detector_type?: string;
  is_ai_generated: boolean | null;
  score: number;
  confidence: Confidence;
  raw_response?: unknown;
}

export interface MetadataAnalysis {
  exif_found?: boolean;
  png_metadata_found?: boolean;
  c2pa_found?: boolean;
  ai_tool_detected?: boolean;
  detected_tools?: string[];
  detected_tool?: string;
  metadata_score?: number;
  evidence?: string[];
  limitations?: string[];
  raw?: Record<string, unknown>;
}

export interface FinalResult {
  is_ai_generated: boolean | null;
  ai_probability: number;
  label: string;
  confidence: Confidence;
}

export interface AnalysisInput {
  type?: string;
  mime_type?: string;
  width?: number;
  height?: number;
  phash?: string;
}

export interface AnalysisResult {
  product: string;
  request_id: string;
  mode: string;
  input?: AnalysisInput;
  final_result: FinalResult;
  metadata_analysis?: MetadataAnalysis;
  detector_results: DetectorResult[];
  vision_results: VisionResult[];
  evidence_summary: string[];
  suspicious_regions: SuspiciousRegion[];
  limitations: string[];
  recommended_action: string;
}

