import { CheckCircle2, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

const STEPS = [
  { id: "validate", label: "이미지 검증", desc: "파일 형식 및 크기 확인" },
  { id: "metadata", label: "메타데이터 분석", desc: "EXIF · PNG · C2PA 흔적 탐색" },
  { id: "vision", label: "시각 분석", desc: "AI 특이 패턴 및 의심 부위 탐지" },
  { id: "aggregate", label: "결과 집계", desc: "점수 계산 및 근거 정리" },
];

const STEP_DURATIONS = [800, 1400, 3000, 600];

interface AnalysisStepsLoaderProps {
  active: boolean;
}

export default function AnalysisStepsLoader({ active }: AnalysisStepsLoaderProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!active) {
      setCurrentStep(0);
      setCompletedSteps(new Set());
      return;
    }

    let stepIndex = 0;
    const timers: ReturnType<typeof setTimeout>[] = [];

    function advance() {
      if (stepIndex >= STEPS.length) return;
      setCurrentStep(stepIndex);

      const duration = STEP_DURATIONS[stepIndex] ?? 1000;
      const t = setTimeout(() => {
        setCompletedSteps((prev) => new Set([...prev, stepIndex]));
        stepIndex += 1;
        advance();
      }, duration);
      timers.push(t);
    }

    advance();
    return () => timers.forEach(clearTimeout);
  }, [active]);

  if (!active) return null;

  return (
    <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
      <div className="mb-5 text-sm font-semibold text-slate-900">분석 진행 중…</div>
      <ol className="space-y-4">
        {STEPS.map((step, idx) => {
          const isDone = completedSteps.has(idx);
          const isActive = currentStep === idx && !isDone;
          const isPending = idx > currentStep;

          return (
            <li key={step.id} className="flex items-start gap-4">
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border">
                {isDone ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : isActive ? (
                  <Loader2 className="h-4 w-4 animate-spin text-sky-500" />
                ) : (
                  <span className="h-2 w-2 rounded-full bg-slate-200" />
                )}
              </div>
              <div>
                <div
                  className={
                    isDone
                      ? "text-sm font-medium text-emerald-700"
                      : isActive
                        ? "text-sm font-semibold text-slate-900"
                        : "text-sm text-slate-400"
                  }
                >
                  {step.label}
                </div>
                {(isDone || isActive) && !isPending ? (
                  <div className="mt-0.5 text-xs text-slate-400">{step.desc}</div>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
