from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from collections import Counter
import time
from typing import Any

from fastapi import HTTPException, UploadFile

from app.config import Settings
from app.schemas.response import AnalysisResponse, CacheInfo, FinalResult, InputInfo
from app.services.aggregator_service import aggregate_analysis
from app.services.image_downloader import download_image_from_url
from app.services.image_loader import validate_image_bytes
from app.services.image_preprocess import preprocess_image
from app.services.metadata_service import analyze_metadata
from app.services.embedding_service import build_embedding
from app.services.phash_service import generate_phash
from app.services.phash_store import get_phash_store
from app.services.vector_store import get_embedding_store
from app.services.router_policy import decide_routing, has_strong_metadata_evidence
from app.services.trust_analysis_service import build_trust_analysis
from app.services.source_attribution_service import analyze_source_attribution
from app.services.source_pattern_service import analyze_source_patterns
from app.services.visual_source_trace_service import build_visual_source_trace
from app.services.vision_models.claude_service import analyze_with_claude
from app.services.vision_models.gemini_service import analyze_with_gemini
from app.services.vision_models.openai_service import analyze_with_openai
from app.utils.errors import ImageValidationError, SecurityViolationError
from app.utils.logger import get_logger, log_json
from app.schemas.embedding import EmbeddingAnalysisResult, SimilarityHit
from app.services.tracking_service import track_analysis_event

logger = get_logger(__name__)
analysis_logger = get_logger("imalytix.analysis")


def make_request_id() -> str:
    return f"req_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def _round_ms(value: float) -> float:
    return round(value, 1)


def _normalize_image_subject(content_type: str | None) -> str:
    if content_type in {"face", "body"}:
        return "인물"
    if content_type == "landscape":
        return "배경"
    if content_type in {"object", "text", "animal", "other"}:
        return "사물"
    return "미상"


def _extract_content_type(result: Any) -> str | None:
    if isinstance(result, dict):
        value = result.get("content_type")
    else:
        value = getattr(result, "content_type", None)
    return str(value) if value else None


def _resolve_image_subject(vision_results: list[Any]) -> tuple[str, list[str]]:
    content_types = [content_type for result in vision_results if (content_type := _extract_content_type(result))]
    if not content_types:
        return "미상", []

    counts = Counter(_normalize_image_subject(content_type) for content_type in content_types)
    for preferred in ("인물", "배경", "사물"):
        if counts.get(preferred):
            return preferred, content_types
    return "미상", content_types


def _format_stage_timings(timings: dict[str, float]) -> dict[str, float]:
    return {key: _round_ms(value) for key, value in timings.items()}


def _log_analysis_summary(
    *,
    request_id: str,
    mode: str,
    input_type: str,
    input_size_bytes: int | None,
    loaded_image: Any,
    source_url: str | None,
    source_fetch_ms: float | None,
    cache_info: CacheInfo | None,
    final_response: AnalysisResponse,
    timings_ms: dict[str, float],
    provider_timings_ms: dict[str, float],
    total_elapsed_ms: float,
) -> None:
    subject_type, raw_content_types = _resolve_image_subject(final_response.vision_results)
    payload = {
        "event": "analysis.completed",
        "request_id": request_id,
        "mode": mode,
        "input_type": input_type,
        "file_size_bytes": input_size_bytes,
        "file_size_mb": round((input_size_bytes or 0) / (1024 * 1024), 3) if input_size_bytes else None,
        "mime_type": getattr(loaded_image, "mime_type", None),
        "image_width": getattr(loaded_image, "width", None),
        "image_height": getattr(loaded_image, "height", None),
        "image_subject_type": subject_type,
        "image_subject_raw_types": raw_content_types,
        "source_url": source_url,
        "source_fetch_ms": _round_ms(source_fetch_ms) if source_fetch_ms is not None else None,
        "cache_hit": bool(cache_info and cache_info.hit),
        "cache_match_type": cache_info.match_type if cache_info else None,
        "cache_distance": cache_info.distance if cache_info else None,
        "cache_similarity": cache_info.similarity if cache_info else None,
        "final_score": final_response.final_result.ai_probability,
        "final_label": final_response.final_result.label,
        "trust_score": final_response.trust_analysis.trust_score if final_response.trust_analysis else None,
        "recommended_action": final_response.recommended_action,
        "timings_ms": _format_stage_timings(timings_ms),
        "provider_timings_ms": _format_stage_timings(provider_timings_ms),
        "total_ms": _round_ms(total_elapsed_ms),
    }
    log_json(analysis_logger, payload)


async def _timed_provider_call(name: str, func, **kwargs):
    start = time.perf_counter()
    result = await func(**kwargs)
    elapsed = _round_ms((time.perf_counter() - start) * 1000)
    return name, result, elapsed


def _strip_bbox(regions: list[dict], return_bbox: bool) -> list[dict]:
    if return_bbox:
        return regions
    stripped: list[dict] = []
    for region in regions:
        if isinstance(region, dict):
            copied = dict(region)
            copied["bbox"] = None
            stripped.append(copied)
        else:
            stripped.append(region)
    return stripped


def build_final_response(
    *,
    request_id: str,
    mode: str,
    input_type: str,
    loaded_image: Any,
    phash: str,
    metadata_result,
    detector_results: list[dict],
    vision_results: list[dict],
    trust_analysis,
    source_result: dict | None,
    source_attribution,
    source_trace,
    embedding_analysis,
    aggregate_result: dict,
    return_bbox: bool,
    cache_info: CacheInfo | None = None,
) -> AnalysisResponse:
    final_result = aggregate_result["final_result"]
    vision_results = [
        {
            **result,
            "suspicious_regions": _strip_bbox(
                [dict(item) if isinstance(item, dict) else item for item in result.get("suspicious_regions", [])],
                return_bbox,
            ),
        }
        for result in vision_results
    ]

    return AnalysisResponse(
        product="Imalytix",
        request_id=request_id,
        mode=mode,
        input=InputInfo(
            type=input_type,
            mime_type=loaded_image.mime_type,
            width=loaded_image.width,
            height=loaded_image.height,
            phash=phash,
        ),
        final_result=FinalResult(
            is_ai_generated=final_result["is_ai_generated"],
            ai_probability=final_result["ai_probability"],
            label=final_result["label"],
            confidence=final_result["confidence"],
        ),
        metadata_analysis=metadata_result,
        source_attribution=source_attribution,
        source_trace=source_trace,
        embedding_analysis=embedding_analysis,
        detector_results=detector_results,
        vision_results=vision_results,
        trust_analysis=trust_analysis,
        evidence_summary=aggregate_result["evidence_summary"],
        suspicious_regions=_strip_bbox(
            [dict(item) if isinstance(item, dict) else item for item in aggregate_result["suspicious_regions"]],
            return_bbox,
        ),
        limitations=[
            "AI 생성 여부는 100% 단정할 수 없습니다.",
            "SNS를 거친 이미지는 메타데이터가 제거되었을 수 있습니다.",
            "메타데이터는 수정 가능하므로 단독 판정 근거로 사용하지 않습니다.",
            *aggregate_result["limitations"],
        ],
        recommended_action=aggregate_result["recommended_action"],
        cache_info=cache_info,
    )


async def analyze_image_bytes(
    *,
    image_bytes: bytes,
    mode: str,
    include_child_risk: bool,
    return_bbox: bool,
    source_url: str | None,
    filename: str | None,
    settings: Settings,
    input_type: str,
    input_size_bytes: int | None = None,
    source_fetch_ms: float | None = None,
) -> AnalysisResponse:
    timings_ms: dict[str, float] = {}
    provider_timings_ms: dict[str, float] = {}
    started_at = time.perf_counter()

    try:
        # 1) Validate the incoming bytes first so we can fail fast on bad input.
        step = time.perf_counter()
        loaded = validate_image_bytes(image_bytes, filename=filename)
        timings_ms["validate_ms"] = _round_ms((time.perf_counter() - step) * 1000)
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # 2) Normalize the image into a predictable format for every downstream step.
    step = time.perf_counter()
    normalized_image, normalized_bytes, _ = preprocess_image(loaded.image, settings)
    timings_ms["preprocess_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 3) Generate fingerprints for duplicate detection and similarity search.
    #    pHash(동일성) → DINOv2/CLIP 임베딩(구조/의미 유사도) 순서로 만든 뒤,
    #    이 결과는 아래 7)에서 유사도 검색에, 8)에서는 3-LLM 라우팅 판단에도 쓰인다.
    step = time.perf_counter()
    phash = generate_phash(normalized_image)
    # settings를 명시적으로 넘겨서, 매 호출마다 get_settings()로 환경변수를
    # 다시 읽지 않고 이 요청에서 이미 확정된 설정을 그대로 재사용한다.
    dino_embedding = build_embedding(normalized_image, strategy="dino", settings=settings)
    clip_embedding = build_embedding(normalized_image, strategy="clip", settings=settings)
    timings_ms["fingerprint_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 4) Open the local stores used for caching and vector retrieval.
    step = time.perf_counter()
    cache_store = get_phash_store(settings.phash_db_path) if settings.phash_cache_enabled else None
    embedding_store = get_embedding_store(settings.embedding_db_path) if settings.embedding_store_enabled else None
    timings_ms["store_init_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    cache_info = CacheInfo(
        enabled=bool(settings.phash_cache_enabled),
        hit=False,
        match_type=None,
        matched_phash=None,
        distance=None,
        similarity=None,
    )
    cached_response: AnalysisResponse | None = None

    # 5) If the same or a very similar image was already analyzed,
    #    reuse the cached result to avoid unnecessary API calls.
    step = time.perf_counter()
    if cache_store:
        cached_match = cache_store.find_best_match(
            phash=phash,
            mode=mode,
            max_distance=settings.phash_similarity_threshold,
        )
        if cached_match:
            cached_response = AnalysisResponse.model_validate(cached_match.payload)
            cached_response.request_id = make_request_id()
            cached_response.mode = mode
            cached_response.input = InputInfo(
                type=input_type,
                mime_type=loaded.mime_type,
                width=loaded.width,
                height=loaded.height,
                phash=phash,
            )
            cache_info = CacheInfo(
                enabled=True,
                hit=True,
                match_type="exact" if cached_match.distance == 0 else "similar",
                matched_phash=cached_match.phash,
                distance=cached_match.distance,
                similarity=cached_match.similarity,
            )
            cached_response.cache_info = cache_info
    timings_ms["cache_lookup_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    if cached_response is not None:
        # Cache hit path: return immediately with a fresh request id.
        total_elapsed_ms = _round_ms((time.perf_counter() - started_at) * 1000)
        _log_analysis_summary(
            request_id=cached_response.request_id,
            mode=mode,
            input_type=input_type,
            input_size_bytes=input_size_bytes or len(image_bytes),
            loaded_image=loaded,
            source_url=source_url,
            source_fetch_ms=source_fetch_ms,
            cache_info=cache_info,
            final_response=cached_response,
            timings_ms=timings_ms,
            provider_timings_ms=provider_timings_ms,
            total_elapsed_ms=total_elapsed_ms,
        )
        if total_elapsed_ms >= settings.analysis_slow_threshold_ms:
            logger.warning(
                "analysis_slow request_id=%s total_ms=%.1f cache_hit=%s",
                cached_response.request_id,
                total_elapsed_ms,
                True,
            )
        if settings.tracking_enabled:
            asyncio.ensure_future(
                track_analysis_event(
                    request_id=cached_response.request_id,
                    phash=phash,
                    file_size_bytes=input_size_bytes or len(image_bytes),
                    width=loaded.width,
                    height=loaded.height,
                    mime_type=loaded.mime_type,
                    ai_probability=cached_response.final_result.ai_probability,
                    final_label=cached_response.final_result.label,
                    confidence=cached_response.final_result.confidence,
                    is_ai_generated=cached_response.final_result.is_ai_generated,
                    input_type=input_type,
                    source_type=None,
                    mode=mode,
                    vision_models=[r["provider"] for r in (cached_response.vision_results or [])],
                    metadata_ai_flag=bool(
                        cached_response.metadata_analysis
                        and cached_response.metadata_analysis.ai_tool_detected
                    ),
                    total_ms=total_elapsed_ms,
                    cache_hit=True,
                    db_path=settings.tracking_db_path,
                )
            )
        return cached_response

    # 6) Extract metadata and source clues.
    #    This covers EXIF, PNG text chunks, file name hints, and URL patterns.
    step = time.perf_counter()
    metadata_result = analyze_metadata(
        loaded.image,
        source_url=source_url,
        filename=filename,
        image_format=loaded.format_name,
    )
    source_result = analyze_source_patterns(source_url)
    source_attribution = analyze_source_attribution(source_url, filename=filename)
    timings_ms["metadata_source_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 7) Search the vector store using both visual embeddings.
    step = time.perf_counter()
    embedding_hits: list[SimilarityHit] = []
    best_similarity = 0.0
    best_strategy: str | None = None
    if embedding_store:
        for strategy, embedding in (("dino", dino_embedding), ("clip", clip_embedding)):
            hits = embedding_store.search(
                phash=phash,
                strategy=strategy,
                embedding=embedding,
                top_k=settings.embedding_top_k,
                exclude_phash=phash,
            )
            if hits:
                top_hit = hits[0]
                if top_hit.similarity > best_similarity:
                    best_similarity = top_hit.similarity
                    best_strategy = strategy
                embedding_hits.extend(
                    [
                        SimilarityHit(
                            strategy=hit.strategy,
                            similarity=hit.similarity,
                            phash=hit.phash,
                            source_url=hit.source_url,
                            filename=hit.filename,
                            category=hit.category,
                            label=hit.label,
                            mode=hit.mode,
                            distance=hit.distance,
                        )
                        for hit in hits
                    ]
                )
    timings_ms["embedding_search_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    step = time.perf_counter()
    embedding_analysis = EmbeddingAnalysisResult(
        enabled=bool(embedding_store),
        strategies=["dino", "clip"] if embedding_store else [],
        top_hits=embedding_hits[: settings.embedding_top_k],
        best_similarity=best_similarity,
        best_strategy=best_strategy,
        notes=[
            "pHash는 동일성에 강하고, embedding은 크롭/리사이즈/약한 편집 유사도에 강합니다.",
            "EMBEDDING_MODEL_BACKEND 설정에 따라 실제 DINOv2/CLIP 또는 legacy baseline이 사용됩니다.",
        ]
        if embedding_store
        else [],
    )
    source_trace = build_visual_source_trace(
        phash=phash,
        embedding_hits=embedding_hits,
        top_k=settings.embedding_top_k,
    )
    timings_ms["embedding_trace_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 8) Decide which providers should run for this request.
    #    pHash → DINOv2/CLIP 임베딩(7번) 결과가 여기서 라우팅 판단에 반영된다.
    #    즉 실제 흐름은 pHash → 임베딩 레이어 → (게이팅) → 3-LLM 이다.
    step = time.perf_counter()
    routing = decide_routing(
        mode,
        metadata_result.model_dump(),
        cache_hit=False,
        has_openai_key=bool(settings.openai_api_key),
        has_gemini_key=bool(settings.gemini_api_key),
        has_claude_key=bool(settings.anthropic_api_key),
        embedding_result=embedding_analysis.model_dump(),
        embedding_routing_shortcut_enabled=settings.embedding_routing_shortcut_enabled,
        embedding_strong_similarity_threshold=settings.embedding_strong_similarity_threshold,
    )
    timings_ms["routing_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    detector_results: list[dict] = []
    vision_results: list[dict] = []

    # 9) Launch provider calls — OpenAI / Gemini / Claude in parallel.
    step = time.perf_counter()
    provider_tasks = []
    if routing.get("call_openai"):
        provider_tasks.append(
            _timed_provider_call(
                "openai",
                analyze_with_openai,
                image_bytes=normalized_bytes,
                mime_type="image/jpeg",
                prompt_type=routing["prompt_type"],
                settings=settings,
            )
        )
    if routing.get("call_gemini"):
        provider_tasks.append(
            _timed_provider_call(
                "gemini",
                analyze_with_gemini,
                image_bytes=normalized_bytes,
                mime_type="image/jpeg",
                prompt_type=routing["prompt_type"],
                settings=settings,
            )
        )
    if routing.get("call_claude"):
        provider_tasks.append(
            _timed_provider_call(
                "claude",
                analyze_with_claude,
                image_bytes=normalized_bytes,
                mime_type="image/jpeg",
                prompt_type=routing["prompt_type"],
                settings=settings,
            )
        )

    if provider_tasks:
        # Run providers in parallel so the slowest provider does not block the rest.
        for provider_name, provider_result, elapsed_ms in await asyncio.gather(*provider_tasks):
            provider_timings_ms[provider_name] = elapsed_ms
            vision_results.append(provider_result.model_dump())
    timings_ms["model_calls_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 10) Merge metadata, detector output, and vision output into a single score.
    step = time.perf_counter()
    aggregate_result = aggregate_analysis(
        metadata_result=metadata_result.model_dump(),
        detector_results=detector_results,
        vision_results=vision_results,
        source_result=source_result,
    )
    timings_ms["aggregate_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 11) Build the trust analysis layer, which summarizes how reliable the
    #     evidence is and how strong the final conclusion should be.
    step = time.perf_counter()
    trust_analysis = build_trust_analysis(
        phash=phash,
        mode=mode,
        source_url=source_url,
        filename=filename,
        metadata_result=metadata_result.model_dump(),
        detector_results=detector_results,
        vision_results=vision_results,
        source_result=source_result,
        source_attribution=source_attribution.model_dump(),
        source_trace=source_trace.model_dump(),
        embedding_analysis=embedding_analysis.model_dump(),
        phash_store=cache_store,
    )
    timings_ms["trust_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 12) Convert all internal analysis objects into the final API response.
    step = time.perf_counter()
    final_response = build_final_response(
        request_id=make_request_id(),
        mode=mode,
        input_type=input_type,
        loaded_image=loaded,
        phash=phash,
        metadata_result=metadata_result,
        detector_results=detector_results,
        vision_results=vision_results,
        trust_analysis=trust_analysis,
        source_result=source_result,
        source_attribution=source_attribution,
        source_trace=source_trace,
        embedding_analysis=embedding_analysis,
        aggregate_result=aggregate_result,
        return_bbox=return_bbox,
        cache_info=CacheInfo(
            enabled=bool(settings.phash_cache_enabled),
            hit=False,
            match_type=None,
            matched_phash=None,
            distance=None,
            similarity=None,
        ),
    )
    timings_ms["response_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 13) Save the result to the pHash cache so future duplicate lookups are fast.
    if cache_store:
        step = time.perf_counter()
        cache_store.save(
            phash=phash,
            mode=mode,
            response=final_response.model_dump(mode="json"),
        )
        timings_ms["cache_save_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 14) Save embeddings so this image can be matched again later.
    if embedding_store:
        step = time.perf_counter()
        source_category = source_attribution.source_type
        source_label = "ai_service" if source_attribution.known_ai_service else ("trusted" if source_attribution.trusted_source else "unknown")
        embedding_store.save(
            phash=phash,
            strategy="dino",
            embedding=dino_embedding,
            source_url=source_url,
            filename=filename,
            category=source_category,
            label=source_label,
            mode=mode,
        )
        embedding_store.save(
            phash=phash,
            strategy="clip",
            embedding=clip_embedding,
            source_url=source_url,
            filename=filename,
            category=source_category,
            label=source_label,
            mode=mode,
        )
        timings_ms["embedding_save_ms"] = _round_ms((time.perf_counter() - step) * 1000)

    # 15) Emit a structured log entry for observability.
    total_elapsed_ms = _round_ms((time.perf_counter() - started_at) * 1000)
    _log_analysis_summary(
        request_id=final_response.request_id,
        mode=mode,
        input_type=input_type,
        input_size_bytes=input_size_bytes or len(image_bytes),
        loaded_image=loaded,
        source_url=source_url,
        source_fetch_ms=source_fetch_ms,
        cache_info=final_response.cache_info,
        final_response=final_response,
        timings_ms=timings_ms,
        provider_timings_ms=provider_timings_ms,
        total_elapsed_ms=total_elapsed_ms,
    )
    if total_elapsed_ms >= settings.analysis_slow_threshold_ms:
        slowest_provider = max(provider_timings_ms, key=provider_timings_ms.get, default=None)
        logger.warning(
            "analysis_slow request_id=%s total_ms=%.1f slowest_provider=%s slowest_provider_ms=%s cache_hit=%s",
            final_response.request_id,
            total_elapsed_ms,
            slowest_provider,
            provider_timings_ms.get(slowest_provider) if slowest_provider else None,
            False,
        )

    # 16) Fire-and-forget tracking (non-blocking, pHash + 결과 텍스트만 저장).
    if settings.tracking_enabled:
        asyncio.ensure_future(
            track_analysis_event(
                request_id=final_response.request_id,
                phash=phash,
                file_size_bytes=input_size_bytes or len(image_bytes),
                width=loaded.width,
                height=loaded.height,
                mime_type=loaded.mime_type,
                ai_probability=final_response.final_result.ai_probability,
                final_label=final_response.final_result.label,
                confidence=final_response.final_result.confidence,
                is_ai_generated=final_response.final_result.is_ai_generated,
                input_type=input_type,
                source_type=getattr(source_attribution, "source_type", None),
                mode=mode,
                vision_models=[r["provider"] for r in vision_results],
                metadata_ai_flag=bool(metadata_result.ai_tool_detected),
                total_ms=total_elapsed_ms,
                cache_hit=False,
                db_path=settings.tracking_db_path,
            )
        )

    return final_response


async def analyze_uploaded_file(
    file: UploadFile | None,
    mode: str,
    include_child_risk: bool,
    return_bbox: bool,
    settings: Settings,
) -> AnalysisResponse:
    if not file:
        raise HTTPException(status_code=400, detail="file이 필요합니다.")

    image_bytes = await file.read()
    if len(image_bytes) > settings.max_file_size_bytes:
        raise HTTPException(status_code=400, detail="이미지 파일이 너무 큽니다.")

    return await analyze_image_bytes(
        image_bytes=image_bytes,
        mode=mode,
        include_child_risk=include_child_risk,
        return_bbox=return_bbox,
        source_url=None,
        filename=file.filename,
        settings=settings,
        input_type="file_upload",
        input_size_bytes=len(image_bytes),
    )


async def analyze_image_from_url(
    image_url: str,
    mode: str,
    include_child_risk: bool,
    return_bbox: bool,
    settings: Settings,
) -> AnalysisResponse:
    download_started = time.perf_counter()
    try:
        downloaded = await download_image_from_url(image_url, settings)
    except SecurityViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    download_elapsed_ms = _round_ms((time.perf_counter() - download_started) * 1000)

    return await analyze_image_bytes(
        image_bytes=downloaded.loaded.image_bytes,
        mode=mode,
        include_child_risk=include_child_risk,
        return_bbox=return_bbox,
        source_url=downloaded.source_url,
        filename=None,
        settings=settings,
        input_type="image_url",
        input_size_bytes=len(downloaded.loaded.image_bytes),
        source_fetch_ms=download_elapsed_ms,
    )
