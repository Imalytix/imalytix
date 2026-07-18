from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from PIL import Image, ImageFilter, ImageStat

from app.config import Settings, get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class EmbeddingCandidate:
    phash: str
    strategy: str
    similarity: float
    source_url: str | None = None
    filename: str | None = None
    category: str | None = None
    label: str | None = None
    mode: str | None = None
    distance: float | None = None


def _normalize(values: Iterable[float]) -> list[float]:
    vector = [float(v) for v in values]
    norm = math.sqrt(sum(v * v for v in vector))
    if not norm:
        return [0.0 for _ in vector]
    return [round(v / norm, 6) for v in vector]


def _flatten_image(image: Image.Image, size: int = 32) -> list[float]:
    resized = image.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    pixels = list(resized.getdata())
    vector: list[float] = []
    for r, g, b in pixels:
        vector.extend((r / 255.0, g / 255.0, b / 255.0))
    return vector


def _grayscale_profile(image: Image.Image, size: int = 32) -> list[float]:
    resized = image.convert("L").resize((size, size), Image.Resampling.LANCZOS)
    return [p / 255.0 for p in resized.getdata()]


def _edge_profile(image: Image.Image, size: int = 32) -> list[float]:
    gray = image.convert("L").resize((size, size), Image.Resampling.LANCZOS).filter(ImageFilter.FIND_EDGES)
    return [p / 255.0 for p in gray.getdata()]


def _histogram_profile(image: Image.Image, bins: int = 8) -> list[float]:
    rgb = image.convert("RGB")
    hist = rgb.histogram()
    channel_vectors = []
    step = max(1, 256 // bins)
    for channel in range(3):
        channel_hist = hist[channel * 256 : (channel + 1) * 256]
        buckets = [sum(channel_hist[i : i + step]) for i in range(0, 256, step)]
        total = sum(buckets) or 1
        channel_vectors.extend([bucket / total for bucket in buckets])
    return channel_vectors


def _stat_profile(image: Image.Image) -> list[float]:
    rgb = image.convert("RGB")
    stat = ImageStat.Stat(rgb)
    mean = [v / 255.0 for v in stat.mean[:3]]
    stddev = [v / 255.0 for v in stat.stddev[:3]]
    width, height = rgb.size
    aspect = width / height if height else 1.0
    return [*mean, *stddev, min(aspect / 4.0, 2.0), min(max(width, height) / 2048.0, 1.0)]


def _legacy_baseline_embedding(image: Image.Image, strategy: str) -> list[float]:
    """
    Phase A에서 쓰던 경량 baseline 임베딩(실제 DINOv2/CLIP이 아님).

    히스토그램/그레이스케일/엣지/통계값을 손으로 조합한 "가짜" 임베딩으로,
    실모델을 붙이기 전 파이프라인(벡터 저장/유사도 검색/캐시)을 미리
    검증하기 위한 용도였다. EMBEDDING_MODEL_BACKEND=real이 기본값이 되면
    이 함수는 실모델 로딩이 실패했을 때의 안전한 폴백으로만 남는다.

    - dino 자리: 구조/엣지 중심 특징 (실제 DINOv2의 저수준 특징 역할을 흉내)
    - clip 자리: 색상/히스토그램 중심 특징 (실제 CLIP의 의미 특징 역할을 흉내)
    """
    if strategy == "clip":
        vector = [
            *_histogram_profile(image, bins=8),
            *_flatten_image(image, size=16),
            *_stat_profile(image),
        ]
    else:
        vector = [
            *_grayscale_profile(image, size=32),
            *_edge_profile(image, size=32),
            *_stat_profile(image),
        ]

    return _normalize(vector)


def build_embedding(
    image: Image.Image,
    strategy: str = "dino",
    settings: Settings | None = None,
) -> list[float]:
    """
    이미지를 임베딩 벡터(list[float])로 변환한다.

    settings.embedding_model_backend에 따라 두 가지로 갈린다.
    - "real"   : 실제 DINOv2(dino) / OpenCLIP(clip) 모델을 로드해서 사용한다.
                 최초 호출 시 가중치 다운로드가 발생할 수 있다.
    - "legacy" : 기존 Phase A 경량 baseline을 그대로 사용한다(기본값).

    settings를 명시적으로 넘기지 않으면 get_settings()로 전역 설정을 읽는다.
    (analysis_service.py처럼 이미 Settings 인스턴스를 들고 있는 호출부는
     그대로 넘겨주는 것을 권장 — 매 호출마다 환경변수를 다시 읽지 않도록)
    """
    active_settings = settings or get_settings()

    if active_settings.embedding_model_backend == "real":
        try:
            if strategy == "clip":
                from app.services.embedding_models.clip_model import encode_image as clip_encode

                return clip_encode(
                    image,
                    model_name=active_settings.clip_model_name,
                    pretrained_tag=active_settings.clip_pretrained_tag,
                    device=active_settings.embedding_device,
                )
            else:
                from app.services.embedding_models.dinov2_model import encode_image as dino_encode

                return dino_encode(
                    image,
                    model_name=active_settings.dinov2_model_name,
                    device=active_settings.embedding_device,
                )
        except Exception:
            # 실모델 로딩/추론 실패(의존성 미설치, 네트워크 오류 등) 시
            # 서비스 전체가 죽지 않도록 legacy baseline으로 안전하게 폴백한다.
            # 단, 조용히 넘어가면 원인 파악이 어려우므로 반드시 로그를 남긴다.
            logger.exception(
                "[embedding] 실모델(%s) 임베딩 실패 → legacy baseline으로 폴백합니다.",
                strategy,
            )
            return _legacy_baseline_embedding(image, strategy)

    return _legacy_baseline_embedding(image, strategy)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return max(0.0, min(1.0, sum(a * b for a, b in zip(left, right))))
