import type { AnalysisResult } from "../../types/analysis";
import { toPercentageScore } from "../../utils/score";
import EmptyState from "../common/EmptyState";
import MetadataResultCard from "./MetadataResultCard";
import ProviderResultCard from "./ProviderResultCard";

interface ProviderResultGridProps {
  result: AnalysisResult | null;
}

export default function ProviderResultGrid({ result }: ProviderResultGridProps) {
  if (!result) {
    return (
      <EmptyState
        title="분석 결과가 없습니다."
        message="이미지를 업로드하면 엔진별 결과가 카드 형태로 표시됩니다."
      />
    );
  }

  const metadata = result.metadata_analysis;
  const visionResults = result.vision_results ?? [];
  const detectorResults = result.detector_results ?? [];

  return (
    <div className="space-y-6">
      {metadata ? (
        <MetadataResultCard
          exifFound={Boolean(metadata.exif_found)}
          pngMetadataFound={Boolean(metadata.png_metadata_found)}
          c2paFound={Boolean(metadata.c2pa_found)}
          aiToolDetected={Boolean(metadata.ai_tool_detected)}
          detectedTools={metadata.detected_tools ?? []}
          metadataScore={metadata.metadata_score ?? 0}
          evidence={metadata.evidence ?? []}
          limitations={metadata.limitations ?? []}
        />
      ) : null}

      <section className="space-y-4">
        <div className="section-title">AI 판단 엔진 결과</div>
        {visionResults.length > 0 ? (
          <div className="grid gap-4 xl:grid-cols-2">
            {visionResults.map((item) => (
              <ProviderResultCard
                key={`${item.provider}-${item.model_name ?? "model"}`}
                provider={item.provider}
                modelName={item.model_name}
                score={item.score}
                rawScore={item.score}
                isAiGenerated={item.is_ai_generated}
                confidence={item.confidence}
                evidence={item.evidence.map((e) => e.description)}
                limitations={item.limitations}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            title="표시할 엔진 결과가 없습니다."
            message="샘플 데이터가 비어 있거나 quick 모드에서 생략된 경우입니다."
          />
        )}
      </section>

      <section className="space-y-4">
        <div className="section-title">전용 탐지기 결과</div>
        {detectorResults.length > 0 ? (
          <div className="grid gap-4 xl:grid-cols-2">
            {detectorResults.map((item) => (
              <ProviderResultCard
                key={`${item.provider}-${item.detector_type ?? "detector"}`}
                provider={item.provider}
                modelName={item.detector_type}
                score={toPercentageScore(item.score)}
                rawScore={item.score}
                isAiGenerated={item.is_ai_generated}
                confidence={item.confidence}
                evidence={["전용 탐지 API 점수 기반 결과입니다."]}
                limitations={["추후 Hive / Sightengine / Reality Defender 연동 예정입니다."]}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            title="표시할 전용 탐지기 결과가 없습니다."
            message="현재 MVP에서는 전용 탐지 API 연동을 보류한 상태입니다."
          />
        )}
      </section>
    </div>
  );
}
