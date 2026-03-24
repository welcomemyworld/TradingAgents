import json
import re
from typing import Any, Dict, Iterable, List

from tradingagents.agents.utils.agent_utils import (
    ANALYST_ORDER,
    ANALYST_DISPLAY_NAMES,
    build_instrument_context,
    collect_analyst_reports,
    get_capability_catalog,
    normalize_selected_analysts,
)


def _default_remaining_order(
    selected_analysts: Iterable[str], completed_analysts: Iterable[str]
) -> List[str]:
    completed = set(completed_analysts)
    return [key for key in normalize_selected_analysts(selected_analysts) if key not in completed]


def _truncate(text: str, limit: int = 900) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _parse_json_response(raw_text: str) -> Dict[str, Any]:
    raw_text = raw_text.strip()
    if not raw_text:
        return {}

    candidates = [raw_text]
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def _sanitize_capability_order(
    requested_order: Iterable[str] | None,
    selected_analysts: Iterable[str],
    completed_analysts: Iterable[str],
) -> List[str]:
    selected = set(normalize_selected_analysts(selected_analysts))
    completed = set(completed_analysts)
    order = []

    for analyst_key in requested_order or []:
        if analyst_key in selected and analyst_key not in completed and analyst_key not in order:
            order.append(analyst_key)

    for analyst_key in ANALYST_ORDER:
        if analyst_key in selected and analyst_key not in completed and analyst_key not in order:
            order.append(analyst_key)

    return order


def _format_completed_reports(completed_reports: Dict[str, str]) -> str:
    if not completed_reports:
        return "No completed reports yet."

    sections = []
    for analyst_key in ANALYST_ORDER:
        report = completed_reports.get(analyst_key)
        if report:
            sections.append(
                f"{ANALYST_DISPLAY_NAMES[analyst_key]}:\n{_truncate(report)}"
            )
    return "\n\n".join(sections)


def _build_plan_text(
    plan_data: Dict[str, Any],
    remaining_order: List[str],
    selected_analysts: List[str],
    completed_analysts: List[str],
) -> str:
    objective = plan_data.get("objective", "Generate the highest-conviction investment view.")
    thesis_focus = plan_data.get(
        "thesis_focus",
        "Blend deep business understanding with fast-moving catalysts and tape awareness.",
    )
    risk_focus = plan_data.get(
        "risk_focus",
        "Stress-test downside, crowding, and what would invalidate the thesis.",
    )
    catalyst_focus = plan_data.get(
        "catalyst_focus",
        "Identify the fastest path from insight to monetizable market repricing.",
    )
    key_questions = plan_data.get("key_questions") or []
    if not isinstance(key_questions, list):
        key_questions = [str(key_questions)]

    ordered_names = ", ".join(ANALYST_DISPLAY_NAMES[key] for key in remaining_order) or "Research complete"
    selected_names = ", ".join(ANALYST_DISPLAY_NAMES[key] for key in selected_analysts)
    completed_names = ", ".join(ANALYST_DISPLAY_NAMES[key] for key in completed_analysts) or "None yet"

    lines = [
        "## Investment Orchestration Plan",
        f"Objective: {objective}",
        f"Selected capabilities: {selected_names}",
        f"Completed capabilities: {completed_names}",
        f"Current priority order: {ordered_names}",
        f"Thesis focus: {thesis_focus}",
        f"Risk focus: {risk_focus}",
        f"Catalyst focus: {catalyst_focus}",
    ]

    if key_questions:
        lines.append("Key questions:")
        lines.extend(f"- {question}" for question in key_questions[:5])

    return "\n".join(lines)


def _build_analysis_brief(
    company_name: str, trade_date: str, plan_data: Dict[str, Any]
) -> str:
    objective = plan_data.get("objective", "Find the best risk-adjusted action.")
    thesis_focus = plan_data.get(
        "thesis_focus",
        "Integrate long-horizon company quality with near-term catalysts and market timing.",
    )
    risk_focus = plan_data.get(
        "risk_focus",
        "Prioritize what can go wrong, what the market already knows, and what invalidates the thesis.",
    )
    catalyst_focus = plan_data.get(
        "catalyst_focus",
        "Surface why this idea matters now rather than in the abstract.",
    )
    key_questions = plan_data.get("key_questions") or []
    if not isinstance(key_questions, list):
        key_questions = [str(key_questions)]

    question_block = "\n".join(f"- {question}" for question in key_questions[:5]) or "- What is the highest-conviction edge?"

    return (
        f"Company: {company_name}\n"
        f"Trade date: {trade_date}\n"
        f"Objective: {objective}\n"
        f"Thesis focus: {thesis_focus}\n"
        f"Risk focus: {risk_focus}\n"
        f"Catalyst focus: {catalyst_focus}\n"
        f"Key questions:\n{question_block}"
    )


def create_investment_orchestrator(llm, config):
    def investment_orchestrator_node(state) -> dict:
        selected_analysts = normalize_selected_analysts(state.get("selected_analysts"))
        completed_analysts = normalize_selected_analysts(state.get("completed_analysts"))
        completed_reports = collect_analyst_reports(state, selected_analysts)

        if not selected_analysts:
            return {
                "analysis_queue": [],
                "completed_analysts": [],
                "current_analyst": "",
                "analysis_plan": "## Investment Orchestration Plan\nNo research capabilities selected.",
                "analysis_brief": "",
            }

        if not config.get("enable_investment_orchestrator", True):
            remaining_order = _default_remaining_order(selected_analysts, completed_analysts)
            plan_data = {}
        else:
            remaining_choices = _default_remaining_order(selected_analysts, completed_analysts)
            if not remaining_choices:
                remaining_order = []
                plan_data = {}
            elif config.get("analysis_routing_mode") == "sequential":
                remaining_order = remaining_choices
                plan_data = {}
            else:
                prompt = f"""You are the chief investment orchestrator for an AI-native long/short investment institution.

Your mandate is to combine:
- MM-style speed, catalyst awareness, and fast alpha capture
- Fundamental L/S depth, industry understanding, and business-quality judgment

Decide which research capability modules should run next. Return valid JSON only with these keys:
- objective: string
- thesis_focus: string
- risk_focus: string
- catalyst_focus: string
- key_questions: array of strings
- ordered_capabilities: array of capability ids

Rules:
- Only use capability ids from the available list.
- Include each capability at most once.
- Prioritize the sequence that best sharpens edge, timing, and risk-adjusted conviction.
- When some reports are already completed, re-rank only the remaining capabilities.

{build_instrument_context(state["company_of_interest"])}
Trade date: {state["trade_date"]}

Available capabilities:
{get_capability_catalog(remaining_choices)}

Completed capability reports:
{_format_completed_reports(completed_reports)}
"""
                response = llm.invoke(prompt)
                plan_data = _parse_json_response(response.content)
                remaining_order = _sanitize_capability_order(
                    plan_data.get("ordered_capabilities"),
                    selected_analysts,
                    completed_analysts,
                )

        plan_text = _build_plan_text(
            plan_data,
            remaining_order,
            selected_analysts,
            completed_analysts,
        )
        journal_entry = (
            f"Completed: {', '.join(completed_analysts) or 'none'} | "
            f"Remaining: {', '.join(remaining_order) or 'none'}"
        )
        orchestration_journal = list(state.get("orchestration_journal", []))
        if not orchestration_journal or orchestration_journal[-1] != journal_entry:
            orchestration_journal.append(journal_entry)

        return {
            "analysis_queue": remaining_order,
            "completed_analysts": completed_analysts,
            "current_analyst": remaining_order[0] if remaining_order else "",
            "analysis_plan": plan_text,
            "analysis_brief": _build_analysis_brief(
                state["company_of_interest"],
                state["trade_date"],
                plan_data,
            ),
            "orchestration_journal": orchestration_journal,
        }

    return investment_orchestrator_node
