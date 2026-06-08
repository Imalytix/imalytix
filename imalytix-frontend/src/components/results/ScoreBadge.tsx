import clsx from "clsx";
import { getScoreLabel, getScoreTone } from "../../utils/score";

interface ScoreBadgeProps {
  score: number;
  className?: string;
}

export default function ScoreBadge({ score, className }: ScoreBadgeProps) {
  return (
    <div
      className={clsx(
        "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold shadow-sm",
        getScoreTone(score),
        className,
      )}
    >
      <span>{score}%</span>
      <span className="text-xs font-medium opacity-90">{getScoreLabel(score)}</span>
    </div>
  );
}
