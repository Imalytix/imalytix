from __future__ import annotations

import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any] | None:
    if not text:
        return None

    # thinking 태그 제거 (Gemini 2.5 등)
    stripped = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL).strip()

    # 직접 파싱
    try:
        parsed = json.loads(stripped)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    # 코드블록 내 JSON 추출 (중첩 객체 포함)
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", stripped, re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1)
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            pass

    # 첫 { 부터 마지막 } 까지 추출
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        candidate = stripped[start : end + 1]
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    return None

