from __future__ import annotations

from typing import Any


def normalize_bbox(bbox: Any) -> dict[str, float] | None:
    if not isinstance(bbox, dict):
        return None

    keys = ("x1", "y1", "x2", "y2")
    try:
        values = {key: float(bbox[key]) for key in keys}
    except Exception:
        return None

    if values["x1"] < 0 or values["y1"] < 0 or values["x2"] < 0 or values["y2"] < 0:
        return None
    if values["x1"] > 1 or values["y1"] > 1 or values["x2"] > 1 or values["y2"] > 1:
        return None
    if values["x2"] <= values["x1"] or values["y2"] <= values["y1"]:
        return None

    return values

