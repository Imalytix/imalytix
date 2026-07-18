import axios from "axios";
import { BadgeCheck, Link2, ShieldCheck, ScanSearch, FileSearch, Upload } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeImageFile, analyzeImageUrl } from "../api/imalytixApi";
import AnalysisStepsLoader from "../components/common/AnalysisStepsLoader";
import ErrorState from "../components/common/ErrorState";
import AppHeader from "../components/layout/AppHeader";
import MetadataResultCard from "../components/results/MetadataResultCard";
import HistoryPanel from "../components/results/HistoryPanel";
import ProviderResultCard from "../components/results/ProviderResultCard";
import RecommendationPanel from "../components/results/RecommendationPanel";
import ScoreGauge from "../components/results/ScoreGauge";
import TrustAnalysisCard from "../components/results/TrustAnalysisCard";
import ImageUploader from "../components/upload/ImageUploader";
import type { AnalysisResult, DetectorResult, VisionResult } from "../types/analysis";
import {
  loadAnalysisResult,
  loadHistory,
  loadImageDataUrl,
  saveAnalysisResult,
  saveImageDataUrl,
  type HistoryEntry,
} from "../utils/storage";
import { toPercentageScore } from "../utils/score";

type InputMode = "file" | "url";

const USE_CASES = [
  {
    icon: <ShieldCheck className="h-5 w-5 text-slate-400" />,
    title: "중고거래 이미지 검증",
    desc: "판매 상품 사진이 실제 촬영인지, AI로 만든 가짜인지 확인합니다.",
  },
  {
    icon: <ScanSearch className="h-5 w-5 text-slate-400" />,
    title: "SNS 딥페이크 탐지",
    desc: "소셜 미디어의 의심스러운 프로필·사건 사진의 진위를 판별합니다.",
  },
  {
    icon: <FileSearch className="h-5 w-5 text-slate-400" />,
    title: "문서·증거 사진 확인",
    desc: "법적·계약상 증거 이미지의 편집·위변조 여부를 탐지합니다.",
  },
];

export default function UploadAnalysisPage() {
  const navigate = useNavigate();

  const [inputMode, setInputMode] = useState<InputMode>("file");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imageUrlInput, setImageUrlInput] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(() => loadImageDataUrl());
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(
    () => loadAnalysisResult(),
  );
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>(() => loadHistory());

  const visionResults = analysisResult?.vision_results ?? [];
  const detectorResults = analysisResult?.detector_results ?? [];
  const metadata = analysisResult?.metadata_analysis;
  const scorePercent = analysisResult
    ? toPercentageScore(analysisResult.final_result.ai_probability)
    : 0;

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

  const handleReset = () => {
    setAnalysisResult(null);
    setSelectedFile(null);
    setPreviewUrl(null);
    setErrorMessage(null);
    setImageUrlInput("");
  };

  const handleOpenDetail = () => {
    if (analysisResult) saveAnalysisResult(analysisResult);
    if (previewUrl) saveImageDataUrl(previewUrl);
    navigate("/detail");
  };

  const showHero = !analysisResult && !isLoading;

  return (
    <div className="min-h-screen bg-white">
      <AppHeader />

      {/* 히어로 섹션 — 결과 없을 때만 표시 */}
      {showHero && (
        <section className="border-b border-slate-100 bg-white py-16 text-center">
          <div className="mx-auto max-w-2xl px-6">
            <span className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-slate-100 bg-slate-50 px-3.5 py-1 text-xs font-medium text-slate-500">
              <span className="h-1.5 w-1.5 rounded-full bg-sky-500" />
              멀티모델 AI 이미지 분석
            </span>
            <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900 lg:text-5xl">
              이 이미지, 진짜일까요?
            </h1>
            <p className="mt-4 text-[15px] leading-relaxed text-slate-500">
              메타데이터 분석, 시각 AI 앙상블, 위변조 탐지를 조합해
              <br className="hidden sm:block" />
              이미지의 AI 생성·편집 여부를 판별합니다.
            </p>
          </div>
        </section>
      )}

      <main className="mx-auto w-full max-w-5xl px-6 py-10">
        {/* 업로드 입력 영역 */}
        {showHero && (
          <div className="mx-auto max-w-2xl">
            {/* 탭 */}
            <div className="mb-4 flex gap-2">
              <button
                type="button"
                onClick={() => setInputMode("file")}
                className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition ${
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
                className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition ${
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
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                <label className="mb-2 block text-sm font-medium text-slate-700">이미지 URL</label>
                <input
                  type="url"
                  placeholder="https://example.com/image.jpg"
                  value={imageUrlInput}
                  onChange={(e) => {
                    setImageUrlInput(e.target.value);
                    setErrorMessage(null);
                  }}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100"
                />
                <p className="mt-2 text-xs text-slate-400">공개적으로 접근 가능한 이미지 URL을 입력하세요.</p>
              </div>
            )}

            {/* 에러 */}
            {errorMessage && !isLoading && (
              <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {errorMessage}
              </div>
            )}

            {/* 분석 버튼 */}
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={isLoading}
              className="mt-4 w-full rounded-xl bg-slate-900 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50"
            >
              {isLoading ? "분석 중…" : "분석 시작"}
            </button>
          </div>
        )}

        {/* 단계별 로딩 */}
        {isLoading && (
          <div className="mx-auto max-w-2xl">
            <AnalysisStepsLoader active={isLoading} />
          </div>
        )}

        {/* 결과 영역 */}
        {analysisResult && !isLoading && (
          <>
            {/* 결과 헤더 */}
            <div className="mb-8 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-900">분석 결과</h2>
                <p className="mt-0.5 text-sm text-slate-500">
                  {analysisResult.final_result.label} ·{" "}
                  AI 생성 가능성 {scorePercent}%
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleReset}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
                >
                  새 이미지 분석
                </button>
                <button
                  type="button"
                  onClick={handleOpenDetail}
                  className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
                >
                  상세 분석
                  <BadgeCheck className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* 에러 */}
            {errorMessage && <ErrorState message={errorMessage} />}

            {/* 종합 점수 + 비전 모델 */}
            <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
              {/* 점수 게이지 */}
              <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-100 bg-white p-8 shadow-sm">
                <p className="section-title mb-5">종합 점수</p>
                <ScoreGauge
                  score={scorePercent}
                  label={analysisResult.final_result.label}
                  size={200}
                />
                <p className="mt-5 text-center text-xs leading-5 text-slate-400">
                  높을수록 AI 생성 가능성 높음 · 낮을수록 실제 사진
                </p>
              </div>

              {/* 비전 모델 결과 */}
              <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
                <p className="section-title mb-5">비전 모델 분석</p>
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
                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-6 text-sm text-slate-500">
                      표시할 비전 모델 결과가 없습니다.
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 메타데이터 + 전용 탐지기 */}
            <div className="mt-5 grid gap-5 lg:grid-cols-2">
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

              {detectorResults.length > 0 && (
                <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
                  <p className="section-title mb-5">전용 탐지기</p>
                  <div className="space-y-4">
                    {detectorResults.map((item: DetectorResult) => (
                      <ProviderResultCard
                        key={`${item.provider}-${item.detector_type ?? "detector"}`}
                        provider={item.provider}
                        modelName={item.detector_type}
                        score={toPercentageScore(item.score)}
                        rawScore={item.score}
                        isAiGenerated={item.is_ai_generated}
                        confidence={item.confidence}
                        evidence={["전용 탐지 API 점수 기반 결과입니다."]}
                        limitations={[]}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 신뢰성 분석 */}
            {analysisResult.trust_analysis && (
              <div className="mt-5">
                <TrustAnalysisCard trust={analysisResult.trust_analysis} />
              </div>
            )}

            {/* 권고 사항 */}
            <div className="mt-5">
              <RecommendationPanel
                recommendedAction={analysisResult.recommended_action}
                limitations={analysisResult.limitations ?? []}
                aiProbability={scorePercent}
              />
            </div>
          </>
        )}

        {/* 유스케이스 섹션 — 결과 없을 때만 표시 */}
        {showHero && (
          <section id="how-it-works" className="mt-20">
            <p className="mb-6 text-center text-xs font-semibold uppercase tracking-widest text-slate-400">
              이런 상황에서 사용하세요
            </p>
            <div className="grid gap-4 sm:grid-cols-3">
              {USE_CASES.map((uc) => (
                <div
                  key={uc.title}
                  className="rounded-2xl border border-slate-100 bg-slate-50 p-6 transition hover:border-slate-200 hover:bg-white hover:shadow-sm"
                >
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white">
                    {uc.icon}
                  </div>
                  <div className="text-sm font-semibold text-slate-800">{uc.title}</div>
                  <div className="mt-1.5 text-sm leading-relaxed text-slate-500">{uc.desc}</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 분석 이력 */}
        <div id="history" className="mt-16">
          <HistoryPanel history={history} onClear={() => setHistory([])} />
        </div>
      </main>
    </div>
  );
}
