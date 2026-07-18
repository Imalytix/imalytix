import clsx from "clsx";
import {
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  ScanLine,
  Settings,
  ShieldAlert,
  TriangleAlert,
  Info,
} from "lucide-react";
import { useEffect, useState } from "react";
import ProviderCard from "../components/ProviderCard";
import ScoreGauge from "../components/ScoreGauge";
import type { AnalysisResult } from "../shared/types/analysis";
import { scoreBgClass, toPercentageScore } from "../shared/utils/score";

const LOADING_STEPS = [
  "이미지 검증 중",
  "메타데이터 분석 중",
  "시각적 징후 분석 중",
  "결과 정리 중",
] as const;

type State =
  | { phase: "idle" }
  | { phase: "loading"; preview: string | null }
  | { phase: "result"; result: AnalysisResult; preview: string | null }
  | { phase: "error"; error: string; preview: string | null };

function RecommendIcon({ score }: { score: number }) {
  if (score >= 80) return <ShieldAlert className="h-4 w-4 text-rose-500" />;
  if (score >= 60) return <TriangleAlert className="h-4 w-4 text-amber-500" />;
  if (score >= 31) return <Info className="h-4 w-4 text-sky-500" />;
  return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
}

function readStorage(): Promise<State> {
  return new Promise((resolve) => {
    chrome.storage.local.get(
      ["imalytix_loading", "imalytix_result", "imalytix_error", "imalytix_preview"],
      (data) => {
        if (data.imalytix_loading) {
          resolve({ phase: "loading", preview: data.imalytix_preview ?? null });
          return;
        }
        if (data.imalytix_result) {
          resolve({ phase: "result", result: data.imalytix_result, preview: data.imalytix_preview ?? null });
          return;
        }
        if (data.imalytix_error) {
          resolve({ phase: "error", error: data.imalytix_error, preview: data.imalytix_preview ?? null });
          return;
        }
        resolve({ phase: "idle" });
      },
    );
  });
}

async function openInWebApp(result: AnalysisResult, preview: string | null) {
  const webAppUrl = await new Promise<string>((resolve) => {
    chrome.storage.sync.get({ webAppUrl: "https://imalytix.vercel.app" }, (r) => {
      resolve((r.webAppUrl as string) || "https://imalytix.vercel.app");
    });
  });

  const tab = await chrome.tabs.create({ url: webAppUrl });
  const listener = (tabId: number, info: chrome.tabs.TabChangeInfo) => {
    if (tabId !== tab.id || info.status !== "complete") return;
    chrome.tabs.onUpdated.removeListener(listener);
    chrome.scripting.executeScript({
      target: { tabId: tab.id! },
      func: (resultJson: string, previewUrl: string | null) => {
        localStorage.setItem("imalytix:lastAnalysisResult", resultJson);
        if (previewUrl) localStorage.setItem("imalytix:lastImageDataUrl", previewUrl);
        window.location.href = "/detail";
      },
      args: [JSON.stringify(result), preview],
    });
  };
  chrome.tabs.onUpdated.addListener(listener);
}

export default function SidePanelApp() {
  const [state, setState] = useState<State>({ phase: "idle" });
  const [showSettings, setShowSettings] = useState(false);
  const [apiUrl, setApiUrl] = useState("http://localhost:8000/api/v1");
  const [webAppUrl, setWebAppUrl] = useState("http://localhost:5173");
  const [loadingStep, setLoadingStep] = useState(0);

  useEffect(() => {
    chrome.storage.sync.get(
      { apiUrl: "http://localhost:8000/api/v1", webAppUrl: "http://localhost:5173" },
      (r) => {
        setApiUrl(r.apiUrl as string);
        setWebAppUrl(r.webAppUrl as string);
      },
    );
    readStorage().then(setState);

    const listener = (changes: Record<string, chrome.storage.StorageChange>) => {
      if ("imalytix_timestamp" in changes) readStorage().then(setState);
    };
    chrome.storage.local.onChanged.addListener(listener);
    return () => chrome.storage.local.onChanged.removeListener(listener);
  }, []);

  useEffect(() => {
    if (state.phase !== "loading") {
      setLoadingStep(0);
      return;
    }

    let index = 0;
    const timers: ReturnType<typeof setTimeout>[] = [];

    const advance = () => {
      if (index >= LOADING_STEPS.length - 1) return;
      const timer = setTimeout(() => {
        index += 1;
        setLoadingStep(index);
        advance();
      }, 1200);
      timers.push(timer);
    };

    setLoadingStep(0);
    advance();
    return () => timers.forEach(clearTimeout);
  }, [state.phase]);

  const saveSettings = () => {
    chrome.storage.sync.set({ apiUrl, webAppUrl });
    setShowSettings(false);
  };

  const score = state.phase === "result" ? toPercentageScore(state.result.final_result.ai_probability) : 0;
  const loadingPercent = Math.round(((loadingStep + 1) / LOADING_STEPS.length) * 100);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <div className="sticky top-0 z-10 flex items-center gap-2 border-b border-slate-200 bg-white px-4 py-3 shadow-sm">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900">
          <ScanLine className="h-4 w-4 text-white" />
        </div>
        <span className="text-sm font-bold">Imalytix</span>
        <span className="text-[11px] text-slate-400">상세 분석 결과</span>
        <button
          onClick={() => setShowSettings((v) => !v)}
          className="ml-auto rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
        >
          <Settings className="h-4 w-4" />
        </button>
      </div>

      {showSettings && (
        <div className="space-y-3 border-b border-slate-200 bg-slate-50 px-4 py-3">
          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-slate-600">백엔드 API URL</div>
            <input
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-100"
            />
          </div>
          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-slate-600">웹 앱 URL</div>
            <input
              value={webAppUrl}
              onChange={(e) => setWebAppUrl(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-100"
            />
          </div>
          <button
            onClick={saveSettings}
            className="w-full rounded-lg bg-slate-900 py-1.5 text-xs font-semibold text-white hover:bg-slate-700"
          >
            저장
          </button>
        </div>
      )}

      <div className="flex-1 space-y-3 p-4">
        {state.phase === "idle" && (
          <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 bg-white py-16 text-center">
            <ScanLine className="h-10 w-10 text-slate-300" />
            <div className="text-sm font-semibold text-slate-500">대기 중</div>
            <p className="max-w-[220px] text-xs leading-5 text-slate-400">
              웹페이지에서 이미지를 우클릭한 뒤
              <br />
              <strong className="text-slate-600">"Imalytix AI로 분석하기"</strong>를 선택하세요.
            </p>
          </div>
        )}

        {state.phase === "loading" && (
          <>
            {state.preview && (
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
                <img src={state.preview} alt="분석 중 이미지" className="max-h-56 w-full object-contain" />
              </div>
            )}
            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <div className="flex items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                <div>
                  <div className="text-sm font-semibold text-slate-900">분석 진행 현황</div>
                  <div className="text-xs text-slate-500">{LOADING_STEPS[loadingStep]}</div>
                </div>
              </div>
              <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-slate-900 transition-all duration-300"
                  style={{ width: `${loadingPercent}%` }}
                />
              </div>
              <div className="mt-4 text-xs text-slate-400">GPT-4o · Gemini 2.5 Flash · Claude Haiku</div>
            </div>
          </>
        )}

        {state.phase === "error" && (
          <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-500" />
            <div className="space-y-1">
              <div className="text-sm font-semibold text-rose-800">분석 실패</div>
              <div className="text-xs text-rose-700">{state.error}</div>
              <div className="text-[10px] text-rose-500">백엔드 서버(http://localhost:8000)가 실행 중인지 확인하세요.</div>
            </div>
          </div>
        )}

        {state.phase === "result" && (
          <>
            {state.preview && (
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <img src={state.preview} alt="분석 대상 이미지" className="max-h-64 w-full object-contain" />
              </div>
            )}

            <div className={clsx("rounded-2xl border p-5", scoreBgClass(score))}>
              <div className="mb-3 text-[10px] font-semibold uppercase tracking-widest opacity-60">통합 점수</div>
              <div className="flex items-center gap-5">
                <ScoreGauge score={score} size={130} />
                <div className="flex-1 space-y-2">
                  <div className="text-base font-bold">{state.result.final_result.label}</div>
                  <div className="text-xs opacity-70">
                    신뢰도{" "}
                    {state.result.final_result.confidence === "high"
                      ? "높음"
                      : state.result.final_result.confidence === "medium"
                        ? "보통"
                        : "낮음"}
                  </div>
                  {state.result.evidence_summary.slice(0, 3).map((e) => (
                    <div key={e} className="flex items-start gap-1.5 text-[11px] opacity-80">
                      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-current" />
                      {e}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {state.result.vision_results.length > 0 && (
              <div className="space-y-2">
                <div className="px-1 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                  엔진별 분석
                </div>
                {state.result.vision_results.map((v) => (
                  <ProviderCard key={v.provider} item={v} />
                ))}
              </div>
            )}

            {state.result.metadata_analysis && (
              <div className="space-y-2 rounded-xl border border-slate-200 bg-white p-3">
                <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">메타데이터</div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: "EXIF", v: state.result.metadata_analysis.exif_found },
                    { label: "PNG", v: state.result.metadata_analysis.png_metadata_found },
                    { label: "C2PA", v: state.result.metadata_analysis.c2pa_found },
                    { label: "AI 도구", v: state.result.metadata_analysis.ai_tool_detected },
                  ].map(({ label, v }) => (
                    <div key={label} className="flex items-center gap-1.5 text-[11px]">
                      <span className={clsx("h-2 w-2 rounded-full", v ? "bg-rose-400" : "bg-emerald-400")} />
                      <span className="text-slate-600">{label}</span>
                      <span className={clsx("font-semibold", v ? "text-rose-600" : "text-emerald-600")}>
                        {v ? "있음" : "없음"}
                      </span>
                    </div>
                  ))}
                </div>
                {state.result.metadata_analysis.detected_tools?.length ? (
                  <div className="text-[11px] text-slate-500">
                    감지 도구:{" "}
                    <span className="font-semibold text-rose-600">
                      {state.result.metadata_analysis.detected_tools.join(", ")}
                    </span>
                  </div>
                ) : null}
              </div>
            )}

            <div className={clsx("flex items-start gap-3 rounded-xl border p-3", scoreBgClass(score))}>
              <RecommendIcon score={score} />
              <div className="space-y-0.5">
                <div className="text-[10px] font-semibold uppercase tracking-widest opacity-60">권장 사항</div>
                <div className="text-xs font-medium">{state.result.recommended_action}</div>
              </div>
            </div>

            {state.result.limitations.length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-3 space-y-1.5">
                <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">분석 한계</div>
                {state.result.limitations.slice(0, 3).map((l) => (
                  <div key={l} className="flex items-start gap-1.5 text-[11px] text-slate-500">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-300" />
                    {l}
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={() => openInWebApp(state.result, state.preview)}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-900 bg-slate-900 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
            >
              <ExternalLink className="h-4 w-4" />
              웹 상세보기
            </button>

            <div className="text-center text-[10px] text-slate-300">Request ID: {state.result.request_id}</div>
          </>
        )}
      </div>
    </div>
  );
}
