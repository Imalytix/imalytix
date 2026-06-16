import axios from "axios";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

const API = import.meta.env.VITE_API_BASE_URL || "/api/v1";

type ModelStatus = {
  configured: boolean;
  model: string;
  total_requests: number | null;
  success_count: number | null;
  error_count: number | null;
  success_rate: number | null;
  last_success: string | null;
  last_error: string | null;
  last_error_message: string | null;
};

type TestResult = {
  provider: string;
  status: "ok" | "error" | "not_configured" | "quota_exceeded" | "testing";
  message: string;
  latency_ms?: number;
};

type ErrorLog = { provider: string; message: string; timestamp: string };

const PROVIDER_LABELS: Record<string, { name: string; color: string }> = {
  openai: { name: "OpenAI GPT-4o", color: "violet" },
  gemini: { name: "Gemini 2.5 Flash", color: "blue" },
  claude: { name: "Claude Haiku", color: "amber" },
};

function statusDot(configured: boolean, test?: TestResult) {
  if (!configured) return { cls: "bg-slate-300", label: "미설정" };
  if (!test) return { cls: "bg-slate-400 animate-pulse", label: "미테스트" };
  if (test.status === "testing") return { cls: "bg-yellow-400 animate-pulse", label: "테스트 중…" };
  if (test.status === "ok") return { cls: "bg-emerald-500", label: "정상" };
  if (test.status === "quota_exceeded") return { cls: "bg-orange-400", label: "쿼터 초과" };
  return { cls: "bg-rose-500", label: "오류" };
}

function fmtTime(iso: string | null) {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleString("ko-KR", { timeZone: "Asia/Seoul", hour12: false });
}

export default function DevDashboardPage() {
  const [models, setModels] = useState<Record<string, ModelStatus>>({});
  const [tests, setTests] = useState<Record<string, TestResult>>({});
  const [errors, setErrors] = useState<ErrorLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<string>("");

  const fetchData = useCallback(async () => {
    try {
      const [mRes, eRes] = await Promise.all([
        axios.get(`${API}/health/models`),
        axios.get(`${API}/health/errors`),
      ]);
      setModels(mRes.data);
      setErrors(eRes.data.errors || []);
      setLastRefresh(new Date().toLocaleTimeString("ko-KR", { hour12: false }));
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 15000);
    return () => clearInterval(id);
  }, [fetchData]);

  const testModel = async (provider: string) => {
    setTests((p) => ({ ...p, [provider]: { provider, status: "testing", message: "테스트 중…" } }));
    try {
      const res = await axios.post(`${API}/health/test/${provider}`);
      setTests((p) => ({ ...p, [provider]: res.data }));
    } catch (e: any) {
      setTests((p) => ({
        ...p,
        [provider]: { provider, status: "error", message: e?.message || "요청 실패" },
      }));
    }
  };

  const testAll = () => Object.keys(PROVIDER_LABELS).forEach(testModel);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-slate-500">로딩 중…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-widest text-slate-400">Imalytix</div>
            <h1 className="text-2xl font-bold text-slate-900">개발자 대시보드</h1>
            <p className="mt-0.5 text-sm text-slate-500">API 연결 상태 및 에러 로그 모니터링</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">최근 갱신: {lastRefresh}</span>
            <button
              onClick={testAll}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              전체 테스트
            </button>
            <Link to="/" className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
              ← 메인으로
            </Link>
          </div>
        </div>

        {/* Model Status Cards */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {Object.entries(PROVIDER_LABELS).map(([key, meta]) => {
            const m = models[key] as ModelStatus | undefined;
            const test = tests[key];
            const dot = statusDot(m?.configured ?? false, test);
            return (
              <div key={key} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">{key}</div>
                    <div className="mt-0.5 font-semibold text-slate-900">{meta.name}</div>
                    <div className="mt-0.5 text-xs text-slate-400">{m?.model ?? "-"}</div>
                  </div>
                  <div className="flex items-center gap-1.5 rounded-full border border-slate-100 px-2.5 py-1">
                    <span className={`h-2 w-2 rounded-full ${dot.cls}`} />
                    <span className="text-xs font-medium text-slate-600">{dot.label}</span>
                  </div>
                </div>

                {/* 통계 */}
                <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-lg bg-slate-50 py-2">
                    <div className="text-lg font-bold text-slate-900">{m?.total_requests ?? 0}</div>
                    <div className="text-xs text-slate-400">총 요청</div>
                  </div>
                  <div className="rounded-lg bg-emerald-50 py-2">
                    <div className="text-lg font-bold text-emerald-700">{m?.success_count ?? 0}</div>
                    <div className="text-xs text-emerald-500">성공</div>
                  </div>
                  <div className="rounded-lg bg-rose-50 py-2">
                    <div className="text-lg font-bold text-rose-700">{m?.error_count ?? 0}</div>
                    <div className="text-xs text-rose-400">오류</div>
                  </div>
                </div>

                {m?.success_rate != null && (
                  <div className="mt-2">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>성공률</span><span>{m.success_rate}%</span>
                    </div>
                    <div className="mt-1 h-1.5 w-full rounded-full bg-slate-100">
                      <div
                        className="h-1.5 rounded-full bg-emerald-400 transition-all"
                        style={{ width: `${m.success_rate}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* 마지막 에러 */}
                {m?.last_error_message && (
                  <div className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-600 line-clamp-2">
                    {m.last_error_message}
                  </div>
                )}

                {/* 테스트 결과 */}
                {test && test.status !== "testing" && (
                  <div className={`mt-3 rounded-lg px-3 py-2 text-xs ${test.status === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-600"}`}>
                    {test.status === "ok" ? "✓ " : "✗ "}{test.message}
                    {test.latency_ms && <span className="ml-1 text-slate-400">({test.latency_ms}ms)</span>}
                  </div>
                )}

                <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                  <span>마지막 성공: {fmtTime(m?.last_success ?? null)}</span>
                  <button
                    onClick={() => testModel(key)}
                    disabled={tests[key]?.status === "testing"}
                    className="rounded-md bg-slate-100 px-2 py-1 text-slate-600 hover:bg-slate-200 disabled:opacity-50"
                  >
                    테스트
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Recent Errors */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-900">최근 에러 로그</h2>
            <span className="text-xs text-slate-400">최근 20건 · 서버 재시작 시 초기화</span>
          </div>
          {errors.length === 0 ? (
            <div className="mt-4 rounded-lg bg-emerald-50 py-6 text-center text-sm text-emerald-600">
              기록된 에러 없음 ✓
            </div>
          ) : (
            <div className="mt-3 space-y-2">
              {errors.map((e, i) => (
                <div key={i} className="flex items-start gap-3 rounded-lg bg-slate-50 px-3 py-2 text-xs">
                  <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 font-semibold uppercase
                    ${e.provider === "openai" ? "bg-violet-100 text-violet-700"
                    : e.provider === "gemini" ? "bg-blue-100 text-blue-700"
                    : "bg-amber-100 text-amber-700"}`}>
                    {e.provider}
                  </span>
                  <span className="flex-1 text-slate-600 break-all">{e.message}</span>
                  <span className="shrink-0 text-slate-400">{fmtTime(e.timestamp)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* API 끊김 원인 안내 */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-slate-900">API 연동 끊김 주요 원인</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            {[
              { tag: "크레딧 소진", desc: "Gemini 무료 할당량(1일 500회) 또는 선불 크레딧 소진 → AI Studio에서 충전 필요" },
              { tag: "빈 응답", desc: "OpenAI가 이미지 내용상 거부하거나 output_text가 null로 반환 → 다른 이미지로 재시도" },
              { tag: "JSON 파싱 실패", desc: "응답 토큰이 잘리거나 포맷이 다를 때 → max_tokens 늘리거나 프롬프트 단순화" },
              { tag: "Rate Limit", desc: "짧은 시간 내 반복 요청 시 일시 차단 → 잠시 후 재시도" },
              { tag: "타임아웃", desc: "60초 제한 초과 (고해상도 이미지) → 이미지 크기 줄이거나 timeout 늘리기" },
            ].map((item) => (
              <div key={item.tag} className="flex gap-3">
                <span className="shrink-0 rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">{item.tag}</span>
                <span>{item.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
