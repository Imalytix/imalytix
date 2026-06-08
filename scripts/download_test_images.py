#!/usr/bin/env python3
"""
download_test_images.py
API 키 없이 HTTP 직접 요청으로 테스트 이미지 30장 다운로드.

실제 사진 → picsum.photos  (CC0, 즉시 응답)
AI 이미지  → pollinations.ai (무료 AI 생성, 5~15초 소요)

파일명 규칙: {카테고리}_{번호}_REAL_{설명}.jpg
             {카테고리}_{번호}_AI_{설명}.jpg
"""
from __future__ import annotations

import asyncio
import io
import logging
import re
import sys
import time
from pathlib import Path

import httpx
from PIL import Image

ROOT       = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "samples_test"
MAX_LONG   = 1200
TIMEOUT    = 60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 다운로드 목록  (카테고리, 번호, 라벨, 설명슬러그, URL)
# ──────────────────────────────────────────────────────────────────────────────

def ai_url(prompt: str, seed: int = 1) -> str:
    """pollinations.ai — API 키 불필요, HTTP GET 한 번으로 AI 이미지 생성"""
    import urllib.parse
    p = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{p}?width=1200&height=800&seed={seed}&model=flux&nologo=true&enhance=false"


def real_url(seed: int) -> str:
    """picsum.photos — 시드 기반 랜덤 실사 사진"""
    return f"https://picsum.photos/seed/{seed}/1200/800"


IMAGES: list[tuple[str, int, str, str, str]] = [
    # (카테고리폴더, 번호, REAL/AI, 파일설명슬러그, URL)

    # ── 01 인물 ──────────────────────────────────────────────
    ("01_portraits", 1, "REAL", "portrait-woman",    real_url(10)),
    ("01_portraits", 2, "AI",   "portrait-woman",    ai_url("photorealistic portrait of smiling woman, studio lighting, professional photography", 1)),
    ("01_portraits", 3, "REAL", "elderly-man",       real_url(11)),

    # ── 02 풍경 ──────────────────────────────────────────────
    ("02_landscape", 1, "REAL", "mountain-lake",     real_url(20)),
    ("02_landscape", 2, "AI",   "mountain-sunset",   ai_url("photorealistic mountain sunset landscape, golden hour, nature photography", 2)),
    ("02_landscape", 3, "REAL", "ocean-beach",       real_url(21)),

    # ── 03 동물 ──────────────────────────────────────────────
    ("03_animals",   1, "REAL", "cat-closeup",       real_url(30)),
    ("03_animals",   2, "AI",   "tiger-forest",      ai_url("photorealistic tiger in green forest, wildlife photography, sharp details", 3)),
    ("03_animals",   3, "REAL", "bird-branch",       real_url(31)),

    # ── 04 음식 ──────────────────────────────────────────────
    ("04_food",      1, "REAL", "food-plate",        real_url(40)),
    ("04_food",      2, "AI",   "bibimbap-bowl",     ai_url("photorealistic korean bibimbap rice bowl, food photography, top view, colorful ingredients", 4)),
    ("04_food",      3, "REAL", "dessert-cake",      real_url(41)),

    # ── 05 건축 ──────────────────────────────────────────────
    ("05_architecture", 1, "REAL", "modern-building", real_url(50)),
    ("05_architecture", 2, "AI",   "futuristic-city", ai_url("photorealistic futuristic city skyline at night, modern architecture, reflection in water", 5)),
    ("05_architecture", 3, "REAL", "old-church",       real_url(51)),

    # ── 06 추상 ──────────────────────────────────────────────
    ("06_abstract",  1, "REAL", "texture-pattern",   real_url(60)),
    ("06_abstract",  2, "AI",   "geometric-art",     ai_url("colorful geometric abstract digital art, fractal patterns, vibrant colors", 6)),
    ("06_abstract",  3, "REAL", "color-splash",      real_url(61)),

    # ── 07 제품 ──────────────────────────────────────────────
    ("07_products",  1, "REAL", "product-shot",      real_url(70)),
    ("07_products",  2, "AI",   "sneakers-white",    ai_url("photorealistic white sneakers on clean white background, product photography, studio lighting", 7)),
    ("07_products",  3, "REAL", "watch-close",       real_url(71)),

    # ── 08 텍스트/OCR ────────────────────────────────────────
    ("08_text_ocr",  1, "REAL", "street-sign",       real_url(80)),
    ("08_text_ocr",  2, "AI",   "neon-sign-city",    ai_url("photorealistic neon signs in rainy city street at night, bokeh lights, urban photography", 8)),
    ("08_text_ocr",  3, "REAL", "book-text",         real_url(81)),

    # ── 09 차트 ──────────────────────────────────────────────
    ("09_charts",    1, "REAL", "office-desk",       real_url(90)),
    ("09_charts",    2, "AI",   "data-dashboard",    ai_url("clean modern data dashboard with bar charts graphs statistics, business infographic, white background", 9)),
    ("09_charts",    3, "REAL", "notebook-plan",     real_url(91)),

    # ── 10 일러스트 ──────────────────────────────────────────
    ("10_illustration", 1, "REAL", "painting-canvas",  real_url(100)),
    ("10_illustration", 2, "AI",   "digital-art",       ai_url("beautiful digital illustration watercolor style landscape, soft colors, artistic painting", 10)),
    ("10_illustration", 3, "REAL", "art-gallery",       real_url(101)),
]

# ──────────────────────────────────────────────────────────────────────────────
# 다운로드 & 저장
# ──────────────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def resize_save(data: bytes, path: Path) -> tuple[int, int, int]:
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > MAX_LONG:
            scale = MAX_LONG / max(w, h)
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
        w, h = img.size
        img.save(path, format="JPEG", quality=88, optimize=True)
    return w, h, path.stat().st_size // 1024


async def download_one(
    client: httpx.AsyncClient,
    cat: str,
    idx: int,
    label: str,
    slug: str,
    url: str,
) -> bool:
    cat_dir = OUTPUT_DIR / cat
    cat_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{cat}_{idx:02d}_{label}_{slug}.jpg"
    out = cat_dir / filename

    if out.exists():
        log.info("  [건너뜀] %s", filename)
        return True

    tag = f"[{label}]"
    log.info("%s  %-25s  %s", tag, f"{cat}/{filename[:30]}", "요청 중…")
    t0 = time.perf_counter()

    for attempt in range(3):
        try:
            resp = await client.get(url, timeout=TIMEOUT, follow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 3000:
                break
            log.warning("  HTTP %d, 재시도 %d/3", resp.status_code, attempt + 1)
            await asyncio.sleep(2 ** attempt)
        except Exception as exc:
            log.warning("  오류 (시도 %d/3): %s", attempt + 1, exc)
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
    else:
        log.error("  ✗ 실패: %s", filename)
        return False

    try:
        w, h, kb = resize_save(resp.content, out)
        elapsed = time.perf_counter() - t0
        log.info("  ✓ %s  (%dx%d, %dKB, %.1fs)", filename, w, h, kb, elapsed)
        return True
    except Exception as exc:
        log.error("  ✗ 저장 실패 %s: %s", filename, exc)
        return False


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total   = len(IMAGES)
    ai_cnt  = sum(1 for _, _, lbl, _, _ in IMAGES if lbl == "AI")
    real_cnt= total - ai_cnt

    log.info("=" * 65)
    log.info("Imalytix 테스트 이미지 다운로드 (API 키 불필요)")
    log.info("  실제 사진: %d장  (picsum.photos · CC0)", real_cnt)
    log.info("  AI 사진:   %d장  (pollinations.ai · 무료 생성)", ai_cnt)
    log.info("  저장 위치: %s", OUTPUT_DIR)
    log.info("=" * 65)
    log.info("※ AI 이미지는 생성에 5~15초 소요됩니다.")
    log.info("")

    ok = fail = 0
    # REAL 먼저 (빠름), AI 순서대로
    real_tasks = [(c,i,l,s,u) for c,i,l,s,u in IMAGES if l == "REAL"]
    ai_tasks   = [(c,i,l,s,u) for c,i,l,s,u in IMAGES if l == "AI"]

    async with httpx.AsyncClient(follow_redirects=True) as client:
        log.info("── 실제 사진 다운로드 (%d장) ──────────────────────────────", len(real_tasks))
        for args in real_tasks:
            result = await download_one(client, *args)
            (ok if result else fail).__class__  # dummy
            if result: ok += 1
            else: fail += 1

        log.info("")
        log.info("── AI 이미지 생성 & 다운로드 (%d장) ──────────────────────────", len(ai_tasks))
        for args in ai_tasks:
            result = await download_one(client, *args)
            if result: ok += 1
            else: fail += 1
            await asyncio.sleep(1)  # pollinations.ai 요청 간격

    log.info("")
    log.info("=" * 65)
    log.info("완료: 성공 %d / 실패 %d / 전체 %d", ok, fail, total)
    log.info("")
    log.info("파일 위치: %s", OUTPUT_DIR)
    log.info("  ├─ *_REAL_*.jpg  →  실제 사진 (picsum.photos)")
    log.info("  └─ *_AI_*.jpg    →  AI 생성 이미지 (pollinations.ai)")
    log.info("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
