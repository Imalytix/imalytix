import axios from "axios";
import { BadgeCheck, Link2, Upload } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeImageFile, analyzeImageUrl } from "../api/imalytixApi";
import AnalysisStepsLoader from "../components/common/AnalysisStepsLoader";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import AppHeader from "../components/layout/AppHeader";
import PageContainer from "../components/layout/PageContainer";
import MetadataResultCard from "../components/results/MetadataResultCard";
import HistoryPanel from "../components/results/HistoryPanel";
import ProviderResultCard from "../components/results/ProviderResultCard";
import RecommendationPanel from "../components/results/RecommendationPanel";
import ScoreGauge from "../components/results/ScoreGauge";
import ImageUploader from "../components/upload/ImageUploader";
import type { AnalysisResult, DetectorResult, VisionResult } from "../types/analysis";
import { loadAnalysisResult, loadHistory, loadImageDataUrl, saveAnalysisResult, saveImageDataUrl, type HistoryEntry } from "../utils/storage";
import { toPercentageScore } from "../utils/score";

type InputMode = "file" | "url";

export default function UploadAnalysisPage() {
  const navigate = useNavigate();

  const [inputMode, setInputMode] = useState<InputMode>("file");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imageUrlInput, setImageUrlInput] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(() => loadImageDataUrl());
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(() => loadAnalysisResult());
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>(() => loadHistory());

  const visionResults = analysisResult?.vision_results ?? [];
  const detectorResults = analysisResult?.detector_results ?? [];
  const metadata = analysisResult?.metadata_analysis;
  const scorePercent = analysisResult ? toPercentageScore(analysisResult.final_result.ai_probability) : 0;

  const handleAnalyze = async () => {
    try {
      setErrorMessage(null);
      setIsLoading(true);
      let result: AnalysisResult;

      if (inputMode === "url") {
        const trimmed = imageUrlInput.trim();
        if (!trimmed) {
          setErrorMessage("이미지 URL을 입력해주세요.");
          return;
        }
        result = await analyzeImageUrl(trimmed);
        setPreviewUrl(trimmed);
        saveImageDataUrl(trimmed);
      } else {
        if (!selectedFile) {
          setErrorMessage("이미지를 먼저 선택해주세요.");
          return;
        }
        result = await analyzeImageFile(selectedFile);
        if (previewUrl) saveImageDataUrl(previewUrl);
      }

      setAnalysisResult(result);
      saveAnalysisResult(result);
      setHistory(loadHistory());
    } catch (error) {
      const message = axios.isAxiosError(error)
        ? ((error.response?.data as { detail?: string } | undefined)?.detail ?? error.message)
        : error instanceof Error
          ? error.message
          : "분석에 실패했습니다. 백엔드 서버 상태를 확인해주세요.";
      setErrorMessage(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenDetail = () => {
    if (analysisResult) saveAnalysisResult(analysisResult);
    if (previewUrl) saveImageDataUrl(previewUrl);
    navigate("/detail");
  };

  return (
    <div className="min-h-screen">
      <AppHeader />
      <PageContainer>
        {/* 헤더 */}
        <div className="mb-5 rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-4xl">
              <div className="section-title">Imalytix</div>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
                AI 이미지 판별 대시보드
              </h1>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                이미지를 업로드하거나 URL을 입력하면 메타데이터·시각 분석을 조합해 AI 생성 가능성을 판별합니다.
              </p>
            </div>
            {analysisResult && (
              <button
                type="button"
                onClick={handleOpenDetail}
                className="inline-flex shrink-0 items-center gap-2 rounded-2xl border border-slate-200 bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
              >
                의심 부위 상세보기
                <BadgeCheck className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>

        <div className="space-y-5">
          {/* 입력 영역 */}
          <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
            <div className="mb-4 flex gap-2">
              <button
                type="button"
                onClick={() => setInputMode("file")}
                className={`inline-flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm font-semibold transition ${
                  inputMode === "file"
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                <Upload className="h-4 w-4" />
                파일 업로드
              </button>
              <button
                type="button"
                onClick={() => setInputMode("url")}
                className={`inline-flex items-center gap-2 rounded-2xl border px-4 py-2.5 text-sm font-semibold transition ${
                  inputMode === "url"
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                <Link2 className="h-4 w-4" />
                URL 입력
              </button>
            </div>

            {inputMode === "file" ? (
              <ImageUploader
                previewUrl={previewUrl}
                fileName={selectedFile?.name ?? null}
                onFileSelected={(file, dataUrl) => {
                  setSelectedFile(file);
                  setPreviewUrl(dataUrl);
                  setErrorMessage(null);
                }}
              />
            ) : (
              <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
                <div className="flex flex-col gap-3">
                  <div className="text-sm font-medium text-slate-700">이미지 URL</div>
                  <input
                    type="url"
                    placeholder="https://example.com/image.jpg"
                    value={imageUrlInput}
                    onChange={(e) => {
                      setImageUrlInput(e.target.value);
                      setErrorMessage(null);
                    }}
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-sky-400 focus:bg-white focus:ring-2 focus:ring-sky-100"
                  />
                  <p className="text-xs text-slate-400">
                    공개적으로 접근 가능한 이미지 URL을 입력하세요.
                  </p>
                </div>
                <div className="flex items-center justify-center rounded-[28px] border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-400">
                  URL 분석 시 이미지는 미리보기 없이 처리됩니다.
                </div>
              </div>
            )}

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={isLoading}
                className="rounded-2xl bg-sky-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-sky-600 disabled:opacity-50"
              >
                {isLoading ? "분석 중…" : "분석 시작"}
              </button>
              <span className="text-xs text-slate-400">모드: standard · return_bbox: true</span>
            </div>
          </div>

          {/* 단계별 로딩 */}
          {isLoading && <AnalysisStepsLoader active={isLoading} />}

          {/* 오류 */}
          {errorMessage && !isLoading && <ErrorState message={errorMessage} />}

          {/* 결과 없을 때 안내 */}
          {!analysisResult && !isLoading && !errorMessage && (
            <EmptyState
              title="아직 분석 결과가 없습니다."
              message="이미지를 업로드하거나 URL을 입력한 뒤 분석 시작 버튼을 눌러주세요."
            />
          )}

          {/* 분석 결과 */}
          {analysisResult && !isLoading && (
            <>
              {/* 점수 + 비전 모델 */}
              <div className="grid gap-5 lg:grid-cols-[0.36fr_0.64fr]">
                <div className="flex flex-col items-center justify-center rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
                  <div className="section-title mb-4 self-start">종합 점수</div>
                  <ScoreGauge
                    score={scorePercent}
                    label={analysisResult.final_result.label}
                    size={200}
                  />
                  <p className="mt-4 text-center text-xs leading-5 text-slate-400">
                    높을수록 AI 생성 가능성 높음 · 낮을수록 실제 사진
                  </p>
                </div>

                <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
                  <div className="section-title mb-4">비전 모델 분석</div>
                  <div className="space-y-4">
                    {visionResults.length > 0 ? (
                      visionResults.map((item: VisionResult) => (
                        <ProviderResultCard
                          key={`${item.provider}-${item.model_name ?? "model"}`}
                          provider={item.provider}
                          modelName={item.model_name}
                          score={item.score}
                          rawScore={item.score}
                          isAiGenerated={item.is_ai_generated}
                          confidence={item.confidence}
                          evidence={item.evidence.map((e) => e.description)}
                          limitations={item.limitations}
                          isMock={item.is_mock}
                          errorMessage={item.error_message}
                        />
                      ))
                    ) : (
                      <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
                        표시할 비전 모델 결과가 없습니다.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 메타데이터 + 전용 탐지기 */}
              <div className="grid gap-5 lg:grid-cols-[0.54fr_0.46fr]">
                <MetadataResultCard
                  exifFound={Boolean(metadata?.exif_found)}
                  pngMetadataFound={Boolean(metadata?.png_metadata_found)}
                  c2paFound={Boolean(metadata?.c2pa_found)}
                  aiToolDetected={Boolean(metadata?.ai_tool_detected)}
                  detectedTools={metadata?.detected_tools ?? []}
                  metadataScore={metadata?.metadata_score ?? 0}
                  evidence={metadata?.evidence ?? []}
                  limitations={metadata?.limitations ?? []}
                />

                <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
                  <div className="section-title mb-4">전용 탐지기</div>
                  <div className="space-y-4">
                    {detectorResults.length > 0 ? (
                      detectorResults.map((item: DetectorResult) => (
                        <ProviderResultCard
                          key={`${item.provider}-${item.detector_type ?? "detector"}`}
                          provider={item.provider}
                          modelName={item.detector_type}
                          score={toPercentageScore(item.score)}
                          rawScore={item.score}
                          isAiGenerated={item.is_ai_generated}
                          confidence={item.confidence}
                          evidence={["전용 탐지 API 점수 기반 결과입니다."]}
                          limitations={["추후 Hive · Sightengine · Reality Defender 연동 예정"]}
                        />
                      ))
                    ) : (
                      <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
                        현재 전용 탐지기 결과 없음
                        <div className="mt-1 text-xs text-slate-400">
                          Hive · Sightengine · Reality Defender 연동 예정
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 권고 사항 */}
              <RecommendationPanel
                recommendedAction={analysisResult.recommended_action}
                limitations={analysisResult.limitations ?? []}
                aiProbability={scorePercent}
              />
            </>
          )}

          {/* 분석 히스토리 */}
          <HistoryPanel history={history} onClear={() => setHistory([])} />
        </div>
      </PageContainer>
    </div>
  );
}
