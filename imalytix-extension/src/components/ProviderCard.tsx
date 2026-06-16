import clsx from "clsx";
import { AlertCircle, CheckCircle2, MinusCircle, TriangleAlert } from "lucide-react";
import { toPercentageScore } from "../shared/utils/score";
import type { VisionResult } from "../shared/types/analysis";

function VerdictIcon({ v }: { v: boolean | null }) {
  if (v === true) return <CheckCircle2 className="h-3.5 w-3.5 text-rose-500" />;
  if (v === false) return <MinusCircle className="h-3.5 w-3.5 text-emerald-500" />;
  return <TriangleAlert className="h-3.5 w-3.5 text-amber-500" />;
}

export default function ProviderCard({ item }: { item: VisionResult }) {
  const pct = toPercentageScore(item.score);
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold text-slate-900">{item.provider}</div>
          {item.model_name && <div className="text-[10px] text-slate-400">{item.model_name}</div>}
        </div>
        <div className="text-xl font-bold text-slate-900">{pct}%</div>
      </div>

      {item.error_message ? (
        <div className="flex items-start gap-1.5 rounded-lg bg-rose-50 px-2.5 py-2 text-[11px] text-rose-700">
          <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          {item.error_message}
        </div>
      ) : (
        <>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={clsx("h-full rounded-full transition-all",
                pct >= 80 ? "bg-rose-500" : pct >= 60 ? "bg-amber-400" : pct >= 31 ? "bg-sky-400" : "bg-emerald-400"
              )}
              style={{ width: `${Math.max(4, pct)}%` }}
            />
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-slate-600">
            <VerdictIcon v={item.is_ai_generated} />
            <span>{item.is_ai_generated === true ? "AI 생성 가능성 높음" : item.is_ai_generated === false ? "실제 이미지 가능성 높음" : "판단 불확실"}</span>
          </div>
          {item.evidence.slice(0, 2).map((e) => (
            <div key={e.description} className="flex items-start gap-1.5 text-[11px] text-slate-500">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-300" />
              {e.description}
            </div>
          ))}
        </>
      )}
    </div>
  );
}
