from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

from app.constants.mime_types import ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES
from app.utils.errors import ImageValidationError


@dataclass(slots=True)
class LoadedImage:
    image: Image.Image
    image_bytes: bytes
    mime_type: str
    width: int
    height: int
    format_name: str


def _guess_mime_type(format_name: str | None) -> str:
    mapping = {"JPEG": "image/jpeg", "JPG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    return mapping.get((format_name or "").upper(), "application/octet-stream")


def validate_image_bytes(image_bytes: bytes, mime_type: str | None = None, filename: str | None = None) -> LoadedImage:
    if not image_bytes:
        raise ImageValidationError("이미지 데이터가 비어 있습니다.")

    if filename:
        ext = filename[filename.rfind(".") :].lower() if "." in filename else ""
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise ImageValidationError("허용되지 않은 파일 확장자입니다.")

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.verify()
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.load()
            format_name = (img.format or "").upper()
            loaded = img.copy()
    except UnidentifiedImageError as exc:
        raise ImageValidationError("이미지로 디코딩할 수 없습니다.") from exc
    except Exception as exc:
        raise ImageValidationError("이미지 검증 중 오류가 발생했습니다.") from exc

    detected_mime = _guess_mime_type(format_name)
    final_mime = mime_type or detected_mime

    if final_mime not in ALLOWED_MIME_TYPES:
        raise ImageValidationError("허용되지 않은 이미지 MIME 타입입니다.")

    width, height = loaded.size
    return LoadedImage(
        image=loaded,
        image_bytes=image_bytes,
        mime_type=final_mime,
        width=width,
        height=height,
        format_name=format_name or "UNKNOWN",
    )
