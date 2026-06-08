#!/usr/bin/env python3
"""
download_samples.py
카테고리별 3장씩 총 30장의 샘플 이미지를 다운로드해 samples/ 에 저장한다.

우선순위:
  1. Unsplash API  (UNSPLASH_ACCESS_KEY 설정 시)
  2. Pexels API    (PEXELS_API_KEY 설정 시)
  3. source.unsplash.com 무키 폴백 (키워드 지원)
  4. picsum.photos 최종 폴백 (랜덤 시드 기반)
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from PIL import Image

# ──────────────────────────────────────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

import os

UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
PEXELS_KEY   = os.getenv("PEXELS_API_KEY", "").strip()

SAMPLES_DIR  = ROOT / "samples"
MANIFEST_PATH = SAMPLES_DIR / "manifest.json"
MAX_LONG_SIDE = 1200
DOWNLOAD_TIMEOUT = 30
MAX_RETRIES = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 카테고리 정의
# ──────────────────────────────────────────────────────────────────────────────
CATEGORIES: list[dict[str, Any]] = [
    {
        "id": "01_portraits",
        "label_ko": "인물",
        "keywords": ["portrait face", "smiling person", "elderly portrait"],
        "test_purposes": ["face detection", "emotion recognition", "AI portrait check"],
    },
    {
        "id": "02_landscape",
        "label_ko": "풍경",
        "keywords": ["mountain sunset", "ocean beach", "forest path"],
        "test_purposes": ["natural scene detection", "background analysis"],
    },
    {
        "id": "03_animals",
        "label_ko": "동물",
        "keywords": ["tiger wildlife", "cat closeup", "bird flying"],
        "test_purposes": ["animal detection", "texture analysis"],
    },
    {
        "id": "04_food",
        "label_ko": "음식",
        "keywords": ["bibimbap korean food", "pasta dish", "dessert cake"],
        "test_purposes": ["food classification", "color analysis"],
    },
    {
        "id": "05_architecture",
        "label_ko": "건축",
        "keywords": ["seoul skyline", "modern building", "old castle"],
        "test_purposes": ["building detection", "perspective analysis"],
    },
    {
        "id": "06_abstract",
        "label_ko": "추상",
        "keywords": ["geometric pattern", "abstract art", "fractal design"],
        "test_purposes": ["texture pattern", "AI art detection"],
    },
    {
        "id": "07_products",
        "label_ko": "제품",
        "keywords": ["sneakers white background", "headphones product", "watch product"],
        "test_purposes": ["product photography", "background removal"],
    },
    {
        "id": "08_text_ocr",
        "label_ko": "텍스트",
        "keywords": ["street sign", "handwritten note", "neon sign"],
        "test_purposes": ["OCR", "text detection", "AI text distortion check"],
    },
    {
        "id": "09_charts",
        "label_ko": "차트",
        "keywords": ["bar chart infographic", "dashboard graph", "data visualization"],
        "test_purposes": ["chart understanding", "AI infographic detection"],
    },
    {
        "id": "10_illustration",
        "label_ko": "일러스트",
        "keywords": ["watercolor painting", "digital illustration", "pixel art"],
        "test_purposes": ["illustration detection", "art style analysis"],
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# 다운로드 소스 구현
# ──────────────────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:40]


async def _fetch_with_retry(client: httpx.AsyncClient, url: str, headers: dict | None = None, params: dict | None = None) -> httpx.Response | None:
    for attempt in range(MAX_RETRIES):
        try:
            resp = await client.get(url, headers=headers or {}, params=params or {}, timeout=DOWNLOAD_TIMEOUT, follow_redirects=True)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                wait = 2 ** attempt
                log.warning("Rate limit (429). %d초 대기 후 재시도…", wait)
                await asyncio.sleep(wait)
            else:
                log.warning("HTTP %d: %s", resp.status_code, url)
                return None
        except Exception as exc:
            wait = 2 ** attempt
            log.warning("요청 실패 (시도 %d/%d): %s — %s초 대기", attempt + 1, MAX_RETRIES, exc, wait)
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(wait)
    return None


async def fetch_via_unsplash_api(client: httpx.AsyncClient, keyword: str) -> dict | None:
    if not UNSPLASH_KEY:
        return None
    resp = await _fetch_with_retry(
        client,
        "https://api.unsplash.com/photos/random",
        headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
        params={"query": keyword, "orientation": "landscape"},
    )
    if not resp:
        return None
    data = resp.json()
    img_url = data.get("urls", {}).get("regular") or data.get("urls", {}).get("full")
    if not img_url:
        return None
    return {
        "image_url": img_url,
        "source": "Unsplash",
        "source_url": data.get("links", {}).get("html", ""),
        "author": data.get("user", {}).get("name", "Unknown"),
        "author_url": data.get("user", {}).get("links", {}).get("html", ""),
        "license": "Unsplash License",
        "tags": [t["title"] for t in data.get("tags", [])[:5]],
    }


async def fetch_via_pexels_api(client: httpx.AsyncClient, keyword: str) -> dict | None:
    if not PEXELS_KEY:
        return None
    resp = await _fetch_with_retry(
        client,
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": keyword, "per_page": 3, "orientation": "landscape"},
    )
    if not resp:
        return None
    photos = resp.json().get("photos", [])
    if not photos:
        return None
    photo = photos[0]
    img_url = photo.get("src", {}).get("large") or photo.get("src", {}).get("original")
    if not img_url:
        return None
    return {
        "image_url": img_url,
        "source": "Pexels",
        "source_url": photo.get("url", ""),
        "author": photo.get("photographer", "Unknown"),
        "author_url": photo.get("photographer_url", ""),
        "license": "Pexels License",
        "tags": [],
    }


async def fetch_via_source_unsplash(client: httpx.AsyncClient, keyword: str) -> dict | None:
    """API 키 없이 source.unsplash.com 사용 (키워드 지원, 무인증)"""
    slug = _slugify(keyword)
    url = f"https://source.unsplash.com/1200x800/?{slug}"
    resp = await _fetch_with_retry(client, url)
    if not resp or len(resp.content) < 5000:
        return None
    return {
        "image_url": url,
        "source": "Unsplash (무키 폴백)",
        "source_url": f"https://unsplash.com/s/photos/{slug}",
        "author": "Unknown (Unsplash)",
        "author_url": "",
        "license": "Unsplash License",
        "tags": keyword.split(),
        "_image_bytes": resp.content,
    }


async def fetch_via_picsum(client: httpx.AsyncClient, seed: int) -> dict | None:
    """최종 폴백: picsum.photos (키워드 없음, 시드 기반 랜덤)"""
    url = f"https://picsum.photos/seed/{seed}/1200/800"
    resp = await _fetch_with_retry(client, url)
    if not resp or len(resp.content) < 5000:
        return None
    return {
        "image_url": url,
        "source": "Lorem Picsum (최종 폴백)",
        "source_url": "https://picsum.photos",
        "author": "Various (picsum)",
        "author_url": "https://picsum.photos",
        "license": "CC0 / Public Domain",
        "tags": [],
        "_image_bytes": resp.content,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 이미지 저장
# ──────────────────────────────────────────────────────────────────────────────

def resize_and_save(image_bytes: bytes, output_path: Path) -> tuple[int, int, int]:
    """리사이즈 후 JPEG 저장. (width, height, file_size_kb) 반환"""
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        w, h = img.size
        long_side = max(w, h)
        if long_side > MAX_LONG_SIDE:
            scale = MAX_LONG_SIDE / long_side
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
        w, h = img.size
        img.save(output_path, format="JPEG", quality=88, optimize=True)
    size_kb = output_path.stat().st_size // 1024
    return w, h, size_kb


# ──────────────────────────────────────────────────────────────────────────────
# 메인 다운로드 루틴
# ──────────────────────────────────────────────────────────────────────────────

async def download_one(
    client: httpx.AsyncClient,
    category: dict,
    kw_index: int,
    global_seed: int,
) -> dict | None:
    keyword = category["keywords"][kw_index]
    cat_id  = category["id"]
    idx     = kw_index + 1
    slug    = _slugify(keyword)
    filename = f"{cat_id}_{idx:02d}_{slug}.jpg"
    cat_dir  = SAMPLES_DIR / cat_id
    out_path = cat_dir / filename

    if out_path.exists():
        log.info("이미 존재, 건너뜀: %s", filename)
        with Image.open(out_path) as img:
            w, h = img.size
        size_kb = out_path.stat().st_size // 1024
        return _build_entry(category, idx, filename, cat_id, w, h, size_kb, {
            "source": "cached", "source_url": "", "author": "", "author_url": "", "license": "", "tags": [],
        }, keyword)

    log.info("[%s] %s 다운로드 중…", cat_id, keyword)

    meta: dict | None = None

    # 1) Unsplash API
    meta = await fetch_via_unsplash_api(client, keyword)

    # 2) Pexels API
    if meta is None:
        meta = await fetch_via_pexels_api(client, keyword)

    # 3) source.unsplash.com (무키)
    if meta is None:
        log.info("  → 폴백: source.unsplash.com (%s)", keyword)
        meta = await fetch_via_source_unsplash(client, keyword)

    # 4) picsum 최종 폴백
    if meta is None:
        log.info("  → 최종 폴백: picsum (seed=%d)", global_seed)
        meta = await fetch_via_picsum(client, global_seed)

    if meta is None:
        log.error("모든 소스 실패: %s", filename)
        return None

    # 이미지 바이트 확보
    image_bytes = meta.pop("_image_bytes", None)
    if image_bytes is None:
        resp = await _fetch_with_retry(client, meta["image_url"])
        if resp is None:
            log.error("이미지 바이트 다운로드 실패: %s", filename)
            return None
        image_bytes = resp.content

    try:
        w, h, size_kb = resize_and_save(image_bytes, out_path)
    except Exception as exc:
        log.error("저장 실패 %s: %s", filename, exc)
        return None

    log.info("  ✓ %s (%dx%d, %dKB, 소스: %s)", filename, w, h, size_kb, meta["source"])
    return _build_entry(category, idx, filename, cat_id, w, h, size_kb, meta, keyword)


def _build_entry(
    category: dict,
    idx: int,
    filename: str,
    cat_id: str,
    w: int,
    h: int,
    size_kb: int,
    meta: dict,
    keyword: str,
) -> dict:
    return {
        "id": f"{cat_id}_{idx:02d}",
        "category": cat_id.split("_", 1)[1] if "_" in cat_id else cat_id,
        "category_id": cat_id,
        "category_label_ko": category["label_ko"],
        "filename": filename,
        "path": f"samples/{cat_id}/{filename}",
        "keyword": keyword,
        "source": meta.get("source", ""),
        "source_url": meta.get("source_url", ""),
        "author": meta.get("author", ""),
        "author_url": meta.get("author_url", ""),
        "license": meta.get("license", ""),
        "width": w,
        "height": h,
        "file_size_kb": size_kb,
        "tags": meta.get("tags", []),
        "test_purposes": category.get("test_purposes", []),
    }


async def main() -> None:
    log.info("=" * 60)
    log.info("Imalytix 샘플 이미지 다운로드 시작")
    log.info("Unsplash API: %s", "✓ 설정됨" if UNSPLASH_KEY else "✗ 미설정 (폴백 사용)")
    log.info("Pexels API:   %s", "✓ 설정됨" if PEXELS_KEY else "✗ 미설정 (폴백 사용)")
    log.info("=" * 60)

    results: list[dict] = []
    failed: list[str] = []
    seed = 100

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for category in CATEGORIES:
            for kw_idx in range(3):
                entry = await download_one(client, category, kw_idx, seed)
                seed += 1
                if entry:
                    results.append(entry)
                else:
                    failed.append(f"{category['id']}_{kw_idx + 1:02d}")
                # 소스 서버 부담 완화
                await asyncio.sleep(0.3)

    # manifest.json 저장
    manifest = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "failed": failed,
        "samples": results,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("")
    log.info("=" * 60)
    log.info("완료: %d/%d 성공, %d 실패", len(results), 30, len(failed))
    if failed:
        log.warning("실패 항목: %s", ", ".join(failed))
    log.info("manifest.json 저장: %s", MANIFEST_PATH)
    log.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
