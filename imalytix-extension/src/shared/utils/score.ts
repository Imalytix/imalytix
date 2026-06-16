export function toPercentageScore(score: number | undefined | null): number {
  if (score === undefined || score === null || Number.isNaN(score)) return 0;
  if (score <= 1) return Math.round(score * 100);
  return Math.round(Math.min(score, 100));
}

export function getScoreLabel(score: number): string {
  if (score >= 80) return "AI 생성물 가능성 높음";
  if (score >= 60) return "AI 생성 의심";
  if (score >= 31) return "판단 불확실";
  return "실제 이미지 가능성 높음";
}

export function scoreColor(score: number): string {
  if (score >= 80) return "#f43f5e";
  if (score >= 60) return "#f59e0b";
  if (score >= 31) return "#38bdf8";
  return "#34d399";
}

export function scoreTrackColor(score: number): string {
  if (score >= 80) return "#ffe4e6";
  if (score >= 60) return "#fef3c7";
  if (score >= 31) return "#e0f2fe";
  return "#d1fae5";
}

export function scoreBgClass(score: number): string {
  if (score >= 80) return "bg-rose-50 border-rose-200 text-rose-800";
  if (score >= 60) return "bg-amber-50 border-amber-200 text-amber-800";
  if (score >= 31) return "bg-sky-50 border-sky-200 text-sky-800";
  return "bg-emerald-50 border-emerald-200 text-emerald-800";
}
