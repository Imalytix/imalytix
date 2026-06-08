from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.config import Settings
from app.services.image_loader import LoadedImage, validate_image_bytes
from app.utils.errors import SecurityViolationError
from app.utils.security import validate_redirect_target, validate_safe_url


@dataclass(slots=True)
class DownloadedImage:
    loaded: LoadedImage
    source_url: str


async def download_image_from_url(url: str, settings: Settings) -> DownloadedImage:
    validate_safe_url(url)
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    headers = {"User-Agent": "Imalytix/0.1"}
    max_bytes = settings.max_file_size_bytes
    current_url = url
    redirects = 0

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, headers=headers) as client:
        while True:
            async with client.stream("GET", current_url) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    if redirects >= 3:
                        raise SecurityViolationError("Redirect 횟수가 너무 많습니다.")
                    location = response.headers.get("location")
                    if not location:
                        raise SecurityViolationError("Redirect Location 헤더가 없습니다.")
                    current_url = validate_redirect_target(current_url, location)
                    redirects += 1
                    continue

                if response.status_code >= 400:
                    raise SecurityViolationError(f"이미지 다운로드 실패: HTTP {response.status_code}")

                content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                if content_type and not content_type.startswith("image/"):
                    raise SecurityViolationError("이미지 Content-Type이 아닙니다.")

                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        raise SecurityViolationError("다운로드된 이미지가 너무 큽니다.")
                    chunks.append(chunk)

                content = b"".join(chunks)
                loaded = validate_image_bytes(content, mime_type=content_type or None, filename=urlparse(current_url).path)
                return DownloadedImage(loaded=loaded, source_url=current_url)
