"""
실제(real) 임베딩 모델 어댑터 패키지.

- dinov2_model.py : Hugging Face `facebook/dinov2-*` 기반 구조/텍스처 임베딩
- clip_model.py   : OpenCLIP 기반 의미(semantic) 임베딩

두 모듈 모두 torch/transformers/open_clip을 "함수 내부에서" import한다.
그래야 EMBEDDING_MODEL_BACKEND=legacy(기본값)로 운영할 때는
이 무거운 라이브러리가 전혀 로드되지 않는다.
"""
