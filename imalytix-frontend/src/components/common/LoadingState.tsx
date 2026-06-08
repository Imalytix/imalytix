import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  title?: string;
  description?: string;
}

export default function LoadingState({
  title = "분석 중입니다.",
  description = "이미지를 검사하고 결과를 정리하고 있습니다.",
}: LoadingStateProps) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-slate-500">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
        <div>
          <div className="text-base font-semibold text-slate-900">{title}</div>
          <div className="mt-1 text-sm text-slate-500">{description}</div>
        </div>
      </div>
    </div>
  );
}
