from __future__ import annotations

from typing import Any, Dict, List, Tuple

from tradingagents.agents.utils.agent_utils import (
    ANALYST_DISPLAY_NAMES,
    ANALYST_ORDER,
    ANALYST_REPORT_FIELDS,
    CAPITAL_ALLOCATION_COMMITTEE,
    CHALLENGE_ENGINE,
    DOWNSIDE_GUARDRAIL_ENGINE,
    EXECUTION_ENGINE,
    INVESTMENT_DIRECTOR,
    PORTFOLIO_FIT_ENGINE,
    THESIS_ENGINE,
    UPSIDE_CAPTURE_ENGINE,
)
from tradingagents.agents.utils.decision_protocol import (
    CHALLENGE_STAGE_KEY,
    DOWNSIDE_STAGE_KEY,
    PORTFOLIO_FIT_STAGE_KEY,
    THESIS_STAGE_KEY,
    UPSIDE_STAGE_KEY,
    get_review_output,
    render_portfolio_context,
    render_temporal_context,
)


def _clean_text(value: Any) -> str:
    return str(value).strip() if value else ""


def _join_agent_entries(entries: List[Tuple[str, str]]) -> str:
    return "\n\n".join(
        f"### {title}\n{content}" for title, content in entries if _clean_text(content)
    )


def get_portfolio_mandate_content(state: Dict[str, Any]) -> str:
    portfolio_context = state.get("portfolio_context") or {}
    content = _clean_text(portfolio_context.get("full_context"))
    if content:
        return content
    return _clean_text(render_portfolio_context(portfolio_context))


def get_time_horizon_split_content(state: Dict[str, Any]) -> str:
    temporal_context = state.get("temporal_context") or {}
    content = _clean_text(temporal_context.get("full_context"))
    if content:
        return content
    return _clean_text(render_temporal_context(temporal_context))


def get_institutional_memory_content(state: Dict[str, Any]) -> str:
    return _clean_text(state.get("institution_memory_brief"))


def get_thesis_review_entries(state: Dict[str, Any]) -> List[Tuple[str, str]]:
    review = state.get("thesis_review") or {}
    entries = [
        (THESIS_ENGINE, get_review_output(review, THESIS_STAGE_KEY)),
        (CHALLENGE_ENGINE, get_review_output(review, CHALLENGE_STAGE_KEY)),
        (INVESTMENT_DIRECTOR, _clean_text(review.get("final_memo", ""))),
    ]
    if any(_clean_text(content) for _, content in entries):
        return entries

    legacy = state.get("investment_debate_state") or {}
    return [
        (THESIS_ENGINE, _clean_text(legacy.get("bull_history", ""))),
        (CHALLENGE_ENGINE, _clean_text(legacy.get("bear_history", ""))),
        (INVESTMENT_DIRECTOR, _clean_text(legacy.get("judge_decision", ""))),
    ]


def get_execution_state_entries(state: Dict[str, Any]) -> List[Tuple[str, str]]:
    execution_state = state.get("execution_state") or {}
    content = _clean_text(execution_state.get("full_blueprint")) or _clean_text(
        state.get("trader_investment_plan")
    )
    return [(EXECUTION_ENGINE, content)]


def get_allocation_review_entries(state: Dict[str, Any]) -> List[Tuple[str, str]]:
    review = state.get("allocation_review") or {}
    entries = [
        (UPSIDE_CAPTURE_ENGINE, get_review_output(review, UPSIDE_STAGE_KEY)),
        (DOWNSIDE_GUARDRAIL_ENGINE, get_review_output(review, DOWNSIDE_STAGE_KEY)),
        (PORTFOLIO_FIT_ENGINE, get_review_output(review, PORTFOLIO_FIT_STAGE_KEY)),
    ]
    if any(_clean_text(content) for _, content in entries):
        return entries

    legacy = state.get("risk_debate_state") or {}
    return [
        (UPSIDE_CAPTURE_ENGINE, _clean_text(legacy.get("aggressive_history", ""))),
        (
            DOWNSIDE_GUARDRAIL_ENGINE,
            _clean_text(legacy.get("conservative_history", "")),
        ),
        (PORTFOLIO_FIT_ENGINE, _clean_text(legacy.get("neutral_history", ""))),
    ]


def get_final_decision_entries(state: Dict[str, Any]) -> List[Tuple[str, str]]:
    final_decision = state.get("final_decision") or {}
    content = _clean_text(final_decision.get("full_decision")) or _clean_text(
        state.get("final_trade_decision")
    )
    return [(CAPITAL_ALLOCATION_COMMITTEE, content)]


def build_web_sections(state: Dict[str, Any]) -> List[Dict[str, str]]:
    sections: List[Dict[str, str]] = []

    analysis_plan = _clean_text(state.get("analysis_plan"))
    if analysis_plan:
        sections.append({"key": "analysis_plan", "title": "Investment Orchestration", "content": analysis_plan})

    portfolio_mandate = get_portfolio_mandate_content(state)
    if portfolio_mandate:
        sections.append({"key": "portfolio_context", "title": "Portfolio Mandate", "content": portfolio_mandate})

    time_horizon_split = get_time_horizon_split_content(state)
    if time_horizon_split:
        sections.append({"key": "temporal_context", "title": "Time Horizon Split", "content": time_horizon_split})

    institutional_memory = get_institutional_memory_content(state)
    if institutional_memory:
        sections.append({"key": "institution_memory_brief", "title": "Institutional Memory", "content": institutional_memory})

    analyst_blocks = []
    for analyst_key in ANALYST_ORDER:
        report = _clean_text(state.get(ANALYST_REPORT_FIELDS[analyst_key]))
        if report:
            analyst_blocks.append(f"### {ANALYST_DISPLAY_NAMES[analyst_key]}\n{report}")
    if analyst_blocks:
        sections.append(
            {
                "key": "research_capability_reports",
                "title": "Research Capability Reports",
                "content": "\n\n".join(analyst_blocks),
            }
        )

    thesis_review = _join_agent_entries(get_thesis_review_entries(state))
    if thesis_review:
        sections.append({"key": "thesis_review", "title": "Thesis Review", "content": thesis_review})

    execution_state = _join_agent_entries(get_execution_state_entries(state))
    if execution_state:
        sections.append({"key": "execution_state", "title": "Execution State", "content": execution_state})

    allocation_review = _join_agent_entries(get_allocation_review_entries(state))
    if allocation_review:
        sections.append({"key": "allocation_review", "title": "Allocation Review", "content": allocation_review})

    final_decision = _join_agent_entries(get_final_decision_entries(state))
    if final_decision:
        sections.append({"key": "final_decision", "title": "Final Decision", "content": final_decision})

    dossier = _clean_text(state.get("decision_dossier_markdown"))
    if dossier:
        sections.append({"key": "decision_dossier_markdown", "title": "Future Invest Dossier", "content": dossier})

    return sections

