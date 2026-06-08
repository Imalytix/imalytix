import clsx from "clsx";
import { AlertCircle, CheckCircle2, FlaskConical, MinusCircle, TriangleAlert } from "lucide-react";
import { getConfidenceTone, toPercentageScore } from "../../utils/score";

interface ProviderResultCardProps {
  provider: string;
  modelName?: string;
  score: number;
  isAiGenerated: boolean | null;
  confidence: "low" | "medium" | "high";
  evidence: string[];
  limitations?: string[];
  rawScore?: number;
  isMock?: boolean;
  errorMessage?: string | null;
}

function VerdictIcon({ isAiGenerated }: { isAiGenerated: boolean | null }) {
  if (isAiGenerated === true) return <CheckCircle2 className="h-4 w-4 text-rose-500" />;
  if (isAiGenerated === false) return <MinusCircle className="h-4 w-4 text-emerald-500" />;
  return <TriangleAlert className="h-4 w-4 text-amber-500" />;
}

function verdictLabel(isAiGenerated: boolean | null) {
  if (isAiGenerated === true) return "AI 생성물 가능성 높음";
  if (isAiGenerated === false) return "실제 이미지 가능성 높음";
  return "판단 불확실";
}

export default function ProviderResultCard({
  provider,
  modelName,
  score,
  isAiGenerated,
  confidence,
  evidence,
  limitations = [],
  rawScore,
  isMock,
  errorMessage,
}: ProviderResultCardProps) {
  const percentage = toPercentageScore(score);
  const rawDisplay = rawScore ?? score;

  return (
    <article className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
      {/* 헤더 */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="text-base font-semibold text-slate-900">{provider}</div>
            {isMock && (
              <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-700">
                <FlaskConical className="h-3 w-3" />
                MOCK
              </span>
            )}
          </div>
          {modelName ? <div className="mt-1 text-xs text-slate-500">{modelName}</div> : null}
        </div>
        <div className={clsx("rounded-full border px-3 py-1 text-xs font-semibold", getConfidenceTone(confidence))}>
          신뢰도 {confidence === "high" ? "높음" : confidence === "medium" ? "보통" : "낮음"}
        </div>
      </div>

      {/* API 오류 배너 */}
      {errorMessage && (
        <div className="mt-3 flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" />
          <div>
            <div className="text-xs font-semibold text-rose-700">API 연동 실패</div>
            <div className="mt-0.5 text-xs text-rose-600">{errorMessage}</div>
          </div>
        </div>
      )}

      {/* Mock 안내 배너 */}
      {isMock && !errorMessage && (
        <div className="mt-3 flex items-start gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3">
          <FlaskConical className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          <div className="text-xs text-amber-700">
            <span className="font-semibold">MOCK 응답</span>
            {" — "}실제 API를 호출하지 않은 가짜 응답입니다. 실제 분석을 원하면 <code className="rounded bg-amber-100 px-1">.env</code>에 <code className="rounded bg-amber-100 px-1">OPENAI_API_KEY</code>를 설정하세요.
          </div>
        </div>
      )}

      {/* 점수 & 판정 */}
      <div className="mt-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50">
            <VerdictIcon isAiGenerated={isAiGenerated} />
          </div>
          <div>
            <div className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400">판정</div>
            <div className="text-sm font-semibold text-slate-900">{verdictLabel(isAiGenerated)}</div>
          </div>
        </div>
        <div className="min-w-[128px] text-right">
          <div className="text-3xl font-semibold tracking-tight text-slate-900">{percentage}</div>
          <div className="text-xs text-slate-500">원본 값 {Number(rawDisplay).toFixed(3)}</div>
        </div>
      </div>

      {/* 점수 바 */}
      <div className="mt-4">
        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className={clsx(
              "h-full rounded-full transition-all",
              percentage >= 80
                ? "bg-rose-500"
                : percentage >= 60
                  ? "bg-amber-400"
                  : percentage >= 31
                    ? "bg-sky-400"
                    : "bg-emerald-400",
            )}
            style={{ width: `${Math.max(4, percentage)}%` }}
          />
        </div>
      </div>

      {/* 근거 & 한계 */}
      {!errorMessage && (
        <div className="mt-5 space-y-4">
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">주요 근거</div>
            {evidence.length > 0 ? (
              <ul className="space-y-2 text-sm leading-6 text-slate-700">
                {evidence.slice(0, 3).map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-sm text-slate-400">표시할 근거가 없습니다.</div>
            )}
          </div>

          {limitations.length > 0 && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">분석 한계</div>
              <ul className="space-y-2 text-sm leading-6 text-slate-500">
                {limitations.slice(0, 2).map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-300" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </article>
  );
}
