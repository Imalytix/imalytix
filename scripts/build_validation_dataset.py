from __future__ import annotations

import argparse
import csv
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(slots=True)
class DatasetRow:
    source_path: Path
    relative_path: str
    label: str
    category: str
    size_bytes: int


def _infer_label(path: Path) -> str:
    name = path.name.lower()
    tokens = [token for token in re.split(r"[_\-\.\s]+", name) if token]
    if "ai" in tokens or "generated" in tokens:
        return "AI"
    if "real" in tokens or "photo" in tokens:
        return "REAL"
    return "UNKNOWN"


def _infer_category(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
        return rel.parts[0] if rel.parts else "uncategorized"
    except Exception:
        return path.parent.name


def collect_candidates(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            candidates.append(path)
    return candidates


def build_manifest(
    *,
    source_roots: list[Path],
    output_dir: Path,
    max_size_gb: float,
    per_category_limit: int,
) -> list[DatasetRow]:
    max_bytes = int(max_size_gb * 1024**3)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[DatasetRow] = []
    used_bytes = 0
    category_counts: dict[str, int] = {}

    for root in source_roots:
        if not root.exists():
            continue
        for path in collect_candidates(root):
            category = _infer_category(path, root)
            label = _infer_label(path)
            if label == "UNKNOWN":
                continue
            if category_counts.get(category, 0) >= per_category_limit:
                continue
            size_bytes = path.stat().st_size
            if used_bytes + size_bytes > max_bytes:
                continue

            rel = f"{category}/{path.name}"
            target = output_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

            rows.append(
                DatasetRow(
                    source_path=path,
                    relative_path=rel,
                    label=label,
                    category=category,
                    size_bytes=size_bytes,
                )
            )
            used_bytes += size_bytes
            category_counts[category] = category_counts.get(category, 0) + 1

    manifest_path = output_dir / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["relative_path", "label", "category", "size_bytes", "source_path"])
        for row in rows:
            writer.writerow([row.relative_path, row.label, row.category, row.size_bytes, str(row.source_path)])

    summary_path = output_dir / "summary.txt"
    summary_path.write_text(
        "\n".join(
            [
                f"rows={len(rows)}",
                f"used_bytes={used_bytes}",
                f"used_gb={used_bytes / 1024**3:.3f}",
                f"max_gb={max_size_gb}",
            ]
        ),
        encoding="utf-8",
    )

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local validation dataset under a size cap.")
    parser.add_argument("--source", action="append", required=True, help="Source root directory. Can be repeated.")
    parser.add_argument("--output", default="dataset/validation", help="Output directory.")
    parser.add_argument("--max-size-gb", type=float, default=5.0, help="Maximum dataset size in GB.")
    parser.add_argument("--per-category-limit", type=int, default=30, help="Maximum images per category.")
    args = parser.parse_args()

    source_roots = [Path(item).resolve() for item in args.source]
    output_dir = Path(args.output).resolve()
    rows = build_manifest(
        source_roots=source_roots,
        output_dir=output_dir,
        max_size_gb=args.max_size_gb,
        per_category_limit=args.per_category_limit,
    )
    print(f"built_rows={len(rows)}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
