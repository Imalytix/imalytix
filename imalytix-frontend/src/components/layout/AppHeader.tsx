import axios from "axios";
import { CircleDot } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

type Status = "checking" | "online" | "offline";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function checkHealth(): Promise<boolean> {
  try {
    const res = await axios.get(`${API_BASE_URL}/health`, { timeout: 4000 });
    return res.status === 200;
  } catch {
    return false;
  }
}

export default function AppHeader() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    checkHealth().then((ok) => setStatus(ok ? "online" : "offline"));
  }, []);

  const statusConfig = {
    checking: { dot: "text-slate-400 animate-pulse", label: "서버 확인 중…", bg: "border-slate-200 bg-slate-50 text-slate-500" },
    online: { dot: "text-emerald-500", label: "서버 연결됨", bg: "border-emerald-200 bg-emerald-50 text-emerald-700" },
    offline: { dot: "text-rose-500", label: "서버 오프라인", bg: "border-rose-200 bg-rose-50 text-rose-700" },
  } as const;

  const cfg = statusConfig[status];

  return (
    <header className="border-b border-slate-200/80 bg-white/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_10px_30px_rgba(15,23,42,0.08)]">
            <img src="/imalytix-logo.svg" alt="Imalytix 로고" className="h-full w-full object-cover" />
          </div>
          <div>
            <div className="text-lg font-semibold tracking-tight text-slate-900">Imalytix</div>
            <div className="text-xs text-slate-500">AI 이미지 판별 서비스</div>
          </div>
        </Link>

        <div className="flex items-center gap-3 text-xs">
          <Link
            to="/dev"
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 font-medium text-slate-500 hover:bg-slate-100"
          >
            개발자 대시보드
          </Link>
          <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 font-medium ${cfg.bg}`}>
            <CircleDot className={`h-3.5 w-3.5 ${cfg.dot}`} />
            {cfg.label}
          </span>
        </div>
      </div>
    </header>
  );
}
