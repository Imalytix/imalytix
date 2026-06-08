from __future__ import annotations


def analyze_ocr(*args, **kwargs) -> dict:
    return {
        "text_found": False,
        "texts": [],
        "urls": [],
        "qr_detected": False,
    }

