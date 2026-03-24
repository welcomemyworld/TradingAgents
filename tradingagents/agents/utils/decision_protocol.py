import re
from typing import Dict, Iterable


DECISION_DOSSIER_ORDER = [
    ("world_model", "World Model"),
    ("final_recommendation", "Final Recommendation"),
    ("business_truth", "Business Truth"),
    ("earnings_power", "Earnings Power"),
    ("balance_sheet_resilience", "Balance Sheet / Resilience"),
    ("critical_assumptions", "Critical Assumptions"),
    ("market_expectations_view", "Market Expectations"),
    ("positioning_signal", "Positioning / Momentum"),
    ("attention_regime", "Attention Regime"),
    ("narrative_momentum", "Narrative Momentum"),
    ("sentiment_inflection", "Sentiment Inflection"),
    ("event_map", "Event Map"),
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
    ("position_sizing", "Position Sizing"),
    ("capital_budget", "Capital Budget"),
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
}

MARKET_EXPECTATIONS_SECTION_MAP = {
    "market_expectations_view": ["What Seems Priced In"],
    "positioning_signal": ["Positioning / Momentum Read"],
    "timing_triggers": ["Implications For Timing"],
}

WHY_NOW_SECTION_MAP = {
    "attention_regime": ["Attention Shift"],
    "narrative_momentum": ["Narrative Momentum"],
    "sentiment_inflection": ["Sentiment Inflection"],
    "time_horizon": ["Why This Matters Now"],
}

CATALYST_PATH_SECTION_MAP = {
    "event_map": ["Event Map"],
    "catalyst_path": ["Catalyst Tree"],
    "time_horizon": ["Timeline"],
    "timing_triggers": ["Market-Relevance"],
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
    "risk_guardrails": ["Correlation / Crowding"],
    "capital_budget": ["Capital Budget"],
    "scenario_map": ["Scenario Map"],
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

RESEARCH_DOSSIER_BRIEF_KEYS = [
    "business_truth",
    "earnings_power",
    "balance_sheet_resilience",
    "market_expectations_view",
    "positioning_signal",
    "attention_regime",
    "narrative_momentum",
    "event_map",
    "catalyst_path",
    "time_horizon",
]

EXECUTION_DOSSIER_BRIEF_KEYS = [
    "world_model",
    "core_thesis",
    "variant_perception",
    "catalyst_path",
    "time_horizon",
    "position_sizing",
    "portfolio_role",
]

RISK_DOSSIER_BRIEF_KEYS = [
    "world_model",
    "core_thesis",
    "variant_perception",
    "failure_modes",
    "catalyst_path",
    "time_horizon",
    "position_sizing",
    "portfolio_role",
    "liquidity_plan",
]

CAPITAL_ALLOCATION_DOSSIER_BRIEF_KEYS = [
    "world_model",
    "core_thesis",
    "variant_perception",
    "failure_modes",
    "catalyst_path",
    "time_horizon",
    "portfolio_role",
    "capital_budget",
    "risk_guardrails",
    "kill_criteria",
    "monitoring_triggers",
]


def normalize_heading_key(heading: str) -> str:
    """Normalize markdown headings for fuzzy section matching."""
    return re.sub(r"[^a-z0-9]+", "_", heading.strip().lower()).strip("_")


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
