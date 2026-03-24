from typing import Any, Dict, Iterable, List

from langchain_core.messages import HumanMessage, RemoveMessage

# Import tools from separate utility files
from tradingagents.agents.utils.core_stock_tools import (
    get_stock_data
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_indicators
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement
)
from tradingagents.agents.utils.news_data_tools import (
    get_news,
    get_insider_transactions,
    get_global_news
)


ANALYST_CAPABILITIES = {
    "market_expectations": {
        "display_name": "Market Expectations",
        "report_field": "market_expectations_report",
        "summary": "Infer what the market already expects from price action, momentum, volatility, and positioning so the fund knows what is priced in.",
    },
    "why_now": {
        "display_name": "Why Now",
        "report_field": "why_now_report",
        "summary": "Explain why the idea matters right now by tracking attention, sentiment acceleration, and whether narrative momentum is strengthening or fading.",
    },
    "catalyst_path": {
        "display_name": "Catalyst Path",
        "report_field": "catalyst_path_report",
        "summary": "Map the catalyst path through company-specific and macro events, showing what can force a re-rating and on what timeline.",
    },
    "business_truth": {
        "display_name": "Business Truth",
        "report_field": "business_truth_report",
        "summary": "Establish the business truth: earnings power, unit economics, resilience, balance-sheet strength, and the underlying reality of the company.",
    },
}

ANALYST_ORDER = list(ANALYST_CAPABILITIES.keys())

ANALYST_DISPLAY_NAMES = {
    key: config["display_name"] for key, config in ANALYST_CAPABILITIES.items()
}

ANALYST_REPORT_FIELDS = {
    key: config["report_field"] for key, config in ANALYST_CAPABILITIES.items()
}

ANALYST_REPORT_FIELD_TO_KEY = {
    report_field: key for key, report_field in ANALYST_REPORT_FIELDS.items()
}

ANALYST_SELECTION_LABELS = ANALYST_DISPLAY_NAMES.copy()

ANALYST_REPORT_TITLES = ANALYST_DISPLAY_NAMES.copy()

ANALYST_CAPABILITY_SUMMARIES = {
    key: config["summary"] for key, config in ANALYST_CAPABILITIES.items()
}

THESIS_ENGINE = "Thesis Engine"
CHALLENGE_ENGINE = "Challenge Engine"
INVESTMENT_DIRECTOR = "Investment Director"
EXECUTION_ENGINE = "Execution Engine"
UPSIDE_CAPTURE_ENGINE = "Upside Capture Engine"
DOWNSIDE_GUARDRAIL_ENGINE = "Downside Guardrail Engine"
PORTFOLIO_FIT_ENGINE = "Portfolio Fit Engine"
CAPITAL_ALLOCATION_COMMITTEE = "Capital Allocation Committee"

INSTITUTIONAL_ROLE_NAMES = {
    "bull": THESIS_ENGINE,
    "bear": CHALLENGE_ENGINE,
    "manager": INVESTMENT_DIRECTOR,
    "trader": EXECUTION_ENGINE,
    "aggressive": UPSIDE_CAPTURE_ENGINE,
    "conservative": DOWNSIDE_GUARDRAIL_ENGINE,
    "neutral": PORTFOLIO_FIT_ENGINE,
    "portfolio_manager": CAPITAL_ALLOCATION_COMMITTEE,
}

RESEARCH_TEAM_NAMES = [
    THESIS_ENGINE,
    CHALLENGE_ENGINE,
    INVESTMENT_DIRECTOR,
]

RISK_TEAM_NAMES = [
    UPSIDE_CAPTURE_ENGINE,
    PORTFOLIO_FIT_ENGINE,
    DOWNSIDE_GUARDRAIL_ENGINE,
]


def build_instrument_context(ticker: str) -> str:
    """Describe the exact instrument so agents preserve exchange-qualified tickers."""
    return (
        f"The instrument to analyze is `{ticker}`. "
        "Use this exact ticker in every tool call, report, and recommendation, "
        "preserving any exchange suffix (e.g. `.TO`, `.L`, `.HK`, `.T`)."
    )

def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]

        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")

        return {"messages": removal_operations + [placeholder]}

    return delete_messages


def normalize_selected_analysts(selected_analysts: Iterable[str] | None) -> List[str]:
    """Return valid analyst keys in canonical order without duplicates."""
    requested = set()
    for analyst_key in selected_analysts or []:
        if analyst_key in ANALYST_ORDER:
            requested.add(analyst_key)
    return [analyst_key for analyst_key in ANALYST_ORDER if analyst_key in requested]


def get_analyst_node_name(analyst_key: str) -> str:
    """Return the graph node name for an analyst capability."""
    return ANALYST_DISPLAY_NAMES[analyst_key]


def get_report_field_for_analyst(analyst_key: str) -> str:
    """Return the state field that stores a capability report."""
    return ANALYST_REPORT_FIELDS[analyst_key]


def get_analyst_report_title(analyst_key: str) -> str:
    """Return the user-facing title for an analyst capability report."""
    return ANALYST_REPORT_TITLES[analyst_key]


def get_analyst_tool_node_name(analyst_key: str) -> str:
    """Return the graph tool node name for a capability."""
    return f"tools_{analyst_key}"


def get_analyst_clear_node_name(analyst_key: str) -> str:
    """Return the graph cleanup node name for a capability."""
    return f"Msg Clear {analyst_key}"


def get_capability_catalog(selected_analysts: Iterable[str] | None) -> str:
    """Render the available capability modules for planning prompts."""
    keys = normalize_selected_analysts(selected_analysts)
    return "\n".join(
        f"- {key} ({ANALYST_DISPLAY_NAMES[key]}): {ANALYST_CAPABILITY_SUMMARIES[key]}"
        for key in keys
    )


def get_analyst_report(state: Dict[str, Any], analyst_key: str) -> str:
    """Fetch a capability report from the shared artifact store or state."""
    artifacts = state.get("analysis_artifacts") or {}
    artifact = artifacts.get(analyst_key)
    if isinstance(artifact, dict):
        report = artifact.get("report", "")
        if report:
            return report
    elif isinstance(artifact, str) and artifact:
        return artifact

    return state.get(get_report_field_for_analyst(analyst_key), "")


def collect_analyst_reports(
    state: Dict[str, Any], analyst_keys: Iterable[str] | None = None
) -> Dict[str, str]:
    """Collect non-empty analyst reports keyed by analyst id."""
    reports = {}
    for analyst_key in normalize_selected_analysts(analyst_keys or ANALYST_ORDER):
        report = get_analyst_report(state, analyst_key)
        if report:
            reports[analyst_key] = report
    return reports


def build_research_context(
    state: Dict[str, Any], analyst_keys: Iterable[str] | None = None
) -> str:
    """Build a shared cross-analyst context block for downstream agents."""
    reports = collect_analyst_reports(state, analyst_keys)
    sections = []
    for analyst_key in normalize_selected_analysts(analyst_keys or ANALYST_ORDER):
        report = reports.get(analyst_key)
        if report:
            sections.append(f"{ANALYST_DISPLAY_NAMES[analyst_key]} Report: {report}")
    return "\n\n".join(sections)


        
