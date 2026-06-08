interface EvidencePanelProps {
  evidenceSummary: string[];
  limitations: string[];
}

export default function EvidencePanel({ evidenceSummary, limitations }: EvidencePanelProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-3xl border border-slate-700 bg-slate-950/80 p-5">
        <div className="section-title">분석 근거</div>
        <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-300">
          {evidenceSummary.length > 0 ? (
            evidenceSummary.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-2 h-1.5 w-1.5 rounded-full bg-cyan-300" />
                <span>{item}</span>
              </li>
            ))
          ) : (
            <li className="text-slate-500">요약 근거가 없습니다.</li>
          )}
        </ul>
      </div>
      <div className="rounded-3xl border border-slate-700 bg-slate-950/80 p-5">
        <div className="section-title">분석 한계</div>
        <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-400">
          {limitations.length > 0 ? (
            limitations.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-2 h-1.5 w-1.5 rounded-full bg-slate-500" />
                <span>{item}</span>
              </li>
            ))
          ) : (
            <li>분석 한계가 없습니다.</li>
          )}
        </ul>
      </div>
    </div>
  );
}

