#!/usr/bin/env python3
"""
sample_picker.py
샘플 이미지를 카테고리/태그/ID로 조회하고 랜덤 추출하는 유틸리티.

Programmatic API:
    from scripts.sample_picker import SamplePicker
    picker = SamplePicker()
    picker.list_samples(category="portraits")
    picker.pick_random(n=3)
    picker.get_sample("01_portraits_01")

CLI:
    python scripts/sample_picker.py --list
    python scripts/sample_picker.py --category portraits
    python scripts/sample_picker.py --random 5
    python scripts/sample_picker.py --id 04_food_02
    python scripts/sample_picker.py --id 04_food_02 --copy-path
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "samples" / "manifest.json"


class SamplePicker:
    def __init__(self, manifest_path: Path | str | None = None) -> None:
        path = Path(manifest_path) if manifest_path else MANIFEST_PATH
        if not path.exists():
            raise FileNotFoundError(
                f"manifest.json 을 찾을 수 없습니다: {path}\n"
                "먼저 python scripts/download_samples.py 를 실행하세요."
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        self._samples: list[dict[str, Any]] = data.get("samples", [])
        self._root = path.parent.parent

    # ──────────────────────────────────────────────────────────────────────
    # 내부 헬퍼
    # ──────────────────────────────────────────────────────────────────────

    def _enrich(self, entry: dict) -> dict:
        """절대 경로 필드를 추가해 반환"""
        result = dict(entry)
        result["abs_path"] = str(self._root / entry["path"])
        return result

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def all_categories(self) -> list[dict[str, str]]:
        """카테고리 목록 반환"""
        seen: dict[str, str] = {}
        for s in self._samples:
            cid = s["category_id"]
            if cid not in seen:
                seen[cid] = s["category_label_ko"]
        return [{"id": k, "label_ko": v} for k, v in seen.items()]

    def list_samples(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        category: 카테고리 ID 또는 이름 일부 (예: "portraits", "01_portraits")
        tags:     태그 목록 — 하나라도 포함하면 반환
        """
        results = self._samples

        if category:
            cat_lower = category.lower()
            results = [
                s for s in results
                if cat_lower in s["category_id"].lower()
                or cat_lower in s.get("category", "").lower()
                or cat_lower in s.get("category_label_ko", "").lower()
            ]

        if tags:
            tag_set = {t.lower() for t in tags}
            results = [
                s for s in results
                if any(tag_set & {t.lower() for t in s.get("tags", [])})
            ]

        return [self._enrich(s) for s in results]

    def get_sample(self, sample_id: str) -> dict[str, Any] | None:
        """ID로 단건 조회. 없으면 None."""
        for s in self._samples:
            if s["id"] == sample_id:
                return self._enrich(s)
        return None

    def pick_random(
        self,
        n: int = 1,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """랜덤 n장 추출"""
        pool = self.list_samples(category=category)
        if not pool:
            return []
        return random.sample(pool, min(n, len(pool)))

    def summary(self) -> dict[str, Any]:
        """전체 요약"""
        cats = self.all_categories()
        total = len(self._samples)
        return {
            "total": total,
            "categories": len(cats),
            "category_list": cats,
        }


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def _print_table(samples: list[dict]) -> None:
    if not samples:
        print("(결과 없음)")
        return
    width_id   = max(len(s["id"]) for s in samples) + 2
    width_cat  = max(len(s.get("category_label_ko", "")) for s in samples) + 2
    width_kw   = max(len(s.get("keyword", "")) for s in samples) + 2

    header = f"{'ID':<{width_id}} {'카테고리':<{width_cat}} {'키워드':<{width_kw}} {'크기':>10}  경로"
    print(header)
    print("─" * (len(header) + 20))
    for s in samples:
        size = f"{s.get('width', 0)}×{s.get('height', 0)}"
        print(
            f"{s['id']:<{width_id}} "
            f"{s.get('category_label_ko', ''):<{width_cat}} "
            f"{s.get('keyword', ''):<{width_kw}} "
            f"{size:>10}  "
            f"{s['abs_path']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Imalytix 샘플 이미지 선택 유틸리티",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--list",     action="store_true", help="전체 목록 출력")
    parser.add_argument("--summary",  action="store_true", help="카테고리 요약 출력")
    parser.add_argument("--category", type=str, default=None, help="카테고리 필터 (예: portraits)")
    parser.add_argument("--tags",     type=str, default=None, help="태그 필터 (쉼표 구분)")
    parser.add_argument("--random",   type=int, default=None, metavar="N", help="랜덤 N장 추출")
    parser.add_argument("--id",       type=str, default=None, help="ID로 단건 조회")
    parser.add_argument("--copy-path", action="store_true", help="결과 경로를 클립보드에 복사")
    parser.add_argument("--json",     action="store_true", help="JSON 형식으로 출력")
    args = parser.parse_args()

    try:
        picker = SamplePicker()
    except FileNotFoundError as e:
        print(f"[오류] {e}", file=sys.stderr)
        sys.exit(1)

    results: list[dict] = []

    if args.summary:
        info = picker.summary()
        print(f"\n총 {info['total']}장 / {info['categories']}개 카테고리")
        print()
        for cat in info["category_list"]:
            count = len(picker.list_samples(category=cat["id"]))
            print(f"  {cat['id']:<25} {cat['label_ko']:<10} ({count}장)")
        return

    if args.id:
        sample = picker.get_sample(args.id)
        if sample is None:
            print(f"[오류] ID '{args.id}' 를 찾을 수 없습니다.", file=sys.stderr)
            sys.exit(1)
        results = [sample]
    elif args.random is not None:
        results = picker.pick_random(n=args.random, category=args.category)
    else:
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        results = picker.list_samples(category=args.category, tags=tags)

    if not results:
        print("(조건에 맞는 샘플이 없습니다.)")
        return

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        _print_table(results)

    if args.copy_path:
        paths = "\n".join(s["abs_path"] for s in results)
        try:
            import subprocess
            if sys.platform == "win32":
                subprocess.run(["clip"], input=paths.encode("utf-8"), check=True)
            elif sys.platform == "darwin":
                subprocess.run(["pbcopy"], input=paths.encode("utf-8"), check=True)
            else:
                subprocess.run(["xclip", "-selection", "clipboard"], input=paths.encode("utf-8"), check=True)
            print(f"\n✓ {len(results)}개 경로가 클립보드에 복사되었습니다.")
        except Exception as exc:
            print(f"\n[경고] 클립보드 복사 실패: {exc}")


if __name__ == "__main__":
    main()
