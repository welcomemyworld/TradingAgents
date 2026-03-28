from __future__ import annotations

import argparse
import csv
import json
import traceback
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List

from evaluation.scoring import (
    MANUAL_SCORECARD_HEADERS,
    build_case_summary,
    build_error_summary,
    build_manual_scorecard_rows,
    render_sections_markdown,
)
from futureinvest_web.serializer import build_web_sections
from tradingagents.agents.utils.agent_utils import (
    ANALYST_ORDER,
    normalize_selected_analysts,
)
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import FutureInvestGraph, build_state_log_entry


DEFAULT_CASES_PATH = Path(__file__).with_name("cases.sample.json")
DEFAULT_OUTPUT_ROOT = Path(__file__).with_name("results")
SUMMARY_FIELD_ORDER = [
    "case_id",
    "ticker",
    "analysis_date",
    "status",
    "processed_signal",
    "runtime_seconds",
    "overall_score",
    "canonical_completeness_score",
    "research_coverage_score",
    "decision_quality_score",
    "institutional_loop_mode",
    "token_budget",
    "position_importance",
    "portfolio_role",
    "kill_criteria",
    "missing_sections",
    "error_type",
    "error_message",
]


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _clean_label(value: str) -> str:
    return "".join(
        char if char.isalnum() or char in {"-", "_"} else "-"
        for char in value.strip().lower()
    ).strip("-") or "run"


def _coerce_override(raw_value: str) -> Any:
    lowered = raw_value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "none":
        return None
    try:
        return int(raw_value)
    except ValueError:
        pass
    try:
        return float(raw_value)
    except ValueError:
        pass
    if raw_value.startswith("{") or raw_value.startswith("["):
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return raw_value
    return raw_value


def _parse_override(item: str) -> tuple[str, Any]:
    if "=" not in item:
        raise ValueError(
            f"Config override must look like key=value, received: {item}"
        )
    key, raw_value = item.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"Config override key cannot be empty: {item}")
    return key, _coerce_override(raw_value.strip())


def load_cases(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise ValueError("Evaluation case file must contain a JSON list.")

    cases = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Case #{index} must be a JSON object.")

        ticker = str(item.get("ticker", "")).strip()
        analysis_date = str(item.get("analysis_date", "")).strip()
        if not ticker or not analysis_date:
            raise ValueError(
                f"Case #{index} must include non-empty ticker and analysis_date."
            )

        case_id = str(item.get("case_id", "")).strip() or (
            f"{ticker.lower()}_{analysis_date.replace('-', '')}"
        )
        selected = normalize_selected_analysts(
            item.get("selected_analysts") or ANALYST_ORDER
        )
        cases.append(
            {
                "case_id": case_id,
                "ticker": ticker,
                "analysis_date": analysis_date,
                "selected_analysts": selected or ANALYST_ORDER,
                "notes": str(item.get("notes", "")).strip(),
                "config_overrides": dict(item.get("config_overrides") or {}),
            }
        )
    return cases


def _merge_config(base: Dict[str, Any], *overrides: Dict[str, Any]) -> Dict[str, Any]:
    config = deepcopy(base)
    for override in overrides:
        for key, value in (override or {}).items():
            config[key] = value
    return config


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, default=_json_default))


def _write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            flat_row = {}
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, list):
                    flat_row[field] = "|".join(str(item) for item in value)
                elif isinstance(value, dict):
                    flat_row[field] = json.dumps(value, ensure_ascii=True, sort_keys=True)
                else:
                    flat_row[field] = value
            writer.writerow(flat_row)


def _build_manifest(
    args: argparse.Namespace,
    cases_path: Path,
    run_dir: Path,
    config_overrides: Dict[str, Any],
    case_count: int,
) -> Dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "cases_file": str(cases_path),
        "run_dir": str(run_dir),
        "case_count": case_count,
        "global_config_overrides": config_overrides,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a batch evaluation over Future Invest cases."
    )
    parser.add_argument(
        "--cases",
        default=str(DEFAULT_CASES_PATH),
        help="Path to a JSON file containing evaluation cases.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory where evaluation outputs should be written.",
    )
    parser.add_argument(
        "--label",
        default="baseline",
        help="Short label to identify this evaluation run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optionally limit the number of cases to run.",
    )
    parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        help="Override config values with key=value. Repeatable.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop at the first case failure instead of continuing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases_path = Path(args.cases).resolve()
    output_root = Path(args.output_dir).resolve()
    run_dir = output_root / f"{_timestamp_slug()}_{_clean_label(args.label)}"
    cases_dir = run_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    global_overrides = dict(_parse_override(item) for item in args.overrides)
    cases = load_cases(cases_path)
    if args.limit > 0:
        cases = cases[: args.limit]

    manifest = _build_manifest(args, cases_path, run_dir, global_overrides, len(cases))
    _write_json(run_dir / "run_manifest.json", manifest)

    summaries: List[Dict[str, Any]] = []

    for index, case in enumerate(cases, start=1):
        print(
            f"[{index}/{len(cases)}] Evaluating {case['case_id']} "
            f"({case['ticker']} @ {case['analysis_date']})"
        )
        started = perf_counter()
        case_dir = cases_dir / case["case_id"]
        case_dir.mkdir(parents=True, exist_ok=True)
        _write_json(case_dir / "case.json", case)

        case_config = _merge_config(
            DEFAULT_CONFIG, global_overrides, case.get("config_overrides") or {}
        )

        try:
            graph = FutureInvestGraph(
                selected_analysts=case["selected_analysts"],
                config=case_config,
                debug=False,
            )
            final_state, processed_signal = graph.propagate(
                case["ticker"], case["analysis_date"]
            )
            runtime_seconds = perf_counter() - started

            sections = build_web_sections(final_state)
            state_log = build_state_log_entry(final_state)
            summary = build_case_summary(
                case, final_state, processed_signal, runtime_seconds
            )

            _write_json(case_dir / "state_log.json", state_log)
            _write_json(case_dir / "sections.json", sections)
            (case_dir / "sections.md").write_text(
                render_sections_markdown(sections), encoding="utf-8"
            )
            (case_dir / "processed_signal.txt").write_text(
                f"{processed_signal}\n", encoding="utf-8"
            )
            _write_json(case_dir / "result.json", summary)
            print(
                f"    success | score={summary['overall_score']:.4f} "
                f"| signal={summary['processed_signal'] or 'N/A'}"
            )
        except Exception as error:  # pragma: no cover - covered via summary structure tests
            runtime_seconds = perf_counter() - started
            summary = build_error_summary(case, runtime_seconds, error)
            _write_json(case_dir / "result.json", summary)
            (case_dir / "error.txt").write_text(
                traceback.format_exc(), encoding="utf-8"
            )
            print(
                f"    error | {summary['error_type']}: {summary['error_message']}"
            )
            if args.fail_fast:
                summaries.append(summary)
                break

        summaries.append(summary)

    summary_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "successful_cases": sum(1 for item in summaries if item["status"] == "success"),
        "failed_cases": sum(1 for item in summaries if item["status"] != "success"),
        "average_overall_score": round(
            sum(item.get("overall_score", 0.0) for item in summaries) / len(summaries),
            4,
        )
        if summaries
        else 0.0,
        "cases": summaries,
    }

    _write_json(run_dir / "summary.json", summary_payload)
    _write_csv(run_dir / "summary.csv", summaries, SUMMARY_FIELD_ORDER)
    _write_csv(
        run_dir / "manual_scorecard.csv",
        build_manual_scorecard_rows(summaries),
        MANUAL_SCORECARD_HEADERS,
    )

    print(f"Wrote evaluation outputs to {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
