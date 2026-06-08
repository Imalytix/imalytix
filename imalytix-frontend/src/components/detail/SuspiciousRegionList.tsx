import clsx from "clsx";
import type { SuspiciousRegion } from "../../types/analysis";

interface SuspiciousRegionListProps {
  regions: SuspiciousRegion[];
  selectedIndex: number;
  onSelectRegion: (index: number) => void;
}

const severityTone: Record<"low" | "medium" | "high", string> = {
  low: "border-emerald-200 bg-emerald-50 text-emerald-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  high: "border-rose-200 bg-rose-50 text-rose-700",
};

const severityLabel: Record<"low" | "medium" | "high", string> = {
  low: "낮음",
  medium: "보통",
  high: "높음",
};

export default function SuspiciousRegionList({
  regions,
  selectedIndex,
  onSelectRegion,
}: SuspiciousRegionListProps) {
  return (
    <div className="space-y-3">
      {regions.map((region, index) => (
        <button
          key={`${region.label}-${index}`}
          type="button"
          onClick={() => onSelectRegion(index)}
          className={clsx(
            "w-full rounded-[24px] border p-4 text-left transition",
            selectedIndex === index
              ? "border-slate-300 bg-white shadow-[0_10px_30px_rgba(15,23,42,0.05)]"
              : "border-slate-200 bg-white hover:border-slate-300",
          )}
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-slate-50 font-semibold text-slate-700">
                {index + 1}
              </div>
              <div>
                <div className="font-semibold text-slate-900">{region.label}</div>
                <div className="mt-1 text-xs text-slate-500">{region.description}</div>
              </div>
            </div>
            <span className={clsx("rounded-full border px-3 py-1 text-xs font-medium", severityTone[region.severity])}>
              {severityLabel[region.severity]}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}
