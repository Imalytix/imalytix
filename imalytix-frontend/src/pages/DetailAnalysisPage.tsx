import { ArrowLeft, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import AppHeader from "../components/layout/AppHeader";
import PageContainer from "../components/layout/PageContainer";
import EmptyState from "../components/common/EmptyState";
import ImageCanvasWithBoxes from "../components/detail/ImageCanvasWithBoxes";
import SuspiciousRegionList from "../components/detail/SuspiciousRegionList";
import RegionDetailPanel from "../components/detail/RegionDetailPanel";
import ScoreBadge from "../components/results/ScoreBadge";
import { sampleAnalysisResult } from "../mock/sampleAnalysisResult";
import { samplePreviewImage } from "../mock/sampleImage";
import { loadAnalysisResult, loadImageDataUrl } from "../utils/storage";
import { toPercentageScore } from "../utils/score";

export default function DetailAnalysisPage() {
  const result = useMemo(() => loadAnalysisResult() ?? sampleAnalysisResult, []);
  const imageUrl = useMemo(() => loadImageDataUrl() ?? samplePreviewImage, []);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const regions = result.suspicious_regions ?? [];

  return (
    <div className="min-h-screen">
      <AppHeader />
      <PageContainer>
        <div className="mb-5 flex flex-wrap items-center justify-between gap-4 rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
          <div>
            <div className="section-title">상세 분석</div>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
              이미지 의심 부위 상세보기
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              이미지 내부의 의심 영역을 확인하고, 어떤 근거로 AI 생성물 가능성이 판단되었는지 볼 수 있습니다.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <ScoreBadge score={toPercentageScore(result.final_result.ai_probability)} />
            <Link
              to="/"
              className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            >
              <ArrowLeft className="h-4 w-4" />
              분석 요약으로
            </Link>
          </div>
        </div>

        <div className="mb-5 rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
          <div className="section-title">분석 근거 요약</div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {(result.evidence_summary ?? []).length > 0 ? (
              result.evidence_summary.map((item) => (
                <div
                  key={item}
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700"
                >
                  {item}
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                표시할 분석 근거가 없습니다.
              </div>
            )}
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-[0.25fr_0.5fr_0.25fr]">
          <section className="space-y-4">
            <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
              <div className="section-title">AI 의심 부위</div>
              <div className="mt-2 text-lg font-semibold text-slate-900">선택 목록</div>
            </div>
            {regions.length > 0 ? (
              <SuspiciousRegionList regions={regions} selectedIndex={selectedIndex} onSelectRegion={setSelectedIndex} />
            ) : (
              <EmptyState title="의심 부위가 없습니다." message="현재 분석 결과에는 bbox가 없는 상태입니다." />
            )}
          </section>

          <section className="space-y-4">
            <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
              <div className="flex items-center gap-2 text-slate-900">
                <Sparkles className="h-4 w-4 text-sky-500" />
                <span className="font-semibold">이미지 분석</span>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                벚꽃 사진처럼 현실적인 이미지에서도 의심 영역을 시각적으로 확인할 수 있습니다.
              </p>
            </div>
            <ImageCanvasWithBoxes
              imageUrl={imageUrl}
              regions={regions}
              selectedIndex={selectedIndex}
              onSelectRegion={setSelectedIndex}
            />
          </section>

          <section className="space-y-4">
            <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(15,23,42,0.05)]">
              <div className="section-title">선택 항목 설명</div>
              <div className="mt-2 text-lg font-semibold text-slate-900">상세 정보</div>
            </div>
            <RegionDetailPanel region={regions[selectedIndex]} regionIndex={selectedIndex} />
          </section>
        </div>
      </PageContainer>
    </div>
  );
}
