"""
DINOv2 실모델 임베딩 어댑터.

DINOv2는 라벨 없이(자기지도 학습) 이미지만으로 학습된 비전 트랜스포머라
색상/의미보다 "구조·질감·경계" 같은 저수준 시각 특징을 CLIP보다
세밀하게 보존한다. Imalytix에서는 이 특성을 이용해
① 크롭/리사이즈/재압축된 재업로드 이미지를 찾아내는 유사도 검색과
② (향후) AI 생성 이미지 특유의 미세한 질감 이상 탐지에 활용한다.

모델: facebook/dinov2-small (ViT-S/14, 임베딩 차원 384)
      설정값(app.config.Settings.dinov2_model_name)으로 교체 가능.

주의:
- 이 모듈은 최초 호출 시점에 Hugging Face 허브에서 가중치를 내려받는다.
  네트워크/디스크 비용이 발생하므로, 반드시
  EMBEDDING_MODEL_BACKEND=real 로 명시적으로 켰을 때만 로드되도록
  embedding_service.py 쪽에서 게이팅한다.
- torch/transformers import를 함수 내부로 미뤄서, legacy 모드에서는
  이 라이브러리들이 아예 메모리에 올라오지 않게 한다.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    # 타입 체커만 보는 가짜 import. 런타임에는 실행되지 않는다.
    import torch
    from transformers import AutoImageProcessor, AutoModel


@lru_cache(maxsize=1)
def _load_dinov2(model_name: str, device: str):
    """
    DINOv2 프로세서 + 모델을 한 번만 로드해서 프로세스 전역에 캐싱한다.

    lru_cache를 쓰는 이유:
    - 요청마다 수백 MB짜리 모델을 다시 로드하면 지연시간이 폭발한다.
    - FastAPI는 보통 워커 프로세스 하나가 여러 요청을 처리하므로,
      "모델은 프로세스당 1회 로드"가 표준적인 패턴이다.
    """
    import torch  # noqa: PLC0415 (의도적 지연 import)
    from transformers import AutoImageProcessor, AutoModel

    processor = AutoImageProcessor.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.to(device)
    model.eval()  # 추론 전용: dropout/배치정규화 등을 비활성화
    return processor, model, torch


def encode_image(image: Image.Image, *, model_name: str, device: str = "cpu") -> list[float]:
    """
    PIL 이미지를 DINOv2 임베딩 벡터(list[float])로 변환한다.

    반환값은 embedding_service.build_embedding()의 기존 반환 형태(list[float])와
    동일한 인터페이스를 유지해서, vector_store/aggregator 등 하위 계층은
    "임베딩이 진짜 모델에서 나왔는지 baseline에서 나왔는지" 신경 쓸 필요가 없다.
    """
    processor, model, torch = _load_dinov2(model_name, device)

    # 1) 전처리: 리사이즈/정규화는 모델이 학습된 방식과 동일하게 processor가 처리한다.
    inputs = processor(images=image.convert("RGB"), return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}

    # 2) 추론: 그래디언트 계산 비활성화로 메모리/속도 절약.
    with torch.no_grad():
        outputs = model(**inputs)

    # 3) DINOv2는 ViT 구조라 last_hidden_state[:, 0, :]이 CLS 토큰이다.
    #    CLS 토큰은 이미지 전체를 요약하는 대표 벡터로 흔히 쓰인다.
    cls_embedding = outputs.last_hidden_state[:, 0, :]

    # 4) L2 정규화: 코사인 유사도 비교를 단순화하기 위해 벡터 길이를 1로 맞춘다.
    #    (embedding_service.cosine_similarity가 내적만으로 유사도를 계산하므로 필수)
    normalized = torch.nn.functional.normalize(cls_embedding, p=2, dim=-1)

    return normalized.squeeze(0).cpu().tolist()
