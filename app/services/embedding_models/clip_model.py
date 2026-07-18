"""
OpenCLIP 실모델 임베딩 어댑터.

CLIP은 이미지-텍스트 쌍으로 학습돼서 "의미론적" 표현이 강하다.
전체 장면이 말이 되는지, 색상/구도/객체가 자연스러운지 같은
고차원 판단에 유리해서, DINOv2(저수준 구조)와 상호보완적으로 쓴다.

모델: open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
      설정값(app.config.Settings.clip_model_name / clip_pretrained_tag)으로 교체 가능.

주의사항은 dinov2_model.py와 동일하다:
- 최초 호출 시 가중치 다운로드 비용 발생 → EMBEDDING_MODEL_BACKEND=real일 때만 로드
- torch/open_clip import는 함수 내부로 미뤄서 legacy 모드에 영향 없게 한다
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    import torch  # noqa: F401


@lru_cache(maxsize=1)
def _load_clip(model_name: str, pretrained_tag: str, device: str):
    """
    OpenCLIP 모델 + 전처리 파이프라인을 한 번만 로드해서 캐싱한다.
    (DINOv2와 동일하게 프로세스당 1회 로드 패턴)
    """
    import open_clip  # noqa: PLC0415 (의도적 지연 import)
    import torch

    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name, pretrained=pretrained_tag
    )
    model.to(device)
    model.eval()
    return model, preprocess, torch


def encode_image(
    image: Image.Image,
    *,
    model_name: str = "ViT-B-32",
    pretrained_tag: str = "openai",
    device: str = "cpu",
) -> list[float]:
    """
    PIL 이미지를 OpenCLIP 이미지 임베딩 벡터(list[float])로 변환한다.
    dinov2_model.encode_image()와 동일한 인터페이스(list[float] 반환)를 지킨다.
    """
    model, preprocess, torch = _load_clip(model_name, pretrained_tag, device)

    # 1) OpenCLIP이 제공하는 전처리(리사이즈/정규화)를 그대로 사용해
    #    학습 시 입력 분포와 어긋나지 않게 한다.
    tensor = preprocess(image.convert("RGB")).unsqueeze(0).to(device)

    with torch.no_grad():
        # 2) encode_image()가 CLIP의 이미지 인코더 forward를 대신 호출해준다.
        image_features = model.encode_image(tensor)

        # 3) L2 정규화: DINOv2와 동일하게 코사인 유사도 계산을 단순화한다.
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

    return image_features.squeeze(0).cpu().tolist()
