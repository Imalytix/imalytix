import axios from "axios";
import type { AnalysisResult } from "../types/analysis";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://imalytix-backend.onrender.com/api/v1";

export async function analyzeImageFile(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", "standard");
  formData.append("include_child_risk", "true");
  formData.append("return_bbox", "true");

  const response = await axios.post<AnalysisResult>(`${API_BASE_URL}/analyze/image`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000,
  });

  return response.data;
}

export async function analyzeImageUrl(imageUrl: string): Promise<AnalysisResult> {
  const response = await axios.post<AnalysisResult>(
    `${API_BASE_URL}/analyze/image-url`,
    { image_url: imageUrl, mode: "standard", include_child_risk: true, return_bbox: true },
    { timeout: 60000 },
  );
  return response.data;
}

