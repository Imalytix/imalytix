from __future__ import annotations


def has_strong_metadata_evidence(metadata_result: dict) -> bool:
    """
    Return True when metadata alone is strong enough to skip a vision call.

    In quick mode we want to save latency/cost whenever the file already has
    decisive AI-generation clues such as Stable Diffusion parameters or a very
    strong metadata score.
    """
    score = int(metadata_result.get("metadata_score", 0) or 0)
    if score >= 35:
        return True
    if metadata_result.get("ai_tool_detected"):
        return True
    evidence = metadata_result.get("evidence") or []
    return any("Stable Diffusion" in str(item) or "ComfyUI" in str(item) or "EXIF Software" in str(item) for item in evidence)


def has_strong_embedding_evidence(
    embedding_result: dict | None,
    *,
    similarity_threshold: float = 0.97,
) -> bool:
    """
    pHash → DINOv2/CLIP 임베딩 단계의 결과만으로 3-LLM 호출을
    생략해도 될 만큼 확신이 강한지 판단한다.

    has_strong_metadata_evidence()와 같은 자리(quick 모드의 지름길)에
    새로 추가하는 "임베딩 레이어" 게이트다. 흐름상으로는
    pHash → 임베딩 유사도 검색 → (여기서 게이팅) → 3-LLM 순서로 들어간다.

    True를 반환하는 조건(둘 다 만족해야 함):
    1. 가장 유사한 기존 이미지와의 코사인 유사도가 매우 높다
       (거의 동일 이미지 = 크롭/리사이즈/재압축 수준의 변형만 있음)
    2. 그 매칭에 "label"이 붙어 있다 (label이 없으면 뭘 근거로
       스킵하는지 알 수 없으므로 절대 스킵하지 않는다)

    주의: 이 함수가 True를 반환해도 실제로 스킵할지는
    decide_routing()이 settings.embedding_routing_shortcut_enabled
    플래그로 한 번 더 감싼다. 오탐(잘못된 라벨 재사용) 위험이 있으므로
    기본값은 OFF이고, 팀 검토 후에만 켠다.
    """
    if not embedding_result:
        return False

    best_similarity = float(embedding_result.get("best_similarity") or 0.0)
    top_hits = embedding_result.get("top_hits") or []
    if not top_hits:
        return False

    top_label = top_hits[0].get("label") if isinstance(top_hits[0], dict) else getattr(top_hits[0], "label", None)
    if not top_label:
        return False

    return best_similarity >= similarity_threshold


def decide_routing(
    mode: str,
    metadata_result: dict,
    cache_hit: bool = False,
    has_openai_key: bool = True,
    has_gemini_key: bool = False,
    has_claude_key: bool = False,
    embedding_result: dict | None = None,
    embedding_routing_shortcut_enabled: bool = False,
    embedding_strong_similarity_threshold: float = 0.97,
) -> dict:
    """
    Decide which providers to call for the current request.

    The output is a small routing plan that the analysis pipeline uses to:
    - short-circuit on cache hits
    - skip expensive vision calls in quick mode when metadata is decisive
    - enable whichever providers are configured for the current environment
    """
    if cache_hit:
        return {
            "call_openai": False,
            "call_claude": False,
            "call_gemini": False,
            "prompt_type": "quick",
            "use_cache": True,
        }

    prompt_type = "standard"
    if mode == "quick":
        # Quick mode prefers latency savings and may skip vision calls entirely.
        prompt_type = "quick"
        if has_strong_metadata_evidence(metadata_result):
            return {
                "call_openai": False,
                "call_claude": False,
                "call_gemini": False,
                "prompt_type": prompt_type,
                "use_cache": False,
            }

        # ── 임베딩 레이어 게이트 (기본 OFF, 옵트인) ─────────────────
        # metadata만으로는 부족했지만, pHash+임베딩 유사도 검색에서
        # 이미 라벨이 붙은 이미지와 거의 동일하다고 판단되면
        # quick 모드에 한해 3-LLM 호출을 생략할 수 있다.
        if embedding_routing_shortcut_enabled and has_strong_embedding_evidence(
            embedding_result,
            similarity_threshold=embedding_strong_similarity_threshold,
        ):
            return {
                "call_openai": False,
                "call_claude": False,
                "call_gemini": False,
                "prompt_type": prompt_type,
                "use_cache": False,
            }
    elif mode == "deep":
        # Deep mode currently uses the standard prompt, but keeps the hook
        # open for future multi-stage / region-aware flows.
        prompt_type = "standard"

    # Default routing: call every provider that is available in env.
    return {
        "call_openai": has_openai_key,
        "call_gemini": has_gemini_key,
        "call_claude": has_claude_key,
        "prompt_type": prompt_type,
        "use_cache": False,
    }
