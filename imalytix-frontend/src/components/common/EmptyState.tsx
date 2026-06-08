import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  message: string;
  action?: ReactNode;
}

export default function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-slate-400">
        <Inbox className="h-6 w-6" />
      </div>
      <div className="mt-4 text-lg font-semibold text-slate-900">{title}</div>
      <div className="mt-2 text-sm leading-6 text-slate-500">{message}</div>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
