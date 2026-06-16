import type { AnalysisResult } from "../types/analysis";

const DEFAULT_API_URL = "http://localhost:8000/api/v1";

async function getApiUrl(): Promise<string> {
  return new Promise((resolve) => {
    chrome.storage.sync.get({ apiUrl: DEFAULT_API_URL }, (res) => {
      resolve((res.apiUrl as string) || DEFAULT_API_URL);
    });
  });
}

export async function analyzeImageFile(file: File): Promise<AnalysisResult> {
  const apiUrl = await getApiUrl();
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", "standard");
  formData.append("include_child_risk", "true");
  formData.append("return_bbox", "true");

  const res = await fetch(`${apiUrl}/analyze/image`, { method: "POST", body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<AnalysisResult>;
}

export async function analyzeImageUrl(imageUrl: string): Promise<AnalysisResult> {
  const apiUrl = await getApiUrl();
  const res = await fetch(`${apiUrl}/analyze/image-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_url: imageUrl, mode: "standard", include_child_risk: true, return_bbox: true }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<AnalysisResult>;
}
