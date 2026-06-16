import { useEffect, useRef } from "react";
import { scoreColor, scoreTrackColor, getScoreLabel } from "../shared/utils/score";

interface Props { score: number; size?: number; }

export default function ScoreGauge({ score, size = 140 }: Props) {
  const circleRef = useRef<SVGCircleElement | null>(null);
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference - (clamped / 100) * circumference;
  const color = scoreColor(clamped);
  const track = scoreTrackColor(clamped);

  useEffect(() => {
    const el = circleRef.current;
    if (!el) return;
    el.style.strokeDashoffset = String(circumference);
    const f = requestAnimationFrame(() => {
      el.style.transition = "stroke-dashoffset 1s cubic-bezier(0.34,1.56,0.64,1)";
      el.style.strokeDashoffset = String(offset);
    });
    return () => cancelAnimationFrame(f);
  }, [offset, circumference]);

  return (
    <div className="flex flex-col items-center gap-2">
      <div style={{ width: size, height: size }} className="relative">
        <svg width={size} height={size} className="-rotate-90" style={{ display: "block" }}>
          <circle cx={center} cy={center} r={radius} fill="none" stroke={track} strokeWidth={10} />
          <circle
            ref={circleRef} cx={center} cy={center} r={radius} fill="none"
            stroke={color} strokeWidth={10} strokeLinecap="round"
            strokeDasharray={circumference} strokeDashoffset={circumference}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-0.5">
          <div className="text-2xl font-bold tracking-tight text-slate-900">{clamped}%</div>
          <div className="text-[10px] text-slate-400">AI 생성 가능성</div>
        </div>
      </div>
      <div className="rounded-full border px-3 py-1 text-xs font-semibold"
        style={{ color, borderColor: track, backgroundColor: track }}>
        {getScoreLabel(clamped)}
      </div>
    </div>
  );
}
