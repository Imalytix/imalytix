import clsx from "clsx";
import { AlertCircle, CheckCircle2, ExternalLink, Loader2, ScanLine, Settings, ShieldAlert, TriangleAlert, Info } from "lucide-react";
import { useEffect, useState } from "react";
import type { AnalysisResult } from "../shared/types/analysis";
import { scoreBgClass, toPercentageScore } from "../shared/utils/score";
import ProviderCard from "../components/ProviderCard";
import ScoreGauge from "../components/ScoreGauge";

async function openInWebApp(result: AnalysisResult, preview: string | null) {
  const webAppUrl = await new Promise<string>((resolve) => {
    chrome.storage.sync.get({ webAppUrl: "http://localhost:5173" }, (r) => {
      resolve((r.webAppUrl as string) || "http://localhost:5173");
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

type State =
  | { phase: "idle" }
  | { phase: "loading"; preview: string | null }
  | { phase: "result"; result: AnalysisResult; preview: string | null }
  | { phase: "error"; error: string; preview: string | null };

function readStorage(): Promise<State> {
  return new Promise((resolve) => {
    chrome.storage.local.get(
      ["imalytix_loading", "imalytix_result", "imalytix_error", "imalytix_preview"],
      (data) => {
        if (data.imalytix_loading) {
          resolve({ phase: "loading", preview: data.imalytix_preview ?? null });
        } else if (data.imalytix_result) {
          resolve({ phase: "result", result: data.imalytix_result, preview: data.imalytix_preview ?? null });
        } else if (data.imalytix_error) {
          resolve({ phase: "error", error: data.imalytix_error, preview: data.imalytix_preview ?? null });
        } else {
          resolve({ phase: "idle" });
        }
      },
    );
  });
}

function RecommendIcon({ score }: { score: number }) {
  if (score >= 80) return <ShieldAlert className="h-4 w-4 text-rose-500" />;
  if (score >= 60) return <TriangleAlert className="h-4 w-4 text-amber-500" />;
  if (score >= 31) return <Info className="h-4 w-4 text-sky-500" />;
  return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
}

export default function SidePanelApp() {
  const [state, setState] = useState<State>({ phase: "idle" });
  const [showSettings, setShowSettings] = useState(false);
  const [apiUrl, setApiUrl] = useState("http://localhost:8000/api/v1");
  const [webAppUrl, setWebAppUrl] = useState("http://localhost:5173");

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

  const saveSettings = () => {
    chrome.storage.sync.set({ apiUrl, webAppUrl });
    setShowSettings(false);
  };

  const score =
    state.phase === "result" ? toPercentageScore(state.result.final_result.ai_probability) : 0;

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      {/* 헤더 */}
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

      {/* 설정 패널 */}
      {showSettings && (
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 space-y-3">
          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-slate-600">백엔드 API URL</div>
            <input
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-100"
            />
            <p className="text-[10px] text-slate-400">기본값: http://localhost:8000/api/v1</p>
          </div>
          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-slate-600">웹앱 URL (상세보기 이동 대상)</div>
            <input
              value={webAppUrl}
              onChange={(e) => setWebAppUrl(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-100"
            />
            <p className="text-[10px] text-slate-400">기본값: http://localhost:5173</p>
          </div>
          <button
            onClick={saveSettings}
            className="w-full rounded-lg bg-slate-900 py-1.5 text-xs font-semibold text-white hover:bg-slate-700"
          >
            저장
          </button>
        </div>
      )}

      {/* 콘텐츠 */}
      <div className="flex-1 space-y-3 p-4">

        {/* IDLE */}
        {state.phase === "idle" && (
          <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 bg-white py-16 text-center">
            <ScanLine className="h-10 w-10 text-slate-300" />
            <div className="text-sm font-semibold text-slate-500">대기 중</div>
            <p className="max-w-[220px] text-xs text-slate-400 leading-5">
              팝업에서 이미지를 분석하거나<br />
              웹페이지의 이미지를 우클릭 →<br />
              <strong className="text-slate-600">"Imalytix로 분석"</strong>을 선택하세요.
            </p>
          </div>
        )}

        {/* LOADING */}
        {state.phase === "loading" && (
          <>
            {state.preview && (
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
                <img src={state.preview} alt="분석 중" className="max-h-56 w-full object-contain" />
              </div>
            )}
            <div className="flex flex-col items-center gap-3 rounded-2xl border border-slate-200 bg-white py-10">
              <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
              <div className="text-sm font-medium text-slate-600">3개 AI 모델로 분석 중…</div>
              <div className="text-xs text-slate-400">GPT-4o · Gemini 2.5 Flash · Claude Haiku</div>
            </div>
          </>
        )}

        {/* ERROR */}
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

        {/* RESULT */}
        {state.phase === "result" && (
          <>
            {/* 이미지 미리보기 */}
            {state.preview && (
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <img src={state.preview} alt="분석 이미지" className="max-h-64 w-full object-contain" />
              </div>
            )}

            {/* 종합 점수 */}
            <div className={clsx("rounded-2xl border p-5", scoreBgClass(score))}>
              <div className="mb-3 text-[10px] font-semibold uppercase tracking-widest opacity-60">종합 점수</div>
              <div className="flex items-center gap-5">
                <ScoreGauge score={score} size={130} />
                <div className="flex-1 space-y-2">
                  <div className="text-base font-bold">{state.result.final_result.label}</div>
                  <div className="text-xs opacity-70">
                    신뢰도 {state.result.final_result.confidence === "high" ? "높음" : state.result.final_result.confidence === "medium" ? "보통" : "낮음"}
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

            {/* 비전 모델 결과 */}
            {state.result.vision_results.length > 0 && (
              <div className="space-y-2">
                <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-400 px-1">비전 모델 분석</div>
                {state.result.vision_results.map((v) => (
                  <ProviderCard key={v.provider} item={v} />
                ))}
              </div>
            )}

            {/* 메타데이터 */}
            {state.result.metadata_analysis && (
              <div className="rounded-xl border border-slate-200 bg-white p-3 space-y-2">
                <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">메타데이터 분석</div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: "EXIF", v: state.result.metadata_analysis.exif_found },
                    { label: "PNG 메타데이터", v: state.result.metadata_analysis.png_metadata_found },
                    { label: "C2PA", v: state.result.metadata_analysis.c2pa_found },
                    { label: "AI 도구 감지", v: state.result.metadata_analysis.ai_tool_detected },
                  ].map(({ label, v }) => (
                    <div key={label} className="flex items-center gap-1.5 text-[11px]">
                      <span className={clsx("h-2 w-2 rounded-full", v ? "bg-rose-400" : "bg-emerald-400")} />
                      <span className="text-slate-600">{label}</span>
                      <span className={clsx("font-semibold", v ? "text-rose-600" : "text-emerald-600")}>
                        {v === undefined ? "-" : v ? "있음" : "없음"}
                      </span>
                    </div>
                  ))}
                </div>
                {state.result.metadata_analysis.detected_tools && state.result.metadata_analysis.detected_tools.length > 0 && (
                  <div className="text-[11px] text-slate-500">
                    감지된 AI 도구: <span className="font-semibold text-rose-600">{state.result.metadata_analysis.detected_tools.join(", ")}</span>
                  </div>
                )}
              </div>
            )}

            {/* 권고 사항 */}
            <div className={clsx("flex items-start gap-3 rounded-xl border p-3", scoreBgClass(score))}>
              <RecommendIcon score={score} />
              <div className="space-y-0.5">
                <div className="text-[10px] font-semibold uppercase tracking-widest opacity-60">권고 사항</div>
                <div className="text-xs font-medium">{state.result.recommended_action}</div>
              </div>
            </div>

            {/* 분석 한계 */}
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

            {/* 웹앱 상세보기 버튼 */}
            <button
              onClick={() => openInWebApp(state.result, state.preview)}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-900 bg-slate-900 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
            >
              <ExternalLink className="h-4 w-4" />
              웹에서 상세보기
            </button>

            {/* 요청 ID */}
            <div className="text-center text-[10px] text-slate-300">
              Request ID: {state.result.request_id}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
