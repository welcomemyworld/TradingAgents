from __future__ import annotations

from statistics import mean
from typing import Any, Dict, Iterable, List

from futureinvest_web.serializer import build_web_sections
from tradingagents.agents.utils.agent_utils import (
    ANALYST_ORDER,
    get_analyst_report,
    normalize_selected_analysts,
)
from tradingagents.agents.utils.decision_protocol import CHALLENGE_STAGE_KEY


CANONICAL_SECTION_KEYS = [
    "analysis_plan",
    "portfolio_context",
    "temporal_context",
    "institution_memory_brief",
    "research_capability_reports",
    "thesis_review",
    "execution_state",
    "allocation_review",
    "final_decision",
    "decision_dossier_markdown",
]

MANUAL_SCORECARD_HEADERS = [
    "case_id",
    "ticker",
    "analysis_date",
    "status",
    "processed_signal",
    "overall_score",
    "runtime_seconds",
    "thesis_clarity_1_to_5",
    "counterevidence_quality_1_to_5",
    "portfolio_role_clarity_1_to_5",
    "timing_clarity_1_to_5",
    "sizing_discipline_1_to_5",
    "overall_research_quality_1_to_5",
    "reviewer_notes",
]


def _clean_text(value: Any) -> str:
    return str(value).strip() if value else ""


def _mean_bool(values: Iterable[bool]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return round(mean(1.0 if value else 0.0 for value in values), 4)


def get_section_presence(final_state: Dict[str, Any]) -> Dict[str, bool]:
    sections = {
        section["key"]: _clean_text(section.get("content"))
        for section in build_web_sections(final_state)
    }
    return {
        key: bool(sections.get(key))
        for key in CANONICAL_SECTION_KEYS
    }


def get_research_coverage(final_state: Dict[str, Any]) -> Dict[str, Any]:
    selected = normalize_selected_analysts(
        final_state.get("selected_analysts") or ANALYST_ORDER
    )
    reported = []
    missing = []
    for analyst_key in selected:
        if _clean_text(get_analyst_report(final_state, analyst_key)):
            reported.append(analyst_key)
        else:
            missing.append(analyst_key)

    total = len(selected)
    coverage_ratio = round(len(reported) / total, 4) if total else 0.0
    return {
        "selected": selected,
        "reported": reported,
        "missing": missing,
        "coverage_ratio": coverage_ratio,
    }


def get_decision_quality_flags(
    final_state: Dict[str, Any],
    processed_signal: str = "",
) -> Dict[str, bool]:
    thesis_review = final_state.get("thesis_review") or {}
    thesis_outputs = thesis_review.get("outputs") or {}
    execution_state = final_state.get("execution_state") or {}
    final_decision = final_state.get("final_decision") or {}
    portfolio_context = final_state.get("portfolio_context") or {}
    temporal_context = final_state.get("temporal_context") or {}

    return {
        "has_rating": bool(
            _clean_text(final_decision.get("rating")) or _clean_text(processed_signal)
        ),
        "has_kill_criteria": bool(_clean_text(final_decision.get("kill_criteria"))),
        "has_portfolio_role": bool(
            _clean_text(portfolio_context.get("portfolio_role"))
            or _clean_text(final_decision.get("portfolio_mandate"))
        ),
        "has_long_cycle_view": bool(
            _clean_text(temporal_context.get("long_cycle_mispricing"))
        ),
        "has_medium_cycle_view": bool(
            _clean_text(temporal_context.get("medium_cycle_rerating_path"))
        ),
        "has_short_cycle_window": bool(
            _clean_text(temporal_context.get("short_cycle_execution_window"))
        ),
        "has_counterevidence": bool(
            _clean_text(thesis_outputs.get(CHALLENGE_STAGE_KEY))
        ),
        "has_execution_blueprint": bool(
            _clean_text(execution_state.get("execution_plan"))
            or _clean_text(execution_state.get("full_blueprint"))
        ),
    }


def score_final_state(
    final_state: Dict[str, Any],
    processed_signal: str = "",
) -> Dict[str, Any]:
    section_presence = get_section_presence(final_state)
    research_coverage = get_research_coverage(final_state)
    decision_quality_flags = get_decision_quality_flags(final_state, processed_signal)

    canonical_completeness_score = _mean_bool(section_presence.values())
    research_coverage_score = research_coverage["coverage_ratio"]
    decision_quality_score = _mean_bool(decision_quality_flags.values())

    overall_score = round(
        (0.4 * canonical_completeness_score)
        + (0.2 * research_coverage_score)
        + (0.4 * decision_quality_score),
        4,
    )

    return {
        "section_presence": section_presence,
        "research_coverage": research_coverage,
        "decision_quality_flags": decision_quality_flags,
        "canonical_completeness_score": canonical_completeness_score,
        "research_coverage_score": research_coverage_score,
        "decision_quality_score": decision_quality_score,
        "overall_score": overall_score,
    }


def render_sections_markdown(sections: List[Dict[str, str]]) -> str:
    chunks = []
    for index, section in enumerate(sections, start=1):
        title = _clean_text(section.get("title")) or f"Section {index}"
        content = _clean_text(section.get("content")) or "_Empty_"
        chunks.append(f"## {index}. {title}\n\n{content}")
    return "\n\n".join(chunks).strip() + "\n"


def build_case_summary(
    case: Dict[str, Any],
    final_state: Dict[str, Any],
    processed_signal: str,
    runtime_seconds: float,
) -> Dict[str, Any]:
    scores = score_final_state(final_state, processed_signal)
    missing_sections = [
        key for key, present in scores["section_presence"].items() if not present
    ]
    return {
        "case_id": case["case_id"],
        "ticker": case["ticker"],
        "analysis_date": case["analysis_date"],
        "status": "success",
        "processed_signal": _clean_text(processed_signal),
        "runtime_seconds": round(runtime_seconds, 3),
        "selected_analysts": list(case.get("selected_analysts") or []),
        "token_budget": _clean_text(
            (final_state.get("orchestration_state") or {}).get("token_budget")
        ),
        "position_importance": _clean_text(
            (final_state.get("orchestration_state") or {}).get("position_importance")
        ),
        "portfolio_role": _clean_text(
            (final_state.get("portfolio_context") or {}).get("portfolio_role")
        ),
        "kill_criteria": _clean_text(
            (final_state.get("final_decision") or {}).get("kill_criteria")
        ),
        "missing_sections": missing_sections,
        **scores,
    }


def build_error_summary(
    case: Dict[str, Any],
    runtime_seconds: float,
    error: Exception,
) -> Dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "ticker": case["ticker"],
        "analysis_date": case["analysis_date"],
        "status": "error",
        "processed_signal": "",
        "runtime_seconds": round(runtime_seconds, 3),
        "selected_analysts": list(case.get("selected_analysts") or []),
        "token_budget": "",
        "position_importance": "",
        "portfolio_role": "",
        "kill_criteria": "",
        "missing_sections": CANONICAL_SECTION_KEYS,
        "section_presence": {key: False for key in CANONICAL_SECTION_KEYS},
        "research_coverage": {
            "selected": list(case.get("selected_analysts") or []),
            "reported": [],
            "missing": list(case.get("selected_analysts") or []),
            "coverage_ratio": 0.0,
        },
        "decision_quality_flags": {},
        "canonical_completeness_score": 0.0,
        "research_coverage_score": 0.0,
        "decision_quality_score": 0.0,
        "overall_score": 0.0,
        "error_type": type(error).__name__,
        "error_message": _clean_text(error),
    }


def build_manual_scorecard_rows(
    case_summaries: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows = []
    for summary in case_summaries:
        rows.append(
            {
                "case_id": summary.get("case_id", ""),
                "ticker": summary.get("ticker", ""),
                "analysis_date": summary.get("analysis_date", ""),
                "status": summary.get("status", ""),
                "processed_signal": summary.get("processed_signal", ""),
                "overall_score": summary.get("overall_score", 0.0),
                "runtime_seconds": summary.get("runtime_seconds", 0.0),
                "thesis_clarity_1_to_5": "",
                "counterevidence_quality_1_to_5": "",
                "portfolio_role_clarity_1_to_5": "",
                "timing_clarity_1_to_5": "",
                "sizing_discipline_1_to_5": "",
                "overall_research_quality_1_to_5": "",
                "reviewer_notes": "",
            }
        )
    return rows
