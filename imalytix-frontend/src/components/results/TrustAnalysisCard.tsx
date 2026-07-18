import { AlertTriangle, ShieldCheck, ShieldX } from "lucide-react";
import type { TrustAnalysis } from "../../types/analysis";

function RiskBar({ score, color }: { score: number; color: string }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
      <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${Math.min(score, 100)}%` }} />
    </div>
  );
}

export default function TrustAnalysisCard({ trust }: { trust: TrustAnalysis }) {
  const isRisky = trust.combined_risk_score >= 40;
  const isSafe = trust.combined_risk_score < 20;

  const Icon = isSafe ? ShieldCheck : isRisky ? ShieldX : AlertTriangle;
  const iconColor = isSafe ? "text-emerald-500" : isRisky ? "text-rose-500" : "text-amber-500";
  const borderColor = isSafe ? "border-emerald-100" : isRisky ? "border-rose-100" : "border-amber-100";
  const bgColor = isSafe ? "bg-emerald-50" : isRisky ? "bg-rose-50" : "bg-amber-50";

  return (
    <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="section-title mb-4">신뢰성 분석</div>

      {/* 종합 신뢰도 */}
      <div className={`mb-4 flex items-center gap-3 rounded-2xl border p-4 ${borderColor} ${bgColor}`}>
        <Icon className={`h-5 w-5 shrink-0 ${iconColor}`} />
        <div>
          <div className="text-sm font-semibold text-slate-800">{trust.label}</div>
          <div className="text-xs text-slate-500">신뢰 점수 {trust.trust_score}점 · 위험도 {trust.combined_risk_score}점</div>
        </div>
        <div className="ml-auto text-2xl font-bold text-slate-900">{trust.trust_score}</div>
      </div>

      {/* 위험 항목 */}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>도용 위험도</span>
            <span className="font-semibold text-slate-700">{trust.theft_risk_score}점</span>
          </div>
          <RiskBar score={trust.theft_risk_score} color={trust.theft_risk_score >= 40 ? "bg-rose-400" : trust.theft_risk_score >= 20 ? "bg-amber-400" : "bg-emerald-400"} />
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>편집·위변조 위험도</span>
            <span className="font-semibold text-slate-700">{trust.forgery_risk_score}점</span>
          </div>
          <RiskBar score={trust.forgery_risk_score} color={trust.forgery_risk_score >= 40 ? "bg-rose-400" : trust.forgery_risk_score >= 20 ? "bg-amber-400" : "bg-emerald-400"} />
        </div>
      </div>

      {/* 신호 목록 — 도용/편집 이유 설명 포함 */}
      {trust.signals.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-widest">탐지 신호 (도용 의심 근거)</div>
          {trust.signals.map((s) => {
            const isTheft = ["pHash 중복", "pHash 유사", "embedding 유사도", "복제/재업로드", "출처 패턴", "출처 귀속", "이미지 기반 출처 추적"].includes(s.name);
            const isForgery = ["생성형 메타데이터", "전용 탐지기", "Vision 모델", "시각적 근거"].includes(s.name);
            return (
              <div key={s.name} className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2.5">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <span className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${isTheft ? "bg-amber-100 text-amber-700" : isForgery ? "bg-violet-100 text-violet-700" : "bg-slate-100 text-slate-500"}`}>
                      {isTheft ? "도용" : isForgery ? "위변조" : "기타"}
                    </span>
                    <span className="text-xs font-semibold text-slate-700">{s.name}</span>
                  </div>
                  <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold ${s.score >= 40 ? "bg-rose-100 text-rose-600" : s.score >= 20 ? "bg-amber-100 text-amber-600" : "bg-emerald-100 text-emerald-600"}`}>
                    +{s.score}
                  </span>
                </div>
                <div className="mt-1 text-[11px] leading-4 text-slate-500">{s.description}</div>
              </div>
            );
          })}
        </div>
      )}

      {/* 근거 문장 */}
      {trust.evidence.length > 0 && (
        <div className="mt-3 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2.5 space-y-1">
          <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mb-1.5">상세 근거</div>
          {trust.evidence.map((e) => (
            <div key={e} className="flex items-start gap-1.5 text-[11px] text-slate-600">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-300" />
              {e}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
