import clsx from "clsx";
import { Link2, Loader2, PanelRight, ScanLine, Upload, X } from "lucide-react";
import { useRef, useState } from "react";
import { analyzeImageFile, analyzeImageUrl } from "../shared/api/imalytixApi";
import type { AnalysisResult } from "../shared/types/analysis";
import { scoreBgClass, toPercentageScore } from "../shared/utils/score";
import ProviderCard from "../components/ProviderCard";
import ScoreGauge from "../components/ScoreGauge";

type Tab = "file" | "url";
type Phase = "idle" | "loading" | "result" | "error";

export default function PopupApp() {
  const [tab, setTab] = useState<Tab>("file");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [urlInput, setUrlInput] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result as string);
    reader.readAsDataURL(f);
    e.target.value = "";
  };

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setFile(null);
    setPreview(null);
  };

  const analyze = async () => {
    if (phase === "loading") return;
    try {
      setPhase("loading");
      setError(null);
      let r: AnalysisResult;

      if (tab === "file") {
        if (!file) { setError("파일을 선택해주세요."); setPhase("error"); return; }
        r = await analyzeImageFile(file);
      } else {
        if (!urlInput.trim()) { setError("URL을 입력해주세요."); setPhase("error"); return; }
        r = await analyzeImageUrl(urlInput.trim());
      }

      setResult(r);
      setPhase("result");

      // 사이드 패널 공유용 저장
      chrome.storage.local.set({
        imalytix_loading: false,
        imalytix_result: r,
        imalytix_error: null,
        imalytix_preview: preview ?? urlInput.trim(),
        imalytix_source: "popup",
        imalytix_timestamp: Date.now(),
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "분석 실패. 백엔드 서버를 확인하세요.";
      setError(msg);
      setPhase("error");
    }
  };

  const openSidePanel = () => {
    chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
      if (tab?.windowId) chrome.sidePanel.open({ windowId: tab.windowId });
    });
    window.close();
  };

  const score = result ? toPercentageScore(result.final_result.ai_probability) : 0;

  return (
    <div className="w-[400px] bg-white text-slate-900 select-none">
      {/* 헤더 */}
      <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900">
          <ScanLine className="h-4 w-4 text-white" />
        </div>
        <span className="text-sm font-bold tracking-tight">Imalytix</span>
        <span className="ml-auto text-[11px] text-slate-400">AI 이미지 판별</span>
      </div>

      <div className="space-y-3 p-4">
        {/* 탭 */}
        <div className="flex gap-1 rounded-xl bg-slate-100 p-1">
          {(["file", "url"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setPhase("idle"); setError(null); }}
              className={clsx(
                "flex flex-1 items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-semibold transition",
                tab === t ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700",
              )}
            >
              {t === "file" ? <><Upload className="h-3.5 w-3.5" />파일 업로드</> : <><Link2 className="h-3.5 w-3.5" />URL 입력</>}
            </button>
          ))}
        </div>

        {/* 입력 영역 */}
        {tab === "file" ? (
          <div
            onClick={() => inputRef.current?.click()}
            className="flex min-h-[120px] cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-200 p-4 transition hover:border-slate-300 hover:bg-slate-50"
          >
            {preview ? (
              <div className="relative w-full">
                <img src={preview} alt="preview" className="max-h-40 w-full rounded-lg object-contain" />
                <button
                  type="button"
                  onClick={clearFile}
                  className="absolute right-1 top-1 rounded-full bg-slate-900/70 p-0.5 transition hover:bg-slate-900"
                >
                  <X className="h-3.5 w-3.5 text-white" />
                </button>
              </div>
            ) : (
              <>
                <Upload className="h-7 w-7 text-slate-300" />
                <span className="text-xs text-slate-500">클릭하여 이미지 선택</span>
                <span className="text-[10px] text-slate-400">JPG · PNG · WEBP · 최대 10MB</span>
              </>
            )}
            <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleFileChange} />
          </div>
        ) : (
          <input
            type="url"
            placeholder="https://example.com/image.jpg"
            value={urlInput}
            onChange={(e) => { setUrlInput(e.target.value); setPhase("idle"); }}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-sky-400 focus:bg-white focus:ring-2 focus:ring-sky-100"
          />
        )}

        {/* 분석 버튼 */}
        <button
          onClick={analyze}
          disabled={phase === "loading"}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-50"
        >
          {phase === "loading" ? (
            <><Loader2 className="h-4 w-4 animate-spin" />분석 중…</>
          ) : "분석 시작"}
        </button>

        {/* 오류 */}
        {phase === "error" && error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</div>
        )}

        {/* 결과 */}
        {phase === "result" && result && (
          <div className="space-y-3">
            {/* 종합 점수 */}
            <div className={clsx("flex items-center gap-4 rounded-2xl border p-4", scoreBgClass(score))}>
              <ScoreGauge score={score} size={110} />
              <div className="flex-1 space-y-2">
                <div className="text-[10px] font-semibold uppercase tracking-wider opacity-60">판정 결과</div>
                <div className="text-sm font-bold">{result.final_result.label}</div>
                <div className="text-[11px] opacity-70">
                  신뢰도 {result.final_result.confidence === "high" ? "높음" : result.final_result.confidence === "medium" ? "보통" : "낮음"}
                </div>
                {result.evidence_summary.slice(0, 2).map((e) => (
                  <div key={e} className="flex items-start gap-1 text-[11px] opacity-80">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-current" />
                    {e}
                  </div>
                ))}
              </div>
            </div>

            {/* 모델 카드 */}
            {result.vision_results.map((v) => (
              <ProviderCard key={v.provider} item={v} />
            ))}

            {/* 권고 */}
            {result.recommended_action && (
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-xs text-slate-600">
                <span className="font-semibold text-slate-700">권고: </span>{result.recommended_action}
              </div>
            )}

            {/* 상세보기 버튼 */}
            <button
              onClick={openSidePanel}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
            >
              <PanelRight className="h-4 w-4" />
              사이드 패널에서 상세보기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
