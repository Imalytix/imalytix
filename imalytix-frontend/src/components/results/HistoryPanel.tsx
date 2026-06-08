import clsx from "clsx";
import { Clock, Trash2 } from "lucide-react";
import type { HistoryEntry } from "../../utils/storage";
import { clearHistory } from "../../utils/storage";

interface HistoryPanelProps {
  history: HistoryEntry[];
  onClear: () => void;
}

function scoreColor(score: number) {
  if (score >= 80) return "text-rose-600";
  if (score >= 60) return "text-amber-600";
  if (score >= 31) return "text-sky-600";
  return "text-emerald-600";
}

function scoreBg(score: number) {
  if (score >= 80) return "bg-rose-50 border-rose-200";
  if (score >= 60) return "bg-amber-50 border-amber-200";
  if (score >= 31) return "bg-sky-50 border-sky-200";
  return "bg-emerald-50 border-emerald-200";
}

function formatTime(ts: number) {
  const d = new Date(ts);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

export default function HistoryPanel({ history, onClear }: HistoryPanelProps) {
  if (history.length === 0) return null;

  return (
    <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-slate-400" />
          <span className="section-title">최근 분석 기록</span>
        </div>
        <button
          type="button"
          onClick={() => {
            clearHistory();
            onClear();
          }}
          className="flex items-center gap-1 rounded-xl border border-slate-200 px-3 py-1.5 text-xs text-slate-500 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600"
        >
          <Trash2 className="h-3 w-3" />
          기록 삭제
        </button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {history.map((entry) => (
          <div
            key={entry.requestId}
            className={clsx("rounded-2xl border p-3", scoreBg(entry.aiProbability))}
          >
            <div className={clsx("text-2xl font-bold", scoreColor(entry.aiProbability))}>
              {entry.aiProbability}%
            </div>
            <div className="mt-1 text-xs font-medium text-slate-700 line-clamp-1">{entry.label}</div>
            <div className="mt-1 text-[11px] text-slate-400">{formatTime(entry.timestamp)}</div>
            <div className="mt-1 text-[11px] text-slate-400 uppercase">{entry.mode}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
