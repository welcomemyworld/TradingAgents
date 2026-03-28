from typing import Optional
import datetime as dt
import typer
from pathlib import Path
from functools import wraps
from rich.console import Console
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich.columns import Columns
from rich.markdown import Markdown
from rich.layout import Layout
from rich.text import Text
from rich.table import Table
from collections import deque
import time
from rich.tree import Tree
from rich import box
from rich.align import Align
from rich.rule import Rule

from tradingagents.graph.trading_graph import FutureInvestGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.agent_utils import (
    ANALYST_DISPLAY_NAMES,
    ANALYST_ORDER,
    ANALYST_REPORT_FIELDS,
    ANALYST_REPORT_TITLES,
    CAPITAL_ALLOCATION_COMMITTEE,
    CHALLENGE_ENGINE,
    DOWNSIDE_GUARDRAIL_ENGINE,
    EXECUTION_ENGINE,
    INVESTMENT_DIRECTOR,
    PORTFOLIO_FIT_ENGINE,
    RESEARCH_TEAM_NAMES,
    THESIS_ENGINE,
    UPSIDE_CAPTURE_ENGINE,
    get_analyst_report,
    normalize_selected_analysts,
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
from cli.models import AnalystType
from cli.utils import *
from cli.stats_handler import StatsCallbackHandler

console = Console()

BRAND_NAME = "Future Invest"
BRAND_MARK = "X"
BRAND_TAGLINE = "AI-Native Investment Institution"
BRAND_STYLELINE = "Cyberpunk Capital Interface"
BRAND_REPORT_TITLE = "Future Invest Dossier"

app = typer.Typer(
    name="future-invest",
    help="Future Invest CLI: AI-Native Investment Institution Framework",
    add_completion=True,  # Enable shell completion
)

ANALYST_REPORT_SECTIONS = {
    ANALYST_REPORT_FIELDS[analyst_key]: (analyst_key, ANALYST_DISPLAY_NAMES[analyst_key])
    for analyst_key in ANALYST_ORDER
}

ANALYST_SECTION_TITLES = {
    ANALYST_REPORT_FIELDS[analyst_key]: ANALYST_REPORT_TITLES[analyst_key]
    for analyst_key in ANALYST_ORDER
}


def format_provider_setting(selections: dict) -> str | None:
    if selections.get("openai_reasoning_effort"):
        return f"OpenAI reasoning: {selections['openai_reasoning_effort']}"
    if selections.get("google_thinking_level"):
        return f"Gemini thinking: {selections['google_thinking_level']}"
    if selections.get("anthropic_effort"):
        return f"Claude effort: {selections['anthropic_effort']}"
    return None


def format_position_importance(selections: dict) -> str:
    return selections.get("position_importance_label") or POSITION_IMPORTANCE_LABELS.get(
        selections.get("position_importance", ""),
        str(selections.get("position_importance", "")).title(),
    )


def format_token_budget(selections: dict) -> str:
    return selections.get("token_budget_label") or TOKEN_BUDGET_LABELS.get(
        selections.get("token_budget", ""),
        str(selections.get("token_budget", "")).title(),
    )


def create_launch_brief_panel(selections: dict) -> Panel:
    summary = Table.grid(expand=True)
    summary.add_column(style="bold cyan", ratio=1)
    summary.add_column(style="white", ratio=3)
    summary.add_row("Instrument", selections["ticker"])
    summary.add_row("Market Date", selections["analysis_date"])
    summary.add_row(
        "Run Mode",
        f"{selections['run_mode_label']} - {selections['run_mode_summary']}",
    )
    summary.add_row("Position Importance", format_position_importance(selections))
    summary.add_row("Token Budget", format_token_budget(selections))
    summary.add_row(
        "Signal Stack",
        ", ".join(
            ANALYST_DISPLAY_NAMES[analyst.value] for analyst in selections["analysts"]
        ),
    )
    summary.add_row(
        "Review Intensity",
        f"{selections['research_depth_label']} ({selections['research_depth']} cycles)",
    )
    summary.add_row("Model Backend", selections["llm_provider"].title())
    summary.add_row(
        "Model Pairing",
        f"Scanning: {selections['shallow_thinker']} | Judgment: {selections['deep_thinker']}",
    )
    provider_setting = format_provider_setting(selections)
    if provider_setting:
        summary.add_row("Provider Setting", provider_setting)

    return Panel(
        summary,
        title="Launch Brief",
        subtitle="Mission Control Checkpoint",
        border_style="cyan",
        padding=(1, 2),
    )


def _clean_text(value) -> str:
    return str(value).strip() if value else ""


def _join_agent_entries(entries):
    return "\n\n".join(
        f"### {title}\n{content}"
        for title, content in entries
        if _clean_text(content)
    )


def get_thesis_review_entries(state: dict) -> list[tuple[str, str]]:
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


def get_execution_state_entries(state: dict) -> list[tuple[str, str]]:
    execution_state = state.get("execution_state") or {}
    content = _clean_text(execution_state.get("full_blueprint")) or _clean_text(
        state.get("trader_investment_plan")
    )
    return [(EXECUTION_ENGINE, content)]


def get_allocation_review_entries(state: dict) -> list[tuple[str, str]]:
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


def get_final_decision_entries(state: dict) -> list[tuple[str, str]]:
    final_decision = state.get("final_decision") or {}
    content = _clean_text(final_decision.get("full_decision")) or _clean_text(
        state.get("final_trade_decision")
    )
    return [(CAPITAL_ALLOCATION_COMMITTEE, content)]


def get_portfolio_mandate_content(state: dict) -> str:
    portfolio_context = state.get("portfolio_context") or {}
    content = _clean_text(portfolio_context.get("full_context"))
    if content:
        return content
    return _clean_text(render_portfolio_context(portfolio_context))


def get_time_horizon_split_content(state: dict) -> str:
    temporal_context = state.get("temporal_context") or {}
    content = _clean_text(temporal_context.get("full_context"))
    if content:
        return content
    return _clean_text(render_temporal_context(temporal_context))


def get_institutional_memory_content(state: dict) -> str:
    return _clean_text(state.get("institution_memory_brief"))


def build_report_sections_map(state: dict) -> dict[str, str]:
    sections = {}

    if _clean_text(state.get("analysis_plan")):
        sections["analysis_plan"] = _clean_text(state["analysis_plan"])

    portfolio_mandate = get_portfolio_mandate_content(state)
    if portfolio_mandate:
        sections["portfolio_context"] = portfolio_mandate

    time_horizon_split = get_time_horizon_split_content(state)
    if time_horizon_split:
        sections["temporal_context"] = time_horizon_split

    institutional_memory = get_institutional_memory_content(state)
    if institutional_memory:
        sections["institution_memory_brief"] = institutional_memory

    for analyst_key in ANALYST_ORDER:
        report_field = ANALYST_REPORT_FIELDS[analyst_key]
        report = _clean_text(get_analyst_report(state, analyst_key))
        if report:
            sections[report_field] = report

    thesis_review = _join_agent_entries(get_thesis_review_entries(state))
    if thesis_review:
        sections["thesis_review"] = thesis_review

    execution_state = _join_agent_entries(get_execution_state_entries(state))
    if execution_state:
        sections["execution_state"] = execution_state

    allocation_review = _join_agent_entries(get_allocation_review_entries(state))
    if allocation_review:
        sections["allocation_review"] = allocation_review

    final_decision = _join_agent_entries(get_final_decision_entries(state))
    if final_decision:
        sections["final_decision"] = final_decision

    if _clean_text(state.get("decision_dossier_markdown")):
        sections["decision_dossier_markdown"] = _clean_text(
            state["decision_dossier_markdown"]
        )

    return sections


def sync_report_sections_from_state(buffer, state: dict):
    for section_name, content in build_report_sections_map(state).items():
        buffer.update_report_section(section_name, content)


# Create a deque to store recent messages with a maximum length
class MessageBuffer:
    # Fixed teams that always run (not user-selectable)
    FIXED_AGENTS = {
        "Investment Orchestration": ["Investment Orchestrator"],
        "Decision Core": [THESIS_ENGINE, CHALLENGE_ENGINE, INVESTMENT_DIRECTOR],
        "Execution Stack": [EXECUTION_ENGINE],
        "Capital Engines": [
            UPSIDE_CAPTURE_ENGINE,
            PORTFOLIO_FIT_ENGINE,
            DOWNSIDE_GUARDRAIL_ENGINE,
        ],
        "Allocator": [CAPITAL_ALLOCATION_COMMITTEE],
    }

    # Capability name mapping
    ANALYST_MAPPING = {
        analyst_key: ANALYST_DISPLAY_NAMES[analyst_key] for analyst_key in ANALYST_ORDER
    }

    # Report section mapping: section -> (capability_key for filtering, finalizing_agent)
    # capability_key: which capability selection controls this section (None = always included)
    # finalizing_agent: which agent must be "completed" for this report to count as done
    REPORT_SECTIONS = {
        "analysis_plan": (None, "Investment Orchestrator"),
        "portfolio_context": (None, "Investment Orchestrator"),
        "temporal_context": (None, "Investment Orchestrator"),
        "institution_memory_brief": (None, "Investment Orchestrator"),
        **ANALYST_REPORT_SECTIONS,
        "thesis_review": (None, INVESTMENT_DIRECTOR),
        "execution_state": (None, EXECUTION_ENGINE),
        "allocation_review": (None, CAPITAL_ALLOCATION_COMMITTEE),
        "final_decision": (None, CAPITAL_ALLOCATION_COMMITTEE),
        "decision_dossier_markdown": (None, CAPITAL_ALLOCATION_COMMITTEE),
    }

    def __init__(self, max_length=100):
        self.messages = deque(maxlen=max_length)
        self.tool_calls = deque(maxlen=max_length)
        self.current_report = None
        self.final_report = None  # Store the complete final report
        self.agent_status = {}
        self.current_agent = None
        self.report_sections = {}
        self.selected_analysts = []
        self._last_message_id = None

    def init_for_analysis(self, selected_analysts):
        """Initialize agent status and report sections based on selected capabilities.

        Args:
            selected_analysts: List of capability ids (e.g., ["market_expectations", "timing_catalyst"])
        """
        self.selected_analysts = [a.lower() for a in selected_analysts]

        # Build agent_status dynamically
        self.agent_status = {}

        # Add selected capabilities
        for analyst_key in self.selected_analysts:
            if analyst_key in self.ANALYST_MAPPING:
                self.agent_status[self.ANALYST_MAPPING[analyst_key]] = "pending"

        # Add fixed teams
        for team_agents in self.FIXED_AGENTS.values():
            for agent in team_agents:
                self.agent_status[agent] = "pending"

        # Build report_sections dynamically
        self.report_sections = {}
        for section, (analyst_key, _) in self.REPORT_SECTIONS.items():
            if analyst_key is None or analyst_key in self.selected_analysts:
                self.report_sections[section] = None

        # Reset other state
        self.current_report = None
        self.final_report = None
        self.current_agent = None
        self.messages.clear()
        self.tool_calls.clear()
        self._last_message_id = None

    def ensure_selected_analysts(self, selected_analysts):
        normalized = [a.lower() for a in selected_analysts]
        if normalized == self.selected_analysts:
            return

        for analyst_key in normalized:
            if analyst_key not in self.selected_analysts and analyst_key in self.ANALYST_MAPPING:
                self.agent_status[self.ANALYST_MAPPING[analyst_key]] = "pending"
                report_field = ANALYST_REPORT_FIELDS[analyst_key]
                if report_field not in self.report_sections:
                    self.report_sections[report_field] = None

        self.selected_analysts = normalized

    def get_completed_reports_count(self):
        """Count reports that are finalized (their finalizing agent is completed).

        A report is considered complete when:
        1. The report section has content (not None), AND
        2. The agent responsible for finalizing that report has status "completed"

        This prevents interim updates (like debate rounds) from counting as completed.
        """
        count = 0
        for section in self.report_sections:
            if section not in self.REPORT_SECTIONS:
                continue
            _, finalizing_agent = self.REPORT_SECTIONS[section]
            # Report is complete if it has content AND its finalizing agent is done
            has_content = self.report_sections.get(section) is not None
            agent_done = self.agent_status.get(finalizing_agent) == "completed"
            if has_content and agent_done:
                count += 1
        return count

    def add_message(self, message_type, content):
        timestamp = dt.datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, message_type, content))

    def add_tool_call(self, tool_name, args):
        timestamp = dt.datetime.now().strftime("%H:%M:%S")
        self.tool_calls.append((timestamp, tool_name, args))

    def update_agent_status(self, agent, status):
        if agent in self.agent_status:
            self.agent_status[agent] = status
            self.current_agent = agent

    def update_report_section(self, section_name, content):
        if section_name in self.report_sections:
            self.report_sections[section_name] = content
            self._update_current_report()

    def _update_current_report(self):
        # For the panel display, only show the most recently updated section
        latest_section = None
        latest_content = None

        # Find the most recently updated section
        for section, content in self.report_sections.items():
            if content is not None:
                latest_section = section
                latest_content = content
               
        if latest_section and latest_content:
            # Format the current section for display
            section_titles = {
                "analysis_plan": "Investment Orchestration",
                "portfolio_context": "Portfolio Mandate",
                "temporal_context": "Time Horizon Split",
                "institution_memory_brief": "Institutional Memory",
                **ANALYST_SECTION_TITLES,
                "thesis_review": "Thesis Review",
                "execution_state": "Execution State",
                "allocation_review": "Allocation Review",
                "final_decision": "Final Decision",
                "decision_dossier_markdown": BRAND_REPORT_TITLE,
            }
            self.current_report = (
                f"### {section_titles[latest_section]}\n{latest_content}"
            )

        # Update the final complete report
        self._update_final_report()

    def _update_final_report(self):
        report_parts = []

        if self.report_sections.get("analysis_plan"):
            report_parts.append("## Investment Orchestration")
            report_parts.append(f"{self.report_sections['analysis_plan']}")

        if self.report_sections.get("portfolio_context"):
            report_parts.append("## Portfolio Mandate")
            report_parts.append(f"{self.report_sections['portfolio_context']}")

        if self.report_sections.get("temporal_context"):
            report_parts.append("## Time Horizon Split")
            report_parts.append(f"{self.report_sections['temporal_context']}")

        if self.report_sections.get("institution_memory_brief"):
            report_parts.append("## Institutional Memory")
            report_parts.append(f"{self.report_sections['institution_memory_brief']}")

        analyst_sections = [
            ANALYST_REPORT_FIELDS[analyst_key] for analyst_key in ANALYST_ORDER
        ]
        if any(self.report_sections.get(section) for section in analyst_sections):
            report_parts.append("## Research Capability Reports")
            for analyst_key in ANALYST_ORDER:
                report_field = ANALYST_REPORT_FIELDS[analyst_key]
                report = self.report_sections.get(report_field)
                if report:
                    report_parts.append(
                        f"### {ANALYST_REPORT_TITLES[analyst_key]}\n{report}"
                    )

        if self.report_sections.get("thesis_review"):
            report_parts.append("## Thesis Review")
            report_parts.append(f"{self.report_sections['thesis_review']}")

        if self.report_sections.get("execution_state"):
            report_parts.append("## Execution State")
            report_parts.append(f"{self.report_sections['execution_state']}")

        if self.report_sections.get("allocation_review"):
            report_parts.append("## Allocation Review")
            report_parts.append(f"{self.report_sections['allocation_review']}")

        if self.report_sections.get("final_decision"):
            report_parts.append("## Final Decision")
            report_parts.append(f"{self.report_sections['final_decision']}")

        if self.report_sections.get("decision_dossier_markdown"):
            report_parts.append(f"## {BRAND_REPORT_TITLE}")
            report_parts.append(f"{self.report_sections['decision_dossier_markdown']}")

        self.final_report = "\n\n".join(report_parts) if report_parts else None


message_buffer = MessageBuffer()


def create_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=8),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_column(
        Layout(name="upper", ratio=3), Layout(name="analysis", ratio=5)
    )
    layout["upper"].split_row(
        Layout(name="progress", ratio=2), Layout(name="messages", ratio=3)
    )
    return layout


def format_tokens(n):
    """Format token count for display."""
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


def update_display(
    layout,
    spinner_text=None,
    stats_handler=None,
    start_time=None,
    session_context=None,
):
    # Header with welcome message
    header_lines = [
        f"[bold bright_magenta]{BRAND_NAME}[/bold bright_magenta] [bold cyan]{BRAND_MARK}[/bold cyan]",
        f"[bold cyan]{BRAND_STYLELINE}[/bold cyan]",
        f"[dim]{BRAND_TAGLINE}[/dim]",
    ]
    if session_context:
        header_lines.append(
            f"[white]{session_context['ticker']}[/white] • {session_context['analysis_date']} • {session_context['run_mode_label']}"
        )
        header_lines.append(
            "[dim]"
            f"Importance: {format_position_importance(session_context)} | "
            f"Budget: {format_token_budget(session_context)}"
            "[/dim]"
        )
        header_lines.append(
            "[dim]"
            f"Backend: {session_context['llm_provider'].title()} | "
            f"Scanning: {session_context['shallow_thinker']} | "
            f"Judgment: {session_context['deep_thinker']}"
            "[/dim]"
        )
    if spinner_text:
        header_lines.append(f"[bold blue]Mission:[/bold blue] {spinner_text}")

    layout["header"].update(
        Panel(
            "\n".join(header_lines),
            title="Neon Command Center",
            border_style="cyan",
            padding=(1, 2),
            expand=True,
        )
    )

    # Progress panel showing agent status
    progress_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        box=box.SIMPLE_HEAD,  # Use simple header with horizontal lines
        title=None,  # Remove the redundant Progress title
        padding=(0, 2),  # Add horizontal padding
        expand=True,  # Make table expand to fill available space
    )
    progress_table.add_column("Team", style="cyan", justify="center", width=20)
    progress_table.add_column("Engine", style="green", justify="center", width=20)
    progress_table.add_column("Status", style="yellow", justify="center", width=20)

    # Group agents by team - filter to only include agents in agent_status
    all_teams = {
        "Investment Orchestration": ["Investment Orchestrator"],
        "Signal Stack": [
            ANALYST_DISPLAY_NAMES[analyst_key] for analyst_key in ANALYST_ORDER
        ],
        "Decision Core": [THESIS_ENGINE, CHALLENGE_ENGINE, INVESTMENT_DIRECTOR],
        "Execution Stack": [EXECUTION_ENGINE],
        "Capital Engines": [
            UPSIDE_CAPTURE_ENGINE,
            PORTFOLIO_FIT_ENGINE,
            DOWNSIDE_GUARDRAIL_ENGINE,
        ],
        "Allocator": [CAPITAL_ALLOCATION_COMMITTEE],
    }

    # Filter teams to only include agents that are in agent_status
    teams = {}
    for team, agents in all_teams.items():
        active_agents = [a for a in agents if a in message_buffer.agent_status]
        if active_agents:
            teams[team] = active_agents

    for team, agents in teams.items():
        # Add first agent with team name
        first_agent = agents[0]
        status = message_buffer.agent_status.get(first_agent, "pending")
        if status == "in_progress":
            spinner = Spinner(
                "dots", text="[blue]in_progress[/blue]", style="bold cyan"
            )
            status_cell = spinner
        else:
            status_color = {
                "pending": "yellow",
                "completed": "green",
                "error": "red",
            }.get(status, "white")
            status_cell = f"[{status_color}]{status}[/{status_color}]"
        progress_table.add_row(team, first_agent, status_cell)

        # Add remaining agents in team
        for agent in agents[1:]:
            status = message_buffer.agent_status.get(agent, "pending")
            if status == "in_progress":
                spinner = Spinner(
                    "dots", text="[blue]in_progress[/blue]", style="bold cyan"
                )
                status_cell = spinner
            else:
                status_color = {
                    "pending": "yellow",
                    "completed": "green",
                    "error": "red",
                }.get(status, "white")
                status_cell = f"[{status_color}]{status}[/{status_color}]"
            progress_table.add_row("", agent, status_cell)

        # Add horizontal line after each team
        progress_table.add_row("─" * 20, "─" * 20, "─" * 20, style="dim")

    layout["progress"].update(
        Panel(progress_table, title="Institution Map", border_style="cyan", padding=(1, 2))
    )

    # Messages panel showing recent messages and tool calls
    messages_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        expand=True,  # Make table expand to fill available space
        box=box.MINIMAL,  # Use minimal box style for a lighter look
        show_lines=True,  # Keep horizontal lines
        padding=(0, 1),  # Add some padding between columns
    )
    messages_table.add_column("Time", style="cyan", width=8, justify="center")
    messages_table.add_column("Type", style="green", width=10, justify="center")
    messages_table.add_column(
        "Content", style="white", no_wrap=False, ratio=1
    )  # Make content column expand

    # Combine tool calls and messages
    all_messages = []

    # Add tool calls
    for timestamp, tool_name, args in message_buffer.tool_calls:
        formatted_args = format_tool_args(args)
        all_messages.append((timestamp, "Tool", f"{tool_name}: {formatted_args}"))

    # Add regular messages
    for timestamp, msg_type, content in message_buffer.messages:
        content_str = str(content) if content else ""
        if len(content_str) > 200:
            content_str = content_str[:197] + "..."
        all_messages.append((timestamp, msg_type, content_str))

    # Sort by timestamp descending (newest first)
    all_messages.sort(key=lambda x: x[0], reverse=True)

    # Calculate how many messages we can show based on available space
    max_messages = 12

    # Get the first N messages (newest ones)
    recent_messages = all_messages[:max_messages]

    # Add messages to table (already in newest-first order)
    for timestamp, msg_type, content in recent_messages:
        # Format content with word wrapping
        wrapped_content = Text(content, overflow="fold")
        messages_table.add_row(timestamp, msg_type, wrapped_content)

    layout["messages"].update(
        Panel(
            messages_table,
            title="Signal Feed",
            border_style="blue",
            padding=(1, 2),
        )
    )

    # Analysis panel showing current report
    if message_buffer.current_report:
        layout["analysis"].update(
            Panel(
                Markdown(message_buffer.current_report),
                title="Live Dossier",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        layout["analysis"].update(
            Panel(
                "[italic]Mission is warming up. Waiting for the first institutional output...[/italic]",
                title="Live Dossier",
                border_style="green",
                padding=(1, 2),
            )
        )

    # Footer with statistics
    # Agent progress - derived from agent_status dict
    agents_completed = sum(
        1 for status in message_buffer.agent_status.values() if status == "completed"
    )
    agents_total = len(message_buffer.agent_status)

    # Report progress - based on agent completion (not just content existence)
    reports_completed = message_buffer.get_completed_reports_count()
    reports_total = len(message_buffer.report_sections)

    # Build stats parts
    stats_parts = [f"Agents: {agents_completed}/{agents_total}"]

    # LLM and tool stats from callback handler
    if stats_handler:
        stats = stats_handler.get_stats()
        stats_parts.append(f"LLM: {stats['llm_calls']}")
        stats_parts.append(f"Tools: {stats['tool_calls']}")

        # Token display with graceful fallback
        if stats["tokens_in"] > 0 or stats["tokens_out"] > 0:
            tokens_str = f"Tokens: {format_tokens(stats['tokens_in'])}\u2191 {format_tokens(stats['tokens_out'])}\u2193"
        else:
            tokens_str = "Tokens: --"
        stats_parts.append(tokens_str)

    stats_parts.append(f"Reports: {reports_completed}/{reports_total}")

    # Elapsed time
    if start_time:
        elapsed = time.time() - start_time
        elapsed_str = f"\u23f1 {int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
        stats_parts.append(elapsed_str)

    stats_table = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    stats_table.add_column("Stats", justify="center")
    stats_table.add_row(" | ".join(stats_parts))

    layout["footer"].update(
        Panel(stats_table, title="Mission Status", border_style="grey50")
    )


def get_user_selections():
    """Get all user selections before starting the analysis display."""
    # Display ASCII art welcome message
    with open(Path(__file__).parent / "static" / "welcome.txt", "r") as f:
        welcome_ascii = f.read()

    # Create welcome box content
    welcome_content = f"[bold bright_magenta]{welcome_ascii}[/bold bright_magenta]\n"
    welcome_content += f"[bold bright_magenta]{BRAND_NAME}[/bold bright_magenta] [bold cyan]{BRAND_MARK}[/bold cyan]\n"
    welcome_content += f"[bold cyan]{BRAND_STYLELINE}[/bold cyan]\n"
    welcome_content += f"[dim]{BRAND_TAGLINE}[/dim]\n\n"
    welcome_content += "[bold]Future Invest Workflow:[/bold]\n"
    welcome_content += "[bold cyan]Mandate Layer[/bold cyan]   Mission Setup → Portfolio Mandate → Time Horizon Split\n"
    welcome_content += "[bold bright_magenta]Memory Layer[/bold bright_magenta]    Institutional Memory → Signal Stack\n"
    welcome_content += "[bold yellow]Decision Layer[/bold yellow]  Thesis Review → Execution State → Allocation Review\n"
    welcome_content += "[bold green]Capital Layer[/bold green]   Final Decision → Run Dossier → Company Memory Update\n\n"

    # Create and center the welcome box
    welcome_box = Panel(
        welcome_content,
        border_style="bright_magenta",
        padding=(1, 2),
        title=f"Welcome to {BRAND_NAME} {BRAND_MARK}",
        subtitle=BRAND_STYLELINE,
    )
    console.print(Align.center(welcome_box))
    console.print()
    console.print()  # Add vertical space before announcements

    # Create a boxed questionnaire for each step
    def create_question_box(title, prompt, default=None):
        box_content = f"[bold]{title}[/bold]\n"
        box_content += f"[dim]{prompt}[/dim]"
        if default:
            box_content += f"\n[dim]Default: {default}[/dim]"
        return Panel(box_content, border_style="magenta", padding=(1, 2))

    # Step 1: Ticker symbol
    console.print(
        create_question_box(
            "Step 1: Instrument",
            "Choose the exact ticker symbol to analyze, including exchange suffix when needed (examples: SPY, CNC.TO, 7203.T, 0700.HK)",
            "SPY",
        )
    )
    selected_ticker = get_ticker(default="SPY")
    console.print(f"[green]Instrument armed:[/green] {selected_ticker}")

    # Step 2: Analysis date
    default_date = dt.datetime.now().strftime("%Y-%m-%d")
    console.print(
        create_question_box(
            "Step 2: Market Date",
            "Lock the information set date in YYYY-MM-DD format",
            default_date,
        )
    )
    analysis_date = get_analysis_date(default=default_date)
    console.print(f"[green]Market date locked:[/green] {analysis_date}")

    # Step 3: Run mode
    console.print(
        create_question_box(
            "Step 3: Run Mode",
            "Choose how Future Invest should approach this session",
        )
    )
    run_mode_key, run_mode_label, suggested_depth, run_mode_summary = select_run_mode()
    console.print(f"[green]Run mode:[/green] {run_mode_label}")

    run_mode_controls = RUN_MODE_CONTROL_PRESETS.get(run_mode_key, {})
    recommended_position_importance = run_mode_controls.get(
        "position_importance", "standard"
    )
    recommended_token_budget = run_mode_controls.get("token_budget", "balanced")

    # Step 4: Position importance
    console.print(
        create_question_box(
            "Step 4: Position Importance",
            f"Set how important this seat is to the institution. Suggested for {run_mode_label}: {POSITION_IMPORTANCE_LABELS[recommended_position_importance]}",
        )
    )
    selected_position_importance = select_position_importance(
        recommended_position_importance
    )
    position_importance_label = POSITION_IMPORTANCE_LABELS[selected_position_importance]
    console.print(
        f"[green]Position importance:[/green] {position_importance_label}"
    )

    # Step 5: Token budget
    console.print(
        create_question_box(
            "Step 5: Token Budget",
            f"Set the institution's research spend posture. Suggested for {run_mode_label}: {TOKEN_BUDGET_LABELS[recommended_token_budget]}",
        )
    )
    selected_token_budget = select_token_budget(recommended_token_budget)
    token_budget_label = TOKEN_BUDGET_LABELS[selected_token_budget]
    console.print(f"[green]Token budget:[/green] {token_budget_label}")

    # Step 6: Select research capabilities
    console.print(
        create_question_box(
            "Step 6: Signal Stack",
            "Choose which research capabilities should join the signal stack",
        )
    )
    selected_analysts = select_analysts()
    console.print(
        f"[green]Selected capabilities:[/green] {', '.join(ANALYST_DISPLAY_NAMES[analyst.value] for analyst in selected_analysts)}"
    )

    # Step 7: Research depth
    console.print(
        create_question_box(
            "Step 7: Review Intensity",
            f"Set how many institutional review cycles to run. Suggested for {run_mode_label}: {RESEARCH_DEPTH_LABELS[suggested_depth]}",
        )
    )
    selected_research_depth = select_research_depth(suggested_depth)
    research_depth_label = RESEARCH_DEPTH_LABELS.get(
        selected_research_depth, str(selected_research_depth)
    )
    console.print(
        f"[green]Review intensity:[/green] {research_depth_label} ({selected_research_depth} cycles)"
    )

    # Step 8: Model backend
    console.print(
        create_question_box(
            "Step 8: Model Backend",
            "Select which model provider powers the institution",
        )
    )
    selected_llm_provider, backend_url = select_llm_provider()
    
    # Step 9: Model pairing
    console.print(
        create_question_box(
            "Step 9: Model Pairing",
            "Select the scanning engine and judgment engine for the institution",
        )
    )
    selected_shallow_thinker = select_shallow_thinking_agent(selected_llm_provider)
    selected_deep_thinker = select_deep_thinking_agent(selected_llm_provider)

    # Step 8: Provider-specific thinking configuration
    thinking_level = None
    reasoning_effort = None
    anthropic_effort = None

    provider_lower = selected_llm_provider.lower()
    if provider_lower == "google":
        console.print(
            create_question_box(
                "Step 10: Thinking Mode",
                "Configure Gemini thinking mode"
            )
        )
        thinking_level = ask_gemini_thinking_config()
    elif provider_lower == "openai":
        console.print(
            create_question_box(
                "Step 10: Reasoning Effort",
                "Configure OpenAI reasoning effort level"
            )
        )
        reasoning_effort = ask_openai_reasoning_effort()
    elif provider_lower == "anthropic":
        console.print(
            create_question_box(
                "Step 10: Effort Level",
                "Configure Claude effort level"
            )
        )
        anthropic_effort = ask_anthropic_effort()

    selections = {
        "ticker": selected_ticker,
        "analysis_date": analysis_date,
        "run_mode": run_mode_key,
        "run_mode_label": run_mode_label,
        "run_mode_summary": run_mode_summary,
        "position_importance": selected_position_importance,
        "position_importance_label": position_importance_label,
        "token_budget": selected_token_budget,
        "token_budget_label": token_budget_label,
        "analysts": selected_analysts,
        "research_depth": selected_research_depth,
        "research_depth_label": research_depth_label,
        "llm_provider": selected_llm_provider.lower(),
        "backend_url": backend_url,
        "shallow_thinker": selected_shallow_thinker,
        "deep_thinker": selected_deep_thinker,
        "google_thinking_level": thinking_level,
        "openai_reasoning_effort": reasoning_effort,
        "anthropic_effort": anthropic_effort,
    }

    console.print()
    console.print(create_launch_brief_panel(selections))
    if not confirm_launch():
        console.print("\n[yellow]Session cancelled before launch.[/yellow]")
        raise typer.Exit()

    return selections


def save_report_to_disk(
    final_state, ticker: str, save_path: Path, session_context: Optional[dict] = None
):
    """Save the complete institution run to disk with organized subfolders."""
    save_path.mkdir(parents=True, exist_ok=True)
    sections = []

    # 1. Investment orchestration
    if final_state.get("analysis_plan"):
        orchestration_dir = save_path / "1_orchestration"
        orchestration_dir.mkdir(exist_ok=True)
        (orchestration_dir / "plan.md").write_text(final_state["analysis_plan"])
        sections.append(f"## I. Investment Orchestration\n\n{final_state['analysis_plan']}")

    portfolio_mandate = get_portfolio_mandate_content(final_state)
    if portfolio_mandate:
        orchestration_dir = save_path / "1_orchestration"
        orchestration_dir.mkdir(exist_ok=True)
        (orchestration_dir / "portfolio_mandate.md").write_text(portfolio_mandate)
        sections.append(f"## II. Portfolio Mandate\n\n{portfolio_mandate}")

    time_horizon_split = get_time_horizon_split_content(final_state)
    if time_horizon_split:
        orchestration_dir = save_path / "1_orchestration"
        orchestration_dir.mkdir(exist_ok=True)
        (orchestration_dir / "time_horizon_split.md").write_text(time_horizon_split)
        sections.append(f"## III. Time Horizon Split\n\n{time_horizon_split}")

    institutional_memory = get_institutional_memory_content(final_state)
    if institutional_memory:
        orchestration_dir = save_path / "1_orchestration"
        orchestration_dir.mkdir(exist_ok=True)
        (orchestration_dir / "institutional_memory.md").write_text(institutional_memory)
        sections.append(f"## IV. Institutional Memory\n\n{institutional_memory}")

    # 2. Research capabilities
    analysts_dir = save_path / "2_capabilities"
    analyst_parts = []
    for analyst_key in ANALYST_ORDER:
        report_field = ANALYST_REPORT_FIELDS[analyst_key]
        report = final_state.get(report_field)
        if report:
            analysts_dir.mkdir(exist_ok=True)
            (analysts_dir / f"{analyst_key}.md").write_text(report)
            analyst_parts.append((ANALYST_REPORT_TITLES[analyst_key], report))
    if analyst_parts:
        analyst_content = "\n\n".join(
            f"### {name}\n{text}" for name, text in analyst_parts
        )
        sections.append(f"## V. Research Capability Reports\n\n{analyst_content}")

    # 3. Thesis review
    thesis_entries = [
        (title, content)
        for title, content in get_thesis_review_entries(final_state)
        if _clean_text(content)
    ]
    if thesis_entries:
        research_dir = save_path / "3_research"
        research_dir.mkdir(exist_ok=True)
        for title, content in thesis_entries:
            file_name = {
                THESIS_ENGINE: "thesis_engine.md",
                CHALLENGE_ENGINE: "challenge_engine.md",
                INVESTMENT_DIRECTOR: "investment_director.md",
            }[title]
            (research_dir / file_name).write_text(content)
        thesis_review_markdown = _join_agent_entries(thesis_entries)
        (research_dir / "thesis_review.md").write_text(thesis_review_markdown)
        sections.append(f"## VI. Thesis Review\n\n{thesis_review_markdown}")

    # 4. Execution state
    execution_entries = [
        (title, content)
        for title, content in get_execution_state_entries(final_state)
        if _clean_text(content)
    ]
    if execution_entries:
        trading_dir = save_path / "4_trading"
        trading_dir.mkdir(exist_ok=True)
        execution_markdown = _join_agent_entries(execution_entries)
        (trading_dir / "execution_state.md").write_text(execution_markdown)
        sections.append(f"## VII. Execution State\n\n{execution_markdown}")

    # 5. Allocation review
    allocation_entries = [
        (title, content)
        for title, content in get_allocation_review_entries(final_state)
        if _clean_text(content)
    ]
    if allocation_entries:
        risk_dir = save_path / "5_risk"
        risk_dir.mkdir(exist_ok=True)
        for title, content in allocation_entries:
            file_name = {
                UPSIDE_CAPTURE_ENGINE: "upside_capture.md",
                DOWNSIDE_GUARDRAIL_ENGINE: "downside_guardrail.md",
                PORTFOLIO_FIT_ENGINE: "portfolio_fit.md",
            }[title]
            (risk_dir / file_name).write_text(content)
        allocation_markdown = _join_agent_entries(allocation_entries)
        (risk_dir / "allocation_review.md").write_text(allocation_markdown)
        sections.append(f"## VIII. Allocation Review\n\n{allocation_markdown}")

    # 6. Final decision
    final_decision_entries = [
        (title, content)
        for title, content in get_final_decision_entries(final_state)
        if _clean_text(content)
    ]
    if final_decision_entries:
        portfolio_dir = save_path / "6_portfolio"
        portfolio_dir.mkdir(exist_ok=True)
        final_decision_markdown = _join_agent_entries(final_decision_entries)
        (portfolio_dir / "final_decision.md").write_text(final_decision_markdown)
        sections.append(f"## IX. Final Decision\n\n{final_decision_markdown}")

    if final_state.get("decision_dossier_markdown"):
        dossier_dir = save_path / "7_dossier"
        dossier_dir.mkdir(exist_ok=True)
        (dossier_dir / "dossier.md").write_text(final_state["decision_dossier_markdown"])
        sections.append(f"## X. {BRAND_REPORT_TITLE}\n\n{final_state['decision_dossier_markdown']}")

    # Write consolidated report
    header_lines = [
        f"# {BRAND_NAME} Institution Report: {ticker}",
        f"Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    if session_context:
        header_lines.append(f"Market Date: {session_context['analysis_date']}")
        header_lines.append(f"Run Mode: {session_context['run_mode_label']}")
        header_lines.append(
            f"Position Importance: {format_position_importance(session_context)}"
        )
        header_lines.append(f"Token Budget: {format_token_budget(session_context)}")
        header_lines.append(f"Model Backend: {session_context['llm_provider'].title()}")
    header = "\n\n".join(header_lines) + "\n\n"
    (save_path / "complete_report.md").write_text(header + "\n\n".join(sections))
    return save_path / "complete_report.md"


def display_complete_report(final_state):
    """Display the complete institution report sequentially (avoids truncation)."""
    console.print()
    console.print(Rule(f"{BRAND_NAME} Institution Report", style="bold cyan"))

    if final_state.get("analysis_plan"):
        console.print(Panel("[bold]I. Investment Orchestration[/bold]", border_style="green"))
        console.print(
            Panel(
                Markdown(final_state["analysis_plan"]),
                title="Investment Orchestrator",
                border_style="blue",
                padding=(1, 2),
            )
        )

    portfolio_mandate = get_portfolio_mandate_content(final_state)
    if portfolio_mandate:
        console.print(Panel("[bold]II. Portfolio Mandate[/bold]", border_style="cyan"))
        console.print(
            Panel(
                Markdown(portfolio_mandate),
                title="Portfolio Mandate",
                border_style="blue",
                padding=(1, 2),
            )
        )

    time_horizon_split = get_time_horizon_split_content(final_state)
    if time_horizon_split:
        console.print(Panel("[bold]III. Time Horizon Split[/bold]", border_style="cyan"))
        console.print(
            Panel(
                Markdown(time_horizon_split),
                title="Time Horizon Split",
                border_style="blue",
                padding=(1, 2),
            )
        )

    institutional_memory = get_institutional_memory_content(final_state)
    if institutional_memory:
        console.print(Panel("[bold]IV. Institutional Memory[/bold]", border_style="cyan"))
        console.print(
            Panel(
                Markdown(institutional_memory),
                title="Institutional Memory",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # V. Research Capability Reports
    analysts = []
    for analyst_key in ANALYST_ORDER:
        report_field = ANALYST_REPORT_FIELDS[analyst_key]
        report = final_state.get(report_field)
        if report:
            analysts.append((ANALYST_REPORT_TITLES[analyst_key], report))
    if analysts:
        console.print(Panel("[bold]V. Research Capability Reports[/bold]", border_style="cyan"))
        for title, content in analysts:
            console.print(Panel(Markdown(content), title=title, border_style="blue", padding=(1, 2)))

    thesis_entries = [
        (title, content) for title, content in get_thesis_review_entries(final_state) if _clean_text(content)
    ]
    if thesis_entries:
        console.print(Panel("[bold]VI. Thesis Review[/bold]", border_style="magenta"))
        for title, content in thesis_entries:
            console.print(Panel(Markdown(content), title=title, border_style="blue", padding=(1, 2)))

    execution_entries = [
        (title, content) for title, content in get_execution_state_entries(final_state) if _clean_text(content)
    ]
    if execution_entries:
        console.print(Panel("[bold]VII. Execution State[/bold]", border_style="yellow"))
        for title, content in execution_entries:
            console.print(Panel(Markdown(content), title=title, border_style="blue", padding=(1, 2)))

    allocation_entries = [
        (title, content) for title, content in get_allocation_review_entries(final_state) if _clean_text(content)
    ]
    if allocation_entries:
        console.print(Panel("[bold]VIII. Allocation Review[/bold]", border_style="red"))
        for title, content in allocation_entries:
            console.print(Panel(Markdown(content), title=title, border_style="blue", padding=(1, 2)))

    final_decision_entries = [
        (title, content) for title, content in get_final_decision_entries(final_state) if _clean_text(content)
    ]
    if final_decision_entries:
        console.print(Panel("[bold]IX. Final Decision[/bold]", border_style="green"))
        for title, content in final_decision_entries:
            console.print(Panel(Markdown(content), title=title, border_style="blue", padding=(1, 2)))

    if final_state.get("decision_dossier_markdown"):
        console.print(Panel(f"[bold]X. {BRAND_REPORT_TITLE}[/bold]", border_style="cyan"))
        console.print(
            Panel(
                Markdown(final_state["decision_dossier_markdown"]),
                title=BRAND_REPORT_TITLE,
                border_style="blue",
                padding=(1, 2),
            )
        )


def update_research_team_status(status):
    """Update status for the institutional debate stack."""
    research_team = RESEARCH_TEAM_NAMES
    for agent in research_team:
        message_buffer.update_agent_status(agent, status)


# Ordered list of capabilities for status transitions
ANALYST_AGENT_NAMES = ANALYST_DISPLAY_NAMES
ANALYST_REPORT_MAP = ANALYST_REPORT_FIELDS


def update_analyst_statuses(message_buffer, chunk):
    """Update capability statuses based on accumulated report state.

    Logic:
    - Store new report content from the current chunk if present
    - Check accumulated report_sections (not just current chunk) for status
    - Capabilities with reports = completed
    - First capability without report = in_progress
    - Remaining capabilities without reports = pending
    - When all capabilities finish, hand off to the institutional debate stack
    """
    chunk_selected = normalize_selected_analysts(
        chunk.get("selected_analysts", message_buffer.selected_analysts)
    )
    message_buffer.ensure_selected_analysts(chunk_selected)
    selected = message_buffer.selected_analysts
    active_key = chunk.get("current_analyst")

    if chunk.get("analysis_plan"):
        message_buffer.update_report_section("analysis_plan", chunk["analysis_plan"])
        message_buffer.update_agent_status("Investment Orchestrator", "completed")

    found_active = False

    for analyst_key in ANALYST_ORDER:
        if analyst_key not in selected:
            continue

        agent_name = ANALYST_AGENT_NAMES[analyst_key]
        report_key = ANALYST_REPORT_MAP[analyst_key]

        # Capture new report content from current chunk
        if chunk.get(report_key):
            message_buffer.update_report_section(report_key, chunk[report_key])

        # Determine status from accumulated sections, not just current chunk
        has_report = bool(message_buffer.report_sections.get(report_key))

        if has_report:
            message_buffer.update_agent_status(agent_name, "completed")
        elif active_key == analyst_key and not found_active:
            message_buffer.update_agent_status(agent_name, "in_progress")
            found_active = True
        elif active_key not in selected and not found_active:
            message_buffer.update_agent_status(agent_name, "in_progress")
            found_active = True
        else:
            message_buffer.update_agent_status(agent_name, "pending")

    # When all capabilities complete, transition the debate stack to in_progress
    if not found_active and selected:
        if message_buffer.agent_status.get(THESIS_ENGINE) == "pending":
            message_buffer.update_agent_status(THESIS_ENGINE, "in_progress")

def extract_content_string(content):
    """Extract string content from various message formats.
    Returns None if no meaningful text content is found.
    """
    import ast

    def is_empty(val):
        """Check if value is empty using Python's truthiness."""
        if val is None or val == '':
            return True
        if isinstance(val, str):
            s = val.strip()
            if not s:
                return True
            try:
                return not bool(ast.literal_eval(s))
            except (ValueError, SyntaxError):
                return False  # Can't parse = real text
        return not bool(val)

    if is_empty(content):
        return None

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, dict):
        text = content.get('text', '')
        return text.strip() if not is_empty(text) else None

    if isinstance(content, list):
        text_parts = [
            item.get('text', '').strip() if isinstance(item, dict) and item.get('type') == 'text'
            else (item.strip() if isinstance(item, str) else '')
            for item in content
        ]
        result = ' '.join(t for t in text_parts if t and not is_empty(t))
        return result if result else None

    return str(content).strip() if not is_empty(content) else None


def classify_message_type(message) -> tuple[str, str | None]:
    """Classify LangChain message into display type and extract content.

    Returns:
        (type, content) - type is one of: User, Agent, Data, Control
                        - content is extracted string or None
    """
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    content = extract_content_string(getattr(message, 'content', None))

    if isinstance(message, HumanMessage):
        if content and content.strip() == "Continue":
            return ("Control", content)
        return ("User", content)

    if isinstance(message, ToolMessage):
        return ("Data", content)

    if isinstance(message, AIMessage):
        return ("Agent", content)

    # Fallback for unknown types
    return ("System", content)


def format_tool_args(args, max_length=80) -> str:
    """Format tool arguments for terminal display."""
    result = str(args)
    if len(result) > max_length:
        return result[:max_length - 3] + "..."
    return result

def run_analysis():
    # First get all user selections
    selections = get_user_selections()

    # Create config with selected research depth
    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = selections["research_depth"]
    config["max_risk_discuss_rounds"] = selections["research_depth"]
    config["quick_think_llm"] = selections["shallow_thinker"]
    config["deep_think_llm"] = selections["deep_thinker"]
    config["backend_url"] = selections["backend_url"]
    config["llm_provider"] = selections["llm_provider"].lower()
    config["orchestrator_position_importance"] = selections["position_importance"]
    config["orchestrator_token_budget"] = selections["token_budget"]
    config["institutional_loop_mode"] = RUN_MODE_LOOP_PRESETS.get(
        selections["run_mode"], DEFAULT_CONFIG.get("institutional_loop_mode", "lean")
    )
    config["enable_dynamic_capability_expansion"] = (
        config["institutional_loop_mode"] != "lean"
    )
    if config["institutional_loop_mode"] == "lean":
        config["max_risk_discuss_rounds"] = 0
    # Provider-specific thinking configuration
    config["google_thinking_level"] = selections.get("google_thinking_level")
    config["openai_reasoning_effort"] = selections.get("openai_reasoning_effort")
    config["anthropic_effort"] = selections.get("anthropic_effort")

    # Create stats callback handler for tracking LLM/tool calls
    stats_handler = StatsCallbackHandler()

    # Normalize capability selection to predefined order (selection is a 'set', order is fixed)
    selected_set = {analyst.value for analyst in selections["analysts"]}
    selected_analyst_keys = [a for a in ANALYST_ORDER if a in selected_set]

    # Initialize the graph with callbacks bound to LLMs
    graph = FutureInvestGraph(
        selected_analyst_keys,
        config=config,
        debug=True,
        callbacks=[stats_handler],
    )

    # Initialize message buffer with selected capabilities
    message_buffer.init_for_analysis(selected_analyst_keys)

    # Track start time for elapsed display
    start_time = time.time()

    # Create result directory
    results_dir = Path(config["results_dir"]) / selections["ticker"] / selections["analysis_date"]
    results_dir.mkdir(parents=True, exist_ok=True)
    report_dir = results_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / "message_tool.log"
    log_file.touch(exist_ok=True)

    def save_message_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, message_type, content = obj.messages[-1]
            content = content.replace("\n", " ")  # Replace newlines with spaces
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [{message_type}] {content}\n")
        return wrapper
    
    def save_tool_call_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, tool_name, args = obj.tool_calls[-1]
            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [Tool Call] {tool_name}({args_str})\n")
        return wrapper

    def save_report_section_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(section_name, content):
            func(section_name, content)
            if section_name in obj.report_sections and obj.report_sections[section_name] is not None:
                content = obj.report_sections[section_name]
                if content:
                    file_name = f"{section_name}.md"
                    text = "\n".join(str(item) for item in content) if isinstance(content, list) else content
                    with open(report_dir / file_name, "w") as f:
                        f.write(text)
        return wrapper

    message_buffer.add_message = save_message_decorator(message_buffer, "add_message")
    message_buffer.add_tool_call = save_tool_call_decorator(message_buffer, "add_tool_call")
    message_buffer.update_report_section = save_report_section_decorator(message_buffer, "update_report_section")

    # Now start the display layout
    layout = create_layout()

    with Live(layout, refresh_per_second=4) as live:
        # Initial display
        update_display(
            layout,
            stats_handler=stats_handler,
            start_time=start_time,
            session_context=selections,
        )

        # Add initial messages
        message_buffer.add_message("System", f"Selected ticker: {selections['ticker']}")
        message_buffer.add_message(
            "System", f"Analysis date: {selections['analysis_date']}"
        )
        message_buffer.add_message("System", f"Run mode: {selections['run_mode_label']}")
        message_buffer.add_message(
            "System",
            f"Position importance: {format_position_importance(selections)}",
        )
        message_buffer.add_message(
            "System", f"Token budget: {format_token_budget(selections)}"
        )
        message_buffer.add_message(
            "System",
            f"Model backend: {selections['llm_provider'].title()}",
        )
        message_buffer.add_message(
            "System",
            "Selected capabilities: "
            + ", ".join(ANALYST_DISPLAY_NAMES[analyst.value] for analyst in selections["analysts"]),
        )
        message_buffer.add_message(
            "System",
            f"Model pairing: {selections['shallow_thinker']} / {selections['deep_thinker']}",
        )
        update_display(
            layout,
            stats_handler=stats_handler,
            start_time=start_time,
            session_context=selections,
        )

        # Orchestration runs first and decides the capability path.
        message_buffer.update_agent_status("Investment Orchestrator", "in_progress")
        update_display(
            layout,
            stats_handler=stats_handler,
            start_time=start_time,
            session_context=selections,
        )

        # Create spinner text
        spinner_text = (
            f"Analyzing {selections['ticker']} on {selections['analysis_date']}..."
        )
        update_display(
            layout,
            spinner_text,
            stats_handler=stats_handler,
            start_time=start_time,
            session_context=selections,
        )

        # Initialize state and get graph args with callbacks
        init_agent_state = graph.propagator.create_initial_state(
            selections["ticker"], selections["analysis_date"], selected_analyst_keys
        )
        # Pass callbacks to graph config for tool execution tracking
        # (LLM tracking is handled separately via LLM constructor)
        args = graph.propagator.get_graph_args(callbacks=[stats_handler])

        # Stream the analysis
        trace = []
        for chunk in graph.graph.stream(init_agent_state, **args):
            # Process messages if present (skip duplicates via message ID)
            if len(chunk["messages"]) > 0:
                last_message = chunk["messages"][-1]
                msg_id = getattr(last_message, "id", None)

                if msg_id != message_buffer._last_message_id:
                    message_buffer._last_message_id = msg_id

                    # Add message to buffer
                    msg_type, content = classify_message_type(last_message)
                    if content and content.strip():
                        message_buffer.add_message(msg_type, content)

                    # Handle tool calls
                    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            if isinstance(tool_call, dict):
                                message_buffer.add_tool_call(
                                    tool_call["name"], tool_call["args"]
                                )
                            else:
                                message_buffer.add_tool_call(tool_call.name, tool_call.args)

            # Update capability statuses based on report state (runs on every chunk)
            update_analyst_statuses(message_buffer, chunk)

            sync_report_sections_from_state(message_buffer, chunk)

            thesis_stage_entries = get_thesis_review_entries(chunk)[:2]
            if any(_clean_text(content) for _, content in thesis_stage_entries):
                update_research_team_status("in_progress")

            thesis_final_memo = _clean_text(
                (chunk.get("thesis_review") or {}).get("final_memo")
            )
            if thesis_final_memo:
                update_research_team_status("completed")
                if message_buffer.agent_status.get(EXECUTION_ENGINE) == "pending":
                    message_buffer.update_agent_status(EXECUTION_ENGINE, "in_progress")

            execution_content = _clean_text(
                (chunk.get("execution_state") or {}).get("full_blueprint")
            )
            if execution_content:
                if message_buffer.agent_status.get(EXECUTION_ENGINE) != "completed":
                    message_buffer.update_agent_status(EXECUTION_ENGINE, "completed")
                    message_buffer.update_agent_status(
                        UPSIDE_CAPTURE_ENGINE, "in_progress"
                    )

            upside_content = get_review_output(
                chunk.get("allocation_review"), UPSIDE_STAGE_KEY
            )
            downside_content = get_review_output(
                chunk.get("allocation_review"), DOWNSIDE_STAGE_KEY
            )
            portfolio_fit_content = get_review_output(
                chunk.get("allocation_review"), PORTFOLIO_FIT_STAGE_KEY
            )

            if _clean_text(upside_content):
                if message_buffer.agent_status.get(UPSIDE_CAPTURE_ENGINE) != "completed":
                    message_buffer.update_agent_status(
                        UPSIDE_CAPTURE_ENGINE, "in_progress"
                    )
            if _clean_text(downside_content):
                if (
                    message_buffer.agent_status.get(DOWNSIDE_GUARDRAIL_ENGINE)
                    != "completed"
                ):
                    message_buffer.update_agent_status(
                        DOWNSIDE_GUARDRAIL_ENGINE, "in_progress"
                    )
            if _clean_text(portfolio_fit_content):
                if message_buffer.agent_status.get(PORTFOLIO_FIT_ENGINE) != "completed":
                    message_buffer.update_agent_status(
                        PORTFOLIO_FIT_ENGINE, "in_progress"
                    )

            final_decision_content = _clean_text(
                (chunk.get("final_decision") or {}).get("full_decision")
            )
            if final_decision_content:
                if (
                    message_buffer.agent_status.get(CAPITAL_ALLOCATION_COMMITTEE)
                    != "completed"
                ):
                    message_buffer.update_agent_status(
                        CAPITAL_ALLOCATION_COMMITTEE, "in_progress"
                    )
                    message_buffer.update_agent_status(
                        UPSIDE_CAPTURE_ENGINE, "completed"
                    )
                    message_buffer.update_agent_status(
                        DOWNSIDE_GUARDRAIL_ENGINE, "completed"
                    )
                    message_buffer.update_agent_status(PORTFOLIO_FIT_ENGINE, "completed")
                    message_buffer.update_agent_status(
                        CAPITAL_ALLOCATION_COMMITTEE, "completed"
                    )

            # Update the display
            update_display(
                layout,
                stats_handler=stats_handler,
                start_time=start_time,
                session_context=selections,
            )

            trace.append(chunk)

        # Get final state and decision
        final_state = trace[-1]
        decision = graph.process_signal(
            _clean_text((final_state.get("final_decision") or {}).get("full_decision"))
            or final_state.get("final_trade_decision", "")
        )

        # Update all agent statuses to completed
        for agent in message_buffer.agent_status:
            message_buffer.update_agent_status(agent, "completed")

        message_buffer.add_message(
            "System", f"Completed analysis for {selections['analysis_date']}"
        )

        # Update final report sections
        sync_report_sections_from_state(message_buffer, final_state)

        update_display(
            layout,
            stats_handler=stats_handler,
            start_time=start_time,
            session_context=selections,
        )

    # Post-analysis prompts (outside Live context for clean interaction)
    console.print(f"\n[bold cyan]{BRAND_NAME} run complete.[/bold cyan]\n")
    next_action = select_post_run_action()

    if next_action in ("save", "save_display"):
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = Path.cwd() / "reports" / f"{selections['ticker']}_{timestamp}"
        save_path_str = typer.prompt(
            "Save path (press Enter for default)",
            default=str(default_path)
        ).strip()
        save_path = Path(save_path_str)
        try:
            report_file = save_report_to_disk(
                final_state,
                selections["ticker"],
                save_path,
                session_context=selections,
            )
            console.print(f"\n[green]✓ Report saved to:[/green] {save_path.resolve()}")
            console.print(f"  [dim]Complete report:[/dim] {report_file.name}")
        except Exception as e:
            console.print(f"[red]Error saving report: {e}[/red]")

    if next_action in ("display", "save_display"):
        display_complete_report(final_state)


@app.command()
def analyze():
    run_analysis()


if __name__ == "__main__":
    app()
