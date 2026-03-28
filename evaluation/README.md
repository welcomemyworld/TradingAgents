# Future Invest Evaluation Harness

This folder contains a minimal batch-evaluation scaffold for comparing Future Invest runs across historical cases.

## What it measures

- Canonical section completeness
- Research capability coverage
- Decision-quality structure
- Runtime per case
- Manual review rubric template

## Quick start

```bash
cd <repo-root>
source .venv/bin/activate
future-invest-eval --cases evaluation/cases.sample.json --label baseline
```

## Output

Each run writes to `evaluation/results/<timestamp>_<label>/`:

- `run_manifest.json`
- `summary.json`
- `summary.csv`
- `manual_scorecard.csv`
- `cases/<case_id>/result.json`
- `cases/<case_id>/sections.md`
- `cases/<case_id>/sections.json`
- `cases/<case_id>/state_log.json`

## Notes

- The harness uses the same `FutureInvestGraph` runtime as the CLI and web app.
- If your model provider quota is exhausted, failing cases are still recorded with structured error summaries so you can track operational reliability separately from research quality.
