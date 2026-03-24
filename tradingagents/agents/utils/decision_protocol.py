import re
from typing import Dict, Iterable


DECISION_DOSSIER_ORDER = [
    ("final_recommendation", "Final Recommendation"),
    ("core_thesis", "Core Thesis"),
    ("variant_perception", "Variant Perception"),
    ("supporting_evidence", "Supporting Evidence"),
    ("consensus_view", "Consensus View"),
    ("counterevidence", "Counterevidence"),
    ("failure_modes", "Failure Modes"),
    ("catalyst_path", "Catalyst Path"),
    ("timing_triggers", "Timing Triggers"),
    ("execution_plan", "Execution Plan"),
    ("entry_framework", "Entry Framework"),
    ("position_sizing", "Position Sizing"),
    ("portfolio_fit", "Portfolio Fit"),
    ("risk_guardrails", "Risk Guardrails"),
    ("kill_criteria", "Kill Criteria"),
    ("monitoring_triggers", "Monitoring Triggers"),
    ("capital_allocation_rationale", "Capital Allocation Rationale"),
]

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
    "final_recommendation": ["Recommended Stance"],
    "core_thesis": ["Mispricing Narrative"],
    "variant_perception": ["What The Market Is Missing"],
    "supporting_evidence": ["Evidence That Matters"],
    "catalyst_path": ["Catalyst Path"],
    "timing_triggers": ["Timing Triggers"],
    "position_sizing": ["Initial Sizing View"],
    "kill_criteria": ["Kill Criteria"],
}

EXECUTION_ENGINE_SECTION_MAP = {
    "execution_plan": ["Execution Plan"],
    "entry_framework": ["Entry Framework"],
    "position_sizing": ["Position Construction"],
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
}

PORTFOLIO_FIT_SECTION_MAP = {
    "portfolio_fit": ["Portfolio Fit"],
    "risk_guardrails": ["Correlation / Crowding"],
    "position_sizing": ["Capital Budget"],
}

CAPITAL_ALLOCATION_SECTION_MAP = {
    "final_recommendation": ["Rating"],
    "position_sizing": ["Position Size"],
    "entry_framework": ["Entry / Exit"],
    "kill_criteria": ["Kill Criteria"],
    "monitoring_triggers": ["Monitoring Triggers"],
    "capital_allocation_rationale": ["Capital Allocation Rationale"],
}


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
