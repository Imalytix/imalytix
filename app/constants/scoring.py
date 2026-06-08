CONFIDENCE_WEIGHTS = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.4,
}

VISUAL_EVIDENCE_POINTS = {
    "high": 5,
    "medium": 3,
    "low": 1,
}

FINAL_LABELS = [
    (80, "AI 생성 가능성 높음", True, "high"),
    (60, "AI 생성 의심", True, "medium"),
    (31, "판단 불확실", None, "low"),
    (0, "실제 이미지 가능성 높음", False, "medium"),
]

