from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image

from app.services.embedding_service import build_embedding, cosine_similarity


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(slots=True)
class BenchmarkItem:
    path: str
    category: str
    label: str
    filename: str


@dataclass(slots=True)
class NeighborResult:
    path: str
    category: str
    label: str
    strategy: str
    top_match_path: str | None
    top_match_category: str | None
    top_match_label: str | None
    similarity: float
    same_label: bool
    same_category: bool


def _discover_images(dataset_root: Path) -> list[BenchmarkItem]:
    items: list[BenchmarkItem] = []
    for path in sorted(dataset_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        parts = path.relative_to(dataset_root).parts
        category = parts[0] if parts else "unknown"
        name = path.name.lower()
        label = "AI" if "_ai_" in name else "REAL" if "_real_" in name else "UNKNOWN"
        items.append(
            BenchmarkItem(
                path=str(path),
                category=category,
                label=label,
                filename=path.name,
            )
        )
    return items


def _load_image(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.copy()


def _evaluate_strategy(items: list[BenchmarkItem], strategy: str) -> list[NeighborResult]:
    embeddings: dict[str, list[float]] = {}
    for item in items:
        embeddings[item.path] = build_embedding(_load_image(Path(item.path)), strategy=strategy)

    results: list[NeighborResult] = []
    for item in items:
        best_path = None
        best_similarity = -1.0
        for candidate in items:
            if candidate.path == item.path:
                continue
            sim = cosine_similarity(embeddings[item.path], embeddings[candidate.path])
            if sim > best_similarity:
                best_similarity = sim
                best_path = candidate.path

        match = next((x for x in items if x.path == best_path), None)
        results.append(
            NeighborResult(
                path=item.path,
                category=item.category,
                label=item.label,
                strategy=strategy,
                top_match_path=best_path,
                top_match_category=match.category if match else None,
                top_match_label=match.label if match else None,
                similarity=round(max(0.0, best_similarity), 6),
                same_label=bool(match and match.label == item.label),
                same_category=bool(match and match.category == item.category),
            )
        )
    return results


def _summarize(results: list[NeighborResult]) -> dict[str, float]:
    if not results:
        return {"label_accuracy": 0.0, "category_accuracy": 0.0, "avg_similarity": 0.0}
    label_accuracy = sum(1 for r in results if r.same_label) / len(results)
    category_accuracy = sum(1 for r in results if r.same_category) / len(results)
    avg_similarity = sum(r.similarity for r in results) / len(results)
    return {
        "label_accuracy": round(label_accuracy, 4),
        "category_accuracy": round(category_accuracy, 4),
        "avg_similarity": round(avg_similarity, 4),
    }


def _format_report(dataset_root: Path, items: list[BenchmarkItem], results_by_strategy: dict[str, list[NeighborResult]]) -> str:
    lines: list[str] = []
    lines.append("# Phase A Benchmark Report")
    lines.append("")
    lines.append(f"- dataset_root: `{dataset_root}`")
    lines.append(f"- total_images: `{len(items)}`")
    lines.append("")

    for strategy, results in results_by_strategy.items():
        summary = _summarize(results)
        lines.append(f"## {strategy.upper()}")
        lines.append("")
        lines.append(f"- label_accuracy: `{summary['label_accuracy']}`")
        lines.append(f"- category_accuracy: `{summary['category_accuracy']}`")
        lines.append(f"- avg_similarity: `{summary['avg_similarity']}`")
        lines.append("")
        lines.append("| image | label | category | top_match_label | top_match_category | similarity |")
        lines.append("|---|---|---|---|---|---|")
        for row in results[:10]:
            lines.append(
                f"| {Path(row.path).name} | {row.label} | {row.category} | {row.top_match_label or ''} | {row.top_match_category or ''} | {row.similarity:.4f} |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase A benchmark over samples_test.")
    parser.add_argument("--dataset-root", default="samples_test", help="Dataset root directory")
    parser.add_argument("--output", default="reports/phase_a_benchmark_report.md", help="Report output path")
    parser.add_argument("--manifest-output", default="benchmarks/phase_a_manifest.json", help="Manifest output path")
    args = parser.parse_args()

    root = Path(args.dataset_root).resolve()
    items = _discover_images(root)
    if not items:
        raise SystemExit(f"No images found under {root}")

    results_by_strategy = {
        "dino": _evaluate_strategy(items, "dino"),
        "clip": _evaluate_strategy(items, "clip"),
    }

    report = _format_report(root, items, results_by_strategy)

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    manifest_path = Path(args.manifest_output).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(report)
    print(f"\nSaved report to: {output_path}")
    print(f"Saved manifest to: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
