# Phase A Benchmark Dataset

`samples/` and `samples_test/` are used as the first local benchmark corpus.

## Goal

- Compare `dino` and `clip` baseline embeddings.
- Measure whether similar or transformed images are grouped together.
- Produce a reproducible markdown report under `reports/`.

## Run

```bash
python scripts/run_phase_a_benchmark.py
```

Outputs:

- `benchmarks/phase_a_manifest.json`
- `reports/phase_a_benchmark_report.md`

