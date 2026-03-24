import re
from typing import Any, Dict, Iterable, Sequence

from tradingagents.agents.utils.agent_utils import (
    CAPITAL_ALLOCATION_COMMITTEE,
    CHALLENGE_ENGINE,
    DOWNSIDE_GUARDRAIL_ENGINE,
    INVESTMENT_DIRECTOR,
    PORTFOLIO_FIT_ENGINE,
    THESIS_ENGINE,
    UPSIDE_CAPTURE_ENGINE,
)


THESIS_STAGE_KEY = "thesis_case"
CHALLENGE_STAGE_KEY = "challenge_case"
UPSIDE_STAGE_KEY = "upside_case"
DOWNSIDE_STAGE_KEY = "downside_case"
PORTFOLIO_FIT_STAGE_KEY = "portfolio_fit_case"

THESIS_REVIEW_STAGE_ORDER = [THESIS_STAGE_KEY, CHALLENGE_STAGE_KEY]
ALLOCATION_REVIEW_STAGE_ORDER = [
    UPSIDE_STAGE_KEY,
    DOWNSIDE_STAGE_KEY,
    PORTFOLIO_FIT_STAGE_KEY,
]


DECISION_DOSSIER_ORDER = [
    ("world_model", "World Model"),
    ("final_recommendation", "Final Recommendation"),
    ("business_truth", "Business Truth"),
    ("earnings_power", "Earnings Power"),
    ("balance_sheet_resilience", "Balance Sheet / Resilience"),
    ("critical_assumptions", "Critical Assumptions"),
    ("long_cycle_mispricing", "Long-Cycle Mispricing"),
    ("market_expectations_view", "Market Expectations"),
    ("positioning_signal", "Positioning / Momentum"),
    ("attention_regime", "Attention Regime"),
    ("narrative_momentum", "Narrative Momentum"),
    ("sentiment_inflection", "Sentiment Inflection"),
    ("event_map", "Event Map"),
    ("medium_cycle_rerating_path", "Medium-Cycle Re-Rating Path"),
    ("short_cycle_execution_window", "Short-Cycle Execution Window"),
    ("core_thesis", "Core Thesis"),
    ("variant_perception", "Variant Perception"),
    ("supporting_evidence", "Supporting Evidence"),
    ("consensus_view", "Consensus View"),
    ("counterevidence", "Counterevidence"),
    ("failure_modes", "Failure Modes"),
    ("catalyst_path", "Catalyst Path"),
    ("time_horizon", "Time Horizon"),
    ("timing_triggers", "Timing Triggers"),
    ("execution_plan", "Execution Plan"),
    ("entry_framework", "Entry Framework"),
    ("liquidity_plan", "Liquidity Plan"),
    ("position_archetype", "Position Archetype"),
    ("book_correlation_view", "Book Correlation"),
    ("crowding_risk", "Crowding / Factor Overlap"),
    ("position_sizing", "Position Sizing"),
    ("capital_budget", "Capital Budget"),
    ("risk_budget", "Risk Budget"),
    ("scenario_map", "Scenario Map"),
    ("portfolio_role", "Portfolio Role"),
    ("portfolio_fit", "Portfolio Fit"),
    ("risk_guardrails", "Risk Guardrails"),
    ("kill_criteria", "Kill Criteria"),
    ("monitoring_triggers", "Monitoring Triggers"),
    ("capital_allocation_rationale", "Capital Allocation Rationale"),
]

BUSINESS_TRUTH_SECTION_MAP = {
    "business_truth": ["Business Reality"],
    "earnings_power": ["Earnings Power"],
    "balance_sheet_resilience": ["Balance Sheet / Resilience"],
    "critical_assumptions": ["What Must Be True"],
    "long_cycle_mispricing": ["Long-Cycle Mispricing"],
}

MARKET_EXPECTATIONS_SECTION_MAP = {
    "market_expectations_view": ["What Seems Priced In"],
    "positioning_signal": ["Positioning / Momentum Read"],
    "timing_triggers": ["Implications For Timing"],
    "short_cycle_execution_window": [
        "Execution Window Pressure",
        "Implications For Timing",
    ],
}

WHY_NOW_SECTION_MAP = {
    "attention_regime": ["Attention Shift"],
    "narrative_momentum": ["Narrative Momentum"],
    "sentiment_inflection": ["Sentiment Inflection"],
    "time_horizon": ["Why This Matters Now"],
    "short_cycle_execution_window": ["Short-Cycle Execution Window"],
}

CATALYST_PATH_SECTION_MAP = {
    "event_map": ["Event Map"],
    "catalyst_path": ["Catalyst Tree"],
    "time_horizon": ["Timeline"],
    "timing_triggers": ["Market-Relevance"],
    "medium_cycle_rerating_path": ["Medium-Cycle Re-Rating Path"],
}

THESIS_ENGINE_SECTION_MAP = {
    "core_thesis": ["Core Thesis"],
    "variant_perception": ["Variant Perception"],
    "supporting_evidence": ["Supporting Evidence"],
    "catalyst_path": ["Catalyst Path"],
}

CHALLENGE_ENGINE_SECTION_MAP = {
    "consensus_view": ["Consensus View"],
    "counterevidence": ["Counterevidence"],
    "failure_modes": ["Failure Modes"],
    "kill_criteria": ["Kill Criteria"],
}

INVESTMENT_DIRECTOR_SECTION_MAP = {
    "world_model": ["World Model"],
    "final_recommendation": ["Recommended Stance"],
    "core_thesis": ["Mispricing Narrative"],
    "variant_perception": ["What The Market Is Missing"],
    "supporting_evidence": ["Evidence That Matters"],
    "long_cycle_mispricing": ["Long-Cycle Mispricing"],
    "medium_cycle_rerating_path": ["Medium-Cycle Re-Rating Path"],
    "short_cycle_execution_window": ["Short-Cycle Execution Window"],
    "catalyst_path": ["Catalyst Path"],
    "time_horizon": ["Time Horizon"],
    "portfolio_role": ["Portfolio Role"],
    "position_sizing": ["Initial Sizing View"],
    "kill_criteria": ["Kill Criteria"],
}

EXECUTION_ENGINE_SECTION_MAP = {
    "execution_plan": ["Execution Plan"],
    "entry_framework": ["Entry Framework"],
    "position_sizing": ["Position Construction"],
    "liquidity_plan": ["Liquidity Plan"],
    "monitoring_triggers": ["Monitoring Plan"],
}

UPSIDE_CAPTURE_SECTION_MAP = {
    "supporting_evidence": ["Upside Capture"],
    "position_sizing": ["If Right, Press Here"],
    "capital_allocation_rationale": ["Asymmetric Expressions"],
}

DOWNSIDE_GUARDRAIL_SECTION_MAP = {
    "failure_modes": ["Downside Map"],
    "risk_guardrails": ["Hard Limits"],
    "kill_criteria": ["Kill Criteria"],
    "scenario_map": ["Scenario Map"],
}

PORTFOLIO_FIT_SECTION_MAP = {
    "portfolio_role": ["Portfolio Role"],
    "portfolio_fit": ["Portfolio Fit"],
    "book_correlation_view": ["Correlation / Crowding"],
    "crowding_risk": ["Correlation / Crowding"],
    "risk_guardrails": ["Correlation / Crowding"],
    "capital_budget": ["Capital Budget"],
    "scenario_map": ["Scenario Map"],
}

PORTFOLIO_CONTEXT_SECTION_MAP = {
    "portfolio_role": ["Portfolio Role"],
    "position_archetype": ["Position Archetype"],
    "book_correlation_view": ["Correlation To Current Book"],
    "crowding_risk": ["Crowding / Factor Overlap"],
    "capital_budget": ["Capital Budget"],
    "risk_budget": ["Risk Budget"],
}

CAPITAL_ALLOCATION_SECTION_MAP = {
    "final_recommendation": ["Rating"],
    "portfolio_role": ["Portfolio Mandate"],
    "position_sizing": ["Position Size"],
    "entry_framework": ["Entry / Exit"],
    "kill_criteria": ["Kill Criteria"],
    "monitoring_triggers": ["Monitoring Triggers"],
    "capital_allocation_rationale": ["Capital Allocation Rationale"],
}

EXECUTION_STATE_SECTION_MAP = {
    "execution_plan": ["Execution Plan"],
    "entry_framework": ["Entry Framework"],
    "position_construction": ["Position Construction"],
    "liquidity_plan": ["Liquidity Plan"],
    "monitoring_plan": ["Monitoring Plan"],
}

FINAL_DECISION_STATE_SECTION_MAP = {
    "rating": ["Rating"],
    "portfolio_mandate": ["Portfolio Mandate"],
    "position_size": ["Position Size"],
    "entry_exit": ["Entry / Exit"],
    "kill_criteria": ["Kill Criteria"],
    "monitoring_triggers": ["Monitoring Triggers"],
    "capital_allocation_rationale": ["Capital Allocation Rationale"],
}

RESEARCH_DOSSIER_BRIEF_KEYS = [
    "business_truth",
    "earnings_power",
    "balance_sheet_resilience",
    "long_cycle_mispricing",
    "market_expectations_view",
    "positioning_signal",
    "attention_regime",
    "narrative_momentum",
    "event_map",
    "catalyst_path",
    "time_horizon",
    "medium_cycle_rerating_path",
    "short_cycle_execution_window",
    "portfolio_role",
    "position_archetype",
    "book_correlation_view",
    "capital_budget",
    "risk_budget",
]

EXECUTION_DOSSIER_BRIEF_KEYS = [
    "world_model",
    "core_thesis",
    "variant_perception",
    "long_cycle_mispricing",
    "medium_cycle_rerating_path",
    "short_cycle_execution_window",
    "catalyst_path",
    "time_horizon",
    "position_sizing",
    "portfolio_role",
    "position_archetype",
    "book_correlation_view",
    "capital_budget",
    "risk_budget",
]

RISK_DOSSIER_BRIEF_KEYS = [
    "world_model",
    "core_thesis",
    "variant_perception",
    "long_cycle_mispricing",
    "medium_cycle_rerating_path",
    "short_cycle_execution_window",
    "failure_modes",
    "catalyst_path",
    "time_horizon",
    "position_sizing",
    "portfolio_role",
    "position_archetype",
    "book_correlation_view",
    "crowding_risk",
    "capital_budget",
    "risk_budget",
    "liquidity_plan",
]

CAPITAL_ALLOCATION_DOSSIER_BRIEF_KEYS = [
    "world_model",
    "core_thesis",
    "variant_perception",
    "long_cycle_mispricing",
    "medium_cycle_rerating_path",
    "short_cycle_execution_window",
    "failure_modes",
    "catalyst_path",
    "time_horizon",
    "portfolio_role",
    "position_archetype",
    "book_correlation_view",
    "crowding_risk",
    "capital_budget",
    "risk_budget",
    "risk_guardrails",
    "kill_criteria",
    "monitoring_triggers",
]


def normalize_heading_key(heading: str) -> str:
    """Normalize markdown headings for fuzzy section matching."""
    return re.sub(r"[^a-z0-9]+", "_", heading.strip().lower()).strip("_")


def _clean_text(text: str | None) -> str:
    return (text or "").strip()


def _format_agent_turn(agent_name: str, content: str) -> str:
    cleaned = _clean_text(content)
    if not cleaned:
        return ""
    return f"{agent_name}: {cleaned}"


def create_review_loop_state(stage_order: Iterable[str]) -> Dict[str, Any]:
    """Create a normalized review-loop container."""
    return {
        "stage_order": list(stage_order),
        "active_stage": "",
        "round_index": 0,
        "transcript": [],
        "outputs": {},
        "final_memo": "",
        "completion_reason": "",
    }


def create_execution_state() -> Dict[str, str]:
    """Create the execution-state container."""
    return {
        "full_blueprint": "",
        "execution_plan": "",
        "entry_framework": "",
        "position_construction": "",
        "liquidity_plan": "",
        "monitoring_plan": "",
    }


def create_final_decision_state() -> Dict[str, str]:
    """Create the structured final-decision container."""
    return {
        "full_decision": "",
        "rating": "",
        "portfolio_mandate": "",
        "position_size": "",
        "entry_exit": "",
        "kill_criteria": "",
        "monitoring_triggers": "",
        "capital_allocation_rationale": "",
    }


def create_orchestration_state() -> Dict[str, Any]:
    """Create the orchestration control-state container."""
    return {
        "token_budget": "balanced",
        "position_importance": "standard",
        "uncertainty_level": "medium",
        "evidence_conflict_level": "medium",
        "continue_research": True,
        "stop_reason": "",
        "add_capabilities": [],
        "active_capabilities": [],
        "reserve_capabilities": [],
        "trigger_counterevidence_search": False,
        "counterevidence_focus": "",
    }


def create_portfolio_context_state() -> Dict[str, str]:
    """Create the front-loaded portfolio-context container."""
    return {
        "full_context": "",
        "portfolio_role": "",
        "position_archetype": "",
        "book_correlation_view": "",
        "crowding_risk": "",
        "capital_budget": "",
        "risk_budget": "",
    }


def create_temporal_context_state() -> Dict[str, str]:
    """Create the temporal-context container."""
    return {
        "full_context": "",
        "long_cycle_mispricing": "",
        "medium_cycle_rerating_path": "",
        "short_cycle_execution_window": "",
    }


def append_review_stage_output(
    review_state: Dict[str, Any] | None,
    stage_key: str,
    agent_name: str,
    content: str,
) -> Dict[str, Any]:
    """Append a turn to a normalized review loop."""
    current = dict(review_state or {})
    cleaned = _clean_text(content)
    transcript = list(current.get("transcript") or [])
    outputs = dict(current.get("outputs") or {})

    if cleaned:
        transcript.append(
            {
                "stage": stage_key,
                "agent": agent_name,
                "content": cleaned,
            }
        )
        outputs[stage_key] = cleaned

    return {
        "stage_order": list(current.get("stage_order") or []),
        "active_stage": agent_name,
        "round_index": int(current.get("round_index", 0)) + (1 if cleaned else 0),
        "transcript": transcript,
        "outputs": outputs,
        "final_memo": current.get("final_memo", ""),
        "completion_reason": current.get("completion_reason", ""),
    }


def finalize_review_loop(
    review_state: Dict[str, Any] | None,
    agent_name: str,
    final_memo: str,
    completion_reason: str = "completed",
) -> Dict[str, Any]:
    """Finalize a normalized review loop without incrementing the round counter."""
    current = dict(review_state or {})
    return {
        "stage_order": list(current.get("stage_order") or []),
        "active_stage": agent_name,
        "round_index": int(current.get("round_index", 0)),
        "transcript": list(current.get("transcript") or []),
        "outputs": dict(current.get("outputs") or {}),
        "final_memo": _clean_text(final_memo),
        "completion_reason": completion_reason,
    }


def get_review_output(review_state: Dict[str, Any] | None, stage_key: str) -> str:
    """Fetch the latest memo for a review stage."""
    outputs = dict((review_state or {}).get("outputs") or {})
    return _clean_text(outputs.get(stage_key, ""))


def render_review_transcript(
    review_state: Dict[str, Any] | None,
    stage_keys: Sequence[str] | None = None,
) -> str:
    """Render a review loop transcript with optional stage filtering."""
    allowed = set(stage_keys or [])
    parts = []

    for turn in (review_state or {}).get("transcript") or []:
        stage = turn.get("stage", "")
        if allowed and stage not in allowed:
            continue
        agent_name = turn.get("agent", stage or "Unknown")
        content = _clean_text(turn.get("content", ""))
        if content:
            parts.append(_format_agent_turn(agent_name, content))

    return "\n\n".join(parts)


def build_execution_state_update(
    existing: Dict[str, str] | None, text: str
) -> Dict[str, str]:
    """Update the normalized execution state from a memo."""
    updated = dict(existing or {})
    cleaned = _clean_text(text)
    if cleaned:
        updated["full_blueprint"] = cleaned
        updated.update(extract_named_sections(cleaned, EXECUTION_STATE_SECTION_MAP))
    return updated


def build_final_decision_state_update(
    existing: Dict[str, str] | None, text: str
) -> Dict[str, str]:
    """Update the normalized final decision state from a memo."""
    updated = dict(existing or {})
    cleaned = _clean_text(text)
    if cleaned:
        updated["full_decision"] = cleaned
        updated.update(extract_named_sections(cleaned, FINAL_DECISION_STATE_SECTION_MAP))
    return updated


def render_portfolio_context(portfolio_context: Dict[str, str] | None) -> str:
    """Render the front-loaded portfolio context as markdown."""
    portfolio_context = portfolio_context or {}
    sections = [
        ("portfolio_role", "Portfolio Role"),
        ("position_archetype", "Position Archetype"),
        ("book_correlation_view", "Correlation To Current Book"),
        ("crowding_risk", "Crowding / Factor Overlap"),
        ("capital_budget", "Capital Budget"),
        ("risk_budget", "Risk Budget"),
    ]
    parts = []
    for key, heading in sections:
        value = _clean_text(portfolio_context.get(key, ""))
        if value:
            parts.append(f"## {heading}\n{value}")
    return "\n\n".join(parts)


def render_temporal_context(temporal_context: Dict[str, str] | None) -> str:
    """Render the temporal context as markdown."""
    temporal_context = temporal_context or {}
    sections = [
        ("long_cycle_mispricing", "Long-Cycle Mispricing"),
        ("medium_cycle_rerating_path", "Medium-Cycle Re-Rating Path"),
        ("short_cycle_execution_window", "Short-Cycle Execution Window"),
    ]
    parts = []
    for key, heading in sections:
        value = _clean_text(temporal_context.get(key, ""))
        if value:
            parts.append(f"## {heading}\n{value}")
    return "\n\n".join(parts)


def build_portfolio_context_state_update(
    existing: Dict[str, str] | None,
    updates: Dict[str, Any] | None,
) -> Dict[str, str]:
    """Update the canonical portfolio-context state and keep the rendered memo in sync."""
    current = create_portfolio_context_state()
    current.update(existing or {})

    for key in (
        "portfolio_role",
        "position_archetype",
        "book_correlation_view",
        "crowding_risk",
        "capital_budget",
        "risk_budget",
    ):
        value = _clean_text((updates or {}).get(key, ""))
        if value:
            current[key] = value

    current["full_context"] = render_portfolio_context(current)
    return current


def build_temporal_context_state_update(
    existing: Dict[str, str] | None,
    updates: Dict[str, Any] | None,
) -> Dict[str, str]:
    """Update the canonical temporal-context state and keep the rendered memo in sync."""
    current = create_temporal_context_state()
    current.update(existing or {})

    for key in (
        "long_cycle_mispricing",
        "medium_cycle_rerating_path",
        "short_cycle_execution_window",
    ):
        value = _clean_text((updates or {}).get(key, ""))
        if value:
            current[key] = value

    current["full_context"] = render_temporal_context(current)
    return current


def _latest_review_turn(review_state: Dict[str, Any] | None) -> Dict[str, str]:
    transcript = list((review_state or {}).get("transcript") or [])
    return transcript[-1] if transcript else {}


def build_legacy_investment_debate_state(
    review_state: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Mirror the normalized thesis review into the legacy debate schema."""
    latest_turn = _latest_review_turn(review_state)
    latest_content = _format_agent_turn(
        latest_turn.get("agent", ""),
        latest_turn.get("content", ""),
    )
    return {
        "bull_history": render_review_transcript(review_state, [THESIS_STAGE_KEY]),
        "bear_history": render_review_transcript(review_state, [CHALLENGE_STAGE_KEY]),
        "history": render_review_transcript(review_state),
        "latest_speaker": (review_state or {}).get("active_stage", ""),
        "current_response": latest_content,
        "judge_decision": _clean_text((review_state or {}).get("final_memo", "")),
        "count": int((review_state or {}).get("round_index", 0)),
    }


def build_legacy_risk_debate_state(
    review_state: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Mirror the normalized allocation review into the legacy risk schema."""
    return {
        "aggressive_history": render_review_transcript(review_state, [UPSIDE_STAGE_KEY]),
        "conservative_history": render_review_transcript(
            review_state, [DOWNSIDE_STAGE_KEY]
        ),
        "neutral_history": render_review_transcript(
            review_state, [PORTFOLIO_FIT_STAGE_KEY]
        ),
        "history": render_review_transcript(review_state),
        "latest_speaker": (review_state or {}).get("active_stage", ""),
        "current_aggressive_response": _format_agent_turn(
            UPSIDE_CAPTURE_ENGINE,
            get_review_output(review_state, UPSIDE_STAGE_KEY),
        ),
        "current_conservative_response": _format_agent_turn(
            DOWNSIDE_GUARDRAIL_ENGINE,
            get_review_output(review_state, DOWNSIDE_STAGE_KEY),
        ),
        "current_neutral_response": _format_agent_turn(
            PORTFOLIO_FIT_ENGINE,
            get_review_output(review_state, PORTFOLIO_FIT_STAGE_KEY),
        ),
        "judge_decision": _clean_text((review_state or {}).get("final_memo", "")),
        "count": int((review_state or {}).get("round_index", 0)),
    }


def extract_markdown_sections(text: str) -> Dict[str, str]:
    """Parse markdown sections keyed by normalized heading text."""
    if not text or not text.strip():
        return {}

    pattern = re.compile(r"^##+\s+(.*?)\s*$\n?([\s\S]*?)(?=^##+\s+|\Z)", re.MULTILINE)
    sections = {}

    for match in pattern.finditer(text):
        heading = normalize_heading_key(match.group(1))
        body = match.group(2).strip()
        if heading and body:
            sections[heading] = body

    return sections


def extract_named_sections(
    text: str, section_map: Dict[str, Iterable[str]]
) -> Dict[str, str]:
    """Extract named dossier fields from markdown text using heading aliases."""
    sections = extract_markdown_sections(text)
    extracted = {}

    for dossier_key, aliases in section_map.items():
        for alias in aliases:
            match = sections.get(normalize_heading_key(alias))
            if match:
                extracted[dossier_key] = match
                break

    return extracted


def merge_decision_dossier(
    existing: Dict[str, str] | None, updates: Dict[str, str] | None
) -> Dict[str, str]:
    """Merge dossier updates, preferring new non-empty values."""
    merged = dict(existing or {})

    for key, value in (updates or {}).items():
        if value and value.strip():
            merged[key] = value.strip()

    return merged


def render_decision_dossier(dossier: Dict[str, str] | None) -> str:
    """Render a dossier as a markdown summary."""
    dossier = dossier or {}
    parts = ["## AI Investment Dossier"]

    for dossier_key, title in DECISION_DOSSIER_ORDER:
        value = dossier.get(dossier_key, "").strip()
        if value:
            parts.append(f"### {title}\n{value}")

    return "\n\n".join(parts)


def render_dossier_brief(
    dossier: Dict[str, str] | None,
    keys: Iterable[str],
    heading: str = "## Institutional Dossier Snapshot",
) -> str:
    """Render a filtered dossier view for downstream prompts."""
    dossier = dossier or {}
    parts = [heading]

    for dossier_key in keys:
        value = dossier.get(dossier_key, "").strip()
        if value:
            title = dict(DECISION_DOSSIER_ORDER).get(dossier_key, dossier_key)
            parts.append(f"### {title}\n{value}")

    if len(parts) == 1:
        parts.append("No structured dossier fields have been populated yet.")

    return "\n\n".join(parts)


def render_portfolio_context_brief(
    portfolio_context: Dict[str, str] | None,
    heading: str = "## Front-Loaded Portfolio Context",
) -> str:
    """Render the front-loaded portfolio context for downstream prompts."""
    rendered = render_portfolio_context(portfolio_context)
    if rendered:
        return f"{heading}\n\n{rendered}"
    return f"{heading}\n\nPortfolio context has not been established yet."


def render_temporal_context_brief(
    temporal_context: Dict[str, str] | None,
    heading: str = "## Temporal Context",
) -> str:
    """Render the long/medium/short horizon split for downstream prompts."""
    rendered = render_temporal_context(temporal_context)
    if rendered:
        return f"{heading}\n\n{rendered}"
    return f"{heading}\n\nTemporal context has not been established yet."


def build_dossier_update(
    state: Dict[str, str] | Dict[str, object],
    text: str,
    section_map: Dict[str, Iterable[str]],
    raw_text_key: str | None = None,
) -> Dict[str, object]:
    """Create a state update payload for the decision dossier."""
    updates = extract_named_sections(text, section_map)

    if raw_text_key and text and text.strip():
        updates[raw_text_key] = text.strip()

    dossier = merge_decision_dossier(state.get("decision_dossier"), updates)
    return {
        "decision_dossier": dossier,
        "decision_dossier_markdown": render_decision_dossier(dossier),
    }


def build_temporal_context_update(
    state: Dict[str, str] | Dict[str, object],
    text: str,
    section_map: Dict[str, Iterable[str]],
) -> Dict[str, object]:
    """Create a state update payload for the temporal context."""
    updates = extract_named_sections(text, section_map)
    temporal_context = build_temporal_context_state_update(
        state.get("temporal_context"),
        updates,
    )
    return {"temporal_context": temporal_context}
