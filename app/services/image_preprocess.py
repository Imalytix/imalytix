from __future__ import annotations

import base64
import io

from PIL import Image, ImageOps

from app.config import Settings


def preprocess_image(image: Image.Image, settings: Settings) -> tuple[Image.Image, bytes, str]:
    normalized = ImageOps.exif_transpose(image)

    if normalized.mode in {"RGBA", "LA", "P"}:
        rgba = normalized.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        normalized = Image.alpha_composite(background, rgba).convert("RGB")
    else:
        normalized = normalized.convert("RGB")

    width, height = normalized.size
    long_side = max(width, height)
    if long_side > settings.image_long_side:
        scale = settings.image_long_side / float(long_side)
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        normalized = normalized.resize(new_size, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    normalized.save(buffer, format="JPEG", quality=92, optimize=True)
    normalized_bytes = buffer.getvalue()
    data_url = f"data:image/jpeg;base64,{base64.b64encode(normalized_bytes).decode('utf-8')}"
    return normalized, normalized_bytes, data_url

