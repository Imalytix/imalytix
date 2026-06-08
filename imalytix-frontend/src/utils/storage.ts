import type { AnalysisResult } from "../types/analysis";

const ANALYSIS_KEY = "imalytix:lastAnalysisResult";
const IMAGE_KEY = "imalytix:lastImageDataUrl";
const HISTORY_KEY = "imalytix:history";
const HISTORY_MAX = 5;

export interface HistoryEntry {
  requestId: string;
  timestamp: number;
  label: string;
  aiProbability: number;
  mode: string;
}

export function saveAnalysisResult(result: AnalysisResult) {
  localStorage.setItem(ANALYSIS_KEY, JSON.stringify(result));
  _appendHistory(result);
}

export function loadAnalysisResult(): AnalysisResult | null {
  const raw = localStorage.getItem(ANALYSIS_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AnalysisResult;
  } catch {
    return null;
  }
}

export function saveImageDataUrl(dataUrl: string) {
  localStorage.setItem(IMAGE_KEY, dataUrl);
}

export function loadImageDataUrl(): string | null {
  return localStorage.getItem(IMAGE_KEY);
}

export function loadHistory(): HistoryEntry[] {
  const raw = localStorage.getItem(HISTORY_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as HistoryEntry[];
  } catch {
    return [];
  }
}

function _appendHistory(result: AnalysisResult) {
  const entry: HistoryEntry = {
    requestId: result.request_id,
    timestamp: Date.now(),
    label: result.final_result.label,
    aiProbability: result.final_result.ai_probability,
    mode: result.mode,
  };
  const prev = loadHistory().filter((e) => e.requestId !== entry.requestId);
  const next = [entry, ...prev].slice(0, HISTORY_MAX);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
}

export function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
}

