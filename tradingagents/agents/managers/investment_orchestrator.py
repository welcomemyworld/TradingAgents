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
from tradingagents.agents.utils.decision_protocol import (
    PORTFOLIO_CONTEXT_SECTION_MAP,
    RESEARCH_DOSSIER_BRIEF_KEYS,
    build_dossier_update,
    build_portfolio_context_state_update,
    render_dossier_brief,
    render_temporal_context_brief,
)


SIGNAL_LEVELS = {"low", "medium", "high"}
TOKEN_BUDGET_LEVELS = {"tight", "balanced", "expansive"}
POSITION_IMPORTANCE_LEVELS = {"standard", "high", "critical"}


def _default_remaining_order(
    selected_analysts: Iterable[str], completed_analysts: Iterable[str]
) -> List[str]:
    completed = set(completed_analysts)
    return [
        key for key in normalize_selected_analysts(selected_analysts) if key not in completed
    ]


def _truncate(text: str, limit: int = 900) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _clean_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


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


def _sanitize_capability_additions(
    requested_additions: Iterable[str] | None,
    reserve_capabilities: Iterable[str],
) -> List[str]:
    reserve = set(reserve_capabilities)
    additions = []
    for analyst_key in requested_additions or []:
        if analyst_key in reserve and analyst_key not in additions:
            additions.append(analyst_key)
    return additions


def _ensure_additions_are_scheduled(
    ordered_capabilities: List[str], additions: List[str]
) -> List[str]:
    updated = [key for key in ordered_capabilities if key not in additions]
    return list(additions) + updated


def _normalize_choice(value: Any, allowed: set[str], default: str) -> str:
    normalized = _clean_text(value).lower()
    return normalized if normalized in allowed else default


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = _clean_text(value).lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    return default


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


def _default_continue_research(
    completed_count: int,
    remaining_count: int,
    uncertainty_level: str,
    evidence_conflict_level: str,
    token_budget: str,
    position_importance: str,
) -> bool:
    if remaining_count == 0:
        return False
    if completed_count == 0:
        return True
    if position_importance == "critical" and completed_count < 3:
        return True
    if uncertainty_level == "high" or evidence_conflict_level == "high":
        return True
    if token_budget == "tight" and completed_count >= 2:
        return False
    if completed_count >= 3 and uncertainty_level != "high":
        return False
    return completed_count < 2


def _default_counterevidence_search(
    evidence_conflict_level: str,
    uncertainty_level: str,
    completed_count: int,
) -> bool:
    if evidence_conflict_level == "high":
        return True
    if uncertainty_level == "high" and completed_count >= 1:
        return True
    return False


def _default_position_archetype(active_capabilities: List[str]) -> str:
    capability_set = set(active_capabilities)
    if "timing_catalyst" in capability_set:
        return "Event-driven alpha seat with meaningful timing sensitivity."
    if "business_truth" in capability_set and "market_expectations" in capability_set:
        return "Fundamental alpha seat built around variant perception."
    if "business_truth" in capability_set:
        return "Duration-leaning fundamental seat."
    return "General alpha seat pending deeper portfolio classification."


def _default_portfolio_role(position_importance: str, active_capabilities: List[str]) -> str:
    if position_importance == "critical":
        return "Potential core book driver if differentiated edge survives portfolio-fit review."
    if "timing_catalyst" in active_capabilities:
        return "Tactical sleeve expressed around catalysts and attention shifts."
    return "Satellite alpha seat that can earn more capital as the dossier strengthens."


def _default_book_correlation_view(active_capabilities: List[str]) -> str:
    if "market_expectations" in active_capabilities:
        return "Assume overlap with growth, momentum, and crowded consensus factors until the portfolio-fit engine proves otherwise."
    return "Current book correlation is unknown; treat factor overlap as an open question before sizing."


def _default_crowding_risk(
    evidence_conflict_level: str,
    active_capabilities: List[str],
) -> str:
    if evidence_conflict_level == "low":
        return "Potential crowding risk is elevated because the current evidence stack looks unusually one-sided."
    if "timing_catalyst" in active_capabilities:
        return "Catalyst-driven setups can crowd quickly; watch narrative and positioning overlap closely."
    return "Crowding risk remains uncertain and should be tested in challenge and portfolio-fit review."


def _default_capital_budget(position_importance: str, token_budget: str) -> str:
    if position_importance == "critical":
        return "Eligible for a large institutional budget only after overlap, guardrails, and scenario discipline are validated."
    if position_importance == "high":
        return "Reserve meaningful but not max capital; scale as execution and fit improve."
    if token_budget == "tight":
        return "Seed with a pilot allocation until the research stack proves the edge."
    return "Start with a measured satellite allocation and earn more capital through confirmation."


def _default_risk_budget(position_importance: str, uncertainty_level: str) -> str:
    if uncertainty_level == "high":
        return "Keep risk budget tight until the institution resolves the key unknowns."
    if position_importance == "critical":
        return "This seat can earn real risk budget, but only with explicit kill criteria and overlap discipline."
    if position_importance == "high":
        return "Allocate moderate risk budget with room to add as timing and portfolio fit improve."
    return "Limit risk budget to exploratory exposure until conviction graduates."


def _default_stop_reason(
    continue_research: bool,
    remaining_order: List[str],
    uncertainty_level: str,
    evidence_conflict_level: str,
    token_budget: str,
) -> str:
    if continue_research and remaining_order:
        return (
            "Continue research to reduce uncertainty/conflict before moving into thesis synthesis."
        )
    if not remaining_order:
        return "All activated capability modules have finished; proceed to thesis synthesis."
    if token_budget == "tight":
        return "Stop research and synthesize with the current evidence to preserve budget."
    if uncertainty_level == "low" and evidence_conflict_level == "low":
        return "Stop research because the evidence is sufficiently coherent for synthesis."
    return "Stop research and hand off to the thesis review stage."


def _build_plan_text(
    plan_data: Dict[str, Any],
    orchestration_state: Dict[str, Any],
    portfolio_context: Dict[str, str],
    temporal_context: Dict[str, str],
    remaining_order: List[str],
    active_capabilities: List[str],
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
    active_names = ", ".join(ANALYST_DISPLAY_NAMES[key] for key in active_capabilities) or "None"
    completed_names = ", ".join(ANALYST_DISPLAY_NAMES[key] for key in completed_analysts) or "None yet"
    reserve_names = (
        ", ".join(
            ANALYST_DISPLAY_NAMES[key]
            for key in orchestration_state.get("reserve_capabilities", [])
        )
        or "None"
    )
    added_names = (
        ", ".join(
            ANALYST_DISPLAY_NAMES[key]
            for key in orchestration_state.get("add_capabilities", [])
        )
        or "None"
    )

    lines = [
        "## Investment Orchestration Plan",
        f"Objective: {objective}",
        "Research mode: Parallel hard loop across the active research engines.",
        f"Active capabilities: {active_names}",
        f"Completed capabilities: {completed_names}",
        f"Reserve capabilities: {reserve_names}",
        f"Current priority order: {ordered_names}",
        f"Token budget: {orchestration_state['token_budget']}",
        f"Position importance: {orchestration_state['position_importance']}",
        f"Uncertainty: {orchestration_state['uncertainty_level']}",
        f"Evidence conflict: {orchestration_state['evidence_conflict_level']}",
        f"Portfolio role: {portfolio_context['portfolio_role']}",
        f"Position archetype: {portfolio_context['position_archetype']}",
        f"Correlation to current book: {portfolio_context['book_correlation_view']}",
        f"Crowding / factor overlap: {portfolio_context['crowding_risk']}",
        f"Capital budget: {portfolio_context['capital_budget']}",
        f"Risk budget: {portfolio_context['risk_budget']}",
        f"Long-cycle mispricing: {temporal_context.get('long_cycle_mispricing', '')}",
        f"Medium-cycle re-rating path: {temporal_context.get('medium_cycle_rerating_path', '')}",
        f"Short-cycle execution window: {temporal_context.get('short_cycle_execution_window', '')}",
        f"Added reserve capabilities: {added_names}",
        (
            "Counterevidence search: triggered"
            if orchestration_state["trigger_counterevidence_search"]
            else "Counterevidence search: standard"
        ),
        f"Stop rule: {orchestration_state['stop_reason']}",
        f"Thesis focus: {thesis_focus}",
        f"Risk focus: {risk_focus}",
        f"Catalyst focus: {catalyst_focus}",
    ]

    if orchestration_state.get("counterevidence_focus"):
        lines.append(
            f"Counterevidence focus: {orchestration_state['counterevidence_focus']}"
        )

    if key_questions:
        lines.append("Key questions:")
        lines.extend(f"- {question}" for question in key_questions[:5])

    return "\n".join(lines)


def _build_analysis_brief(
    company_name: str,
    trade_date: str,
    plan_data: Dict[str, Any],
    orchestration_state: Dict[str, Any],
    portfolio_context: Dict[str, str],
    temporal_context: Dict[str, str],
    institution_memory_brief: str,
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
    counterevidence_focus = orchestration_state.get("counterevidence_focus") or "Probe the weakest assumptions in the current thesis."

    return (
        f"Company: {company_name}\n"
        f"Trade date: {trade_date}\n"
        f"Objective: {objective}\n"
        f"Token budget: {orchestration_state['token_budget']}\n"
        f"Position importance: {orchestration_state['position_importance']}\n"
        f"Uncertainty: {orchestration_state['uncertainty_level']}\n"
        f"Evidence conflict: {orchestration_state['evidence_conflict_level']}\n"
        f"Portfolio role: {portfolio_context['portfolio_role']}\n"
        f"Position archetype: {portfolio_context['position_archetype']}\n"
        f"Correlation to current book: {portfolio_context['book_correlation_view']}\n"
        f"Crowding / factor overlap: {portfolio_context['crowding_risk']}\n"
        f"Capital budget: {portfolio_context['capital_budget']}\n"
        f"Risk budget: {portfolio_context['risk_budget']}\n"
        f"Long-cycle mispricing: {temporal_context.get('long_cycle_mispricing', '')}\n"
        f"Medium-cycle re-rating path: {temporal_context.get('medium_cycle_rerating_path', '')}\n"
        f"Short-cycle execution window: {temporal_context.get('short_cycle_execution_window', '')}\n"
        f"Continue research: {'yes' if orchestration_state['continue_research'] else 'no'}\n"
        f"Stop rule: {orchestration_state['stop_reason']}\n"
        f"Counterevidence search: {'intensify' if orchestration_state['trigger_counterevidence_search'] else 'standard'}\n"
        f"Counterevidence focus: {counterevidence_focus}\n"
        f"Thesis focus: {thesis_focus}\n"
        f"Risk focus: {risk_focus}\n"
        f"Catalyst focus: {catalyst_focus}\n"
        f"Key questions:\n{question_block}\n"
        f"\nInstitutional memory:\n{institution_memory_brief}"
    )


def create_investment_orchestrator(llm, config):
    def investment_orchestrator_node(state) -> dict:
        selected_analysts = normalize_selected_analysts(state.get("selected_analysts"))
        completed_analysts = normalize_selected_analysts(state.get("completed_analysts"))
        allow_expansion = config.get("enable_dynamic_capability_expansion", True)
        available_capabilities = ANALYST_ORDER if allow_expansion else selected_analysts
        completed_reports = collect_analyst_reports(state, available_capabilities)
        existing_orchestration_state = dict(state.get("orchestration_state") or {})
        institution_memory_brief = state.get("institution_memory_brief", "")
        temporal_context = dict(state.get("temporal_context") or {})

        if not selected_analysts:
            orchestration_state = {
                "token_budget": config.get("orchestrator_token_budget", "balanced"),
                "position_importance": config.get(
                    "orchestrator_position_importance", "standard"
                ),
                "uncertainty_level": "high",
                "evidence_conflict_level": "medium",
                "continue_research": False,
                "stop_reason": "No research capabilities selected.",
                "add_capabilities": [],
                "active_capabilities": [],
                "reserve_capabilities": [],
                "trigger_counterevidence_search": False,
                "counterevidence_focus": "",
                "research_mode": "parallel_hard_loop",
                "missing_capabilities": [],
            }
            return {
                "selected_analysts": [],
                "analysis_queue": [],
                "completed_analysts": [],
                "current_analyst": "",
                "analysis_plan": "## Investment Orchestration Plan\nNo research capabilities selected.",
                "analysis_brief": "",
                "temporal_context": state.get("temporal_context") or {},
                "portfolio_context": build_portfolio_context_state_update(
                    state.get("portfolio_context"),
                    {},
                ),
                "orchestration_state": orchestration_state,
            }

        reserve_capabilities = (
            [
                key
                for key in ANALYST_ORDER
                if key not in selected_analysts and key not in completed_analysts
            ]
            if allow_expansion
            else []
        )
        remaining_choices = _default_remaining_order(selected_analysts, completed_analysts)
        token_budget = _normalize_choice(
            existing_orchestration_state.get("token_budget")
            or config.get("orchestrator_token_budget"),
            TOKEN_BUDGET_LEVELS,
            "balanced",
        )
        position_importance = _normalize_choice(
            existing_orchestration_state.get("position_importance")
            or config.get("orchestrator_position_importance"),
            POSITION_IMPORTANCE_LEVELS,
            "standard",
        )
        plan_data: Dict[str, Any] = {}

        if not config.get("enable_investment_orchestrator", True):
            remaining_order = remaining_choices
        elif not remaining_choices:
            remaining_order = []
        elif config.get("analysis_routing_mode") == "sequential":
            remaining_order = remaining_choices
        else:
            dossier_snapshot = render_dossier_brief(
                state.get("decision_dossier"),
                RESEARCH_DOSSIER_BRIEF_KEYS,
            )
            temporal_context_snapshot = render_temporal_context_brief(
                state.get("temporal_context")
            )
            prompt = f"""You are the chief investment orchestrator for an AI-native long/short investment institution.

Your job is not to make a one-time schedule. Your job is to act like the institution's research command center.

You must decide:
- whether research should continue
- whether reserve capability modules should be activated
- whether counterevidence search should intensify
- when the system has enough evidence to stop researching and move to thesis synthesis

Return valid JSON only with these keys:
- objective: string
- thesis_focus: string
- risk_focus: string
- catalyst_focus: string
- key_questions: array of strings
- ordered_capabilities: array of capability ids
- add_capabilities: array of capability ids
- continue_research: boolean
- stop_reason: string
- uncertainty_level: one of low, medium, high
- evidence_conflict_level: one of low, medium, high
- token_budget: one of tight, balanced, expansive
- position_importance: one of standard, high, critical
- portfolio_role: string
- position_archetype: string
- book_correlation_view: string
- crowding_risk: string
- capital_budget: string
- risk_budget: string
- trigger_counterevidence_search: boolean
- counterevidence_focus: string

Rules:
- ordered_capabilities may only use active or newly added capability ids.
- add_capabilities may only come from the reserve capability list.
- If uncertainty is high, evidence is conflicted, or the position is important, keep researching unless budget is severely constrained.
- If evidence is coherent and the remaining modules are unlikely to change the institutional conclusion, stop and hand off.
- Trigger counterevidence search when the evidence is too one-sided or the thesis still feels fragile.
- Be explicit about the tradeoff between research depth and token budget.
- Establish a front-loaded portfolio context before the rest of the institution works:
  what role this seat should play, what type of position it is, what overlap it might have with the current book, and how much capital/risk budget it deserves.

{build_instrument_context(state["company_of_interest"])}
Trade date: {state["trade_date"]}
Token budget posture: {token_budget}
Position importance: {position_importance}

Active capabilities:
{get_capability_catalog(selected_analysts)}

Reserve capabilities:
{get_capability_catalog(reserve_capabilities)}

Completed capability reports:
{_format_completed_reports(completed_reports)}

Structured dossier snapshot:
{dossier_snapshot}

Temporal context:
{temporal_context_snapshot}

Institutional memory:
{institution_memory_brief}
"""
            response = llm.invoke(prompt)
            plan_data = _parse_json_response(response.content)
            token_budget = _normalize_choice(
                plan_data.get("token_budget"),
                TOKEN_BUDGET_LEVELS,
                token_budget,
            )
            position_importance = _normalize_choice(
                plan_data.get("position_importance"),
                POSITION_IMPORTANCE_LEVELS,
                position_importance,
            )

        additions = (
            _sanitize_capability_additions(
                plan_data.get("add_capabilities"),
                reserve_capabilities,
            )
            if allow_expansion
            else []
        )
        active_capabilities = normalize_selected_analysts(selected_analysts + additions)
        remaining_order = _sanitize_capability_order(
            plan_data.get("ordered_capabilities"),
            active_capabilities,
            completed_analysts,
        )
        if additions:
            remaining_order = _ensure_additions_are_scheduled(remaining_order, additions)

        uncertainty_level = _normalize_choice(
            plan_data.get("uncertainty_level"),
            SIGNAL_LEVELS,
            "high" if len(completed_reports) < 2 else "medium",
        )
        evidence_conflict_level = _normalize_choice(
            plan_data.get("evidence_conflict_level"),
            SIGNAL_LEVELS,
            "medium",
        )
        continue_research_default = _default_continue_research(
            len(completed_reports),
            len(remaining_order),
            uncertainty_level,
            evidence_conflict_level,
            token_budget,
            position_importance,
        )
        continue_research = _coerce_bool(
            plan_data.get("continue_research"),
            continue_research_default,
        )
        if not remaining_order:
            continue_research = False

        trigger_counterevidence_search = _coerce_bool(
            plan_data.get("trigger_counterevidence_search"),
            _default_counterevidence_search(
                evidence_conflict_level,
                uncertainty_level,
                len(completed_reports),
            ),
        )
        counterevidence_focus = _clean_text(plan_data.get("counterevidence_focus"))
        stop_reason = _clean_text(plan_data.get("stop_reason")) or _default_stop_reason(
            continue_research,
            remaining_order,
            uncertainty_level,
            evidence_conflict_level,
            token_budget,
        )

        if not continue_research:
            remaining_order = []

        orchestration_state = {
            "token_budget": token_budget,
            "position_importance": position_importance,
            "uncertainty_level": uncertainty_level,
            "evidence_conflict_level": evidence_conflict_level,
            "continue_research": continue_research,
            "stop_reason": stop_reason,
            "add_capabilities": additions,
            "active_capabilities": active_capabilities,
            "reserve_capabilities": [
                key for key in ANALYST_ORDER if key not in active_capabilities and key not in completed_analysts
            ],
            "trigger_counterevidence_search": trigger_counterevidence_search,
            "counterevidence_focus": counterevidence_focus,
            "research_mode": "parallel_hard_loop",
            "missing_capabilities": [],
        }

        existing_portfolio_context = state.get("portfolio_context") or {}
        portfolio_context = build_portfolio_context_state_update(
            existing_portfolio_context,
            {
                "portfolio_role": _clean_text(plan_data.get("portfolio_role"))
                or existing_portfolio_context.get("portfolio_role")
                or _default_portfolio_role(position_importance, active_capabilities),
                "position_archetype": _clean_text(plan_data.get("position_archetype"))
                or existing_portfolio_context.get("position_archetype")
                or _default_position_archetype(active_capabilities),
                "book_correlation_view": _clean_text(
                    plan_data.get("book_correlation_view")
                )
                or existing_portfolio_context.get("book_correlation_view")
                or _default_book_correlation_view(active_capabilities),
                "crowding_risk": _clean_text(plan_data.get("crowding_risk"))
                or existing_portfolio_context.get("crowding_risk")
                or _default_crowding_risk(
                    evidence_conflict_level, active_capabilities
                ),
                "capital_budget": _clean_text(plan_data.get("capital_budget"))
                or existing_portfolio_context.get("capital_budget")
                or _default_capital_budget(position_importance, token_budget),
                "risk_budget": _clean_text(plan_data.get("risk_budget"))
                or existing_portfolio_context.get("risk_budget")
                or _default_risk_budget(
                    position_importance, uncertainty_level
                ),
            },
        )

        plan_text = _build_plan_text(
            plan_data,
            orchestration_state,
            portfolio_context,
            temporal_context,
            remaining_order,
            active_capabilities,
            completed_analysts,
        )
        journal_entry = (
            f"Completed: {', '.join(completed_analysts) or 'none'} | "
            f"Remaining: {', '.join(remaining_order) or 'none'} | "
            f"Added: {', '.join(additions) or 'none'} | "
            f"Uncertainty: {uncertainty_level} | "
            f"Conflict: {evidence_conflict_level} | "
            f"Counterevidence: {'on' if trigger_counterevidence_search else 'standard'} | "
            f"Continue: {'yes' if continue_research else 'no'}"
        )
        orchestration_journal = list(state.get("orchestration_journal", []))
        if not orchestration_journal or orchestration_journal[-1] != journal_entry:
            orchestration_journal.append(journal_entry)

        result = {
            "selected_analysts": active_capabilities,
            "analysis_queue": remaining_order,
            "completed_analysts": completed_analysts,
            "current_analyst": "",
            "analysis_plan": plan_text,
            "analysis_brief": _build_analysis_brief(
                state["company_of_interest"],
                state["trade_date"],
                plan_data,
                orchestration_state,
                portfolio_context,
                temporal_context,
                institution_memory_brief,
            ),
            "orchestration_state": orchestration_state,
            "portfolio_context": portfolio_context,
            "temporal_context": temporal_context,
            "orchestration_journal": orchestration_journal,
        }
        result.update(
            build_dossier_update(
                state,
                portfolio_context.get("full_context", ""),
                PORTFOLIO_CONTEXT_SECTION_MAP,
            )
        )
        return result

    return investment_orchestrator_node
