import ScoreBadge from "./ScoreBadge";

interface AggregatedResultSummaryProps {
  score: number;
  label: string;
  confidence: "low" | "medium" | "high";
}

export default function AggregatedResultSummary({
  score,
  label,
  confidence,
}: AggregatedResultSummaryProps) {
  return (
    <article className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">통합분석 결과</div>
          <div className="mt-2 text-lg font-semibold text-slate-900">최종 판단 요약</div>
        </div>
        <ScoreBadge score={score} />
      </div>

      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <div className="text-sm text-slate-500">최종 라벨</div>
        <div className="mt-2 text-2xl font-semibold text-slate-900">{label}</div>
        <div className="mt-2 text-sm text-slate-500">
          신뢰도: {confidence === "high" ? "높음" : confidence === "medium" ? "보통" : "낮음"}
        </div>
      </div>
    </article>
  );
}
