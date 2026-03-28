import questionary
from typing import List, Optional, Tuple, Dict
from datetime import datetime

from rich.console import Console

from cli.models import AnalystType
from tradingagents.agents.utils.agent_utils import (
    ANALYST_ORDER as CAPABILITY_ORDER,
    ANALYST_SELECTION_LABELS,
)

console = Console()

TICKER_INPUT_EXAMPLES = "Examples: SPY, CNC.TO, 7203.T, 0700.HK"

CAPABILITY_CHOICES = [
    (ANALYST_SELECTION_LABELS[key], AnalystType(key)) for key in CAPABILITY_ORDER
]

RUN_MODE_PRESETS: Dict[str, Dict[str, object]] = {
    "scout": {
        "label": "Scout",
        "description": "Fast pass for idea triage and early signal detection",
        "suggested_depth": 1,
    },
    "conviction": {
        "label": "Conviction Build",
        "description": "Balanced path for developing a real investment case",
        "suggested_depth": 3,
    },
    "committee": {
        "label": "Capital Committee",
        "description": "Full institutional review for sizing and allocation decisions",
        "suggested_depth": 5,
    },
    "hard_loop": {
        "label": "Hard Loop",
        "description": "Lean institutional loop with hard outputs and tighter traceability",
        "suggested_depth": 2,
    },
}

RUN_MODE_CONTROL_PRESETS: Dict[str, Dict[str, str]] = {
    "scout": {
        "position_importance": "standard",
        "token_budget": "tight",
    },
    "conviction": {
        "position_importance": "high",
        "token_budget": "balanced",
    },
    "committee": {
        "position_importance": "critical",
        "token_budget": "expansive",
    },
    "hard_loop": {
        "position_importance": "high",
        "token_budget": "balanced",
    },
}

RUN_MODE_LOOP_PRESETS: Dict[str, str] = {
    "scout": "lean",
    "conviction": "lean",
    "committee": "full",
    "hard_loop": "lean",
}

RUN_MODE_ANALYST_PRESETS: Dict[str, List[str]] = {
    "scout": ["business_truth", "market_expectations"],
    "conviction": ["business_truth", "market_expectations", "timing_catalyst"],
    "committee": list(CAPABILITY_ORDER),
    "hard_loop": ["business_truth", "market_expectations", "timing_catalyst"],
}

POSITION_IMPORTANCE_OPTIONS = [
    (
        "Standard - Routine seat with balanced review and faster escalation thresholds",
        "standard",
    ),
    (
        "High - Meaningful seat that deserves broader evidence gathering before sizing",
        "high",
    ),
    (
        "Critical - Institution-defining seat; bias toward deeper challenge and confirmation",
        "critical",
    ),
]

POSITION_IMPORTANCE_LABELS = {
    "standard": "Standard",
    "high": "High",
    "critical": "Critical",
}

TOKEN_BUDGET_OPTIONS = [
    (
        "Tight - Conserve tokens, stop once the edge is legible enough to act",
        "tight",
    ),
    (
        "Balanced - Default posture with room for challenge and selective escalation",
        "balanced",
    ),
    (
        "Expansive - Spend research budget freely for high-stakes institutional review",
        "expansive",
    ),
]

TOKEN_BUDGET_LABELS = {
    "tight": "Tight",
    "balanced": "Balanced",
    "expansive": "Expansive",
}

RESEARCH_DEPTH_OPTIONS = [
    (
        "Shallow - Fast institution run, fewer debate and capital formation cycles",
        1,
    ),
    ("Focused - Lean institutional loop with one hard synthesis pass", 2),
    ("Medium - Balanced depth with moderate institutional review", 3),
    ("Deep - Full institutional pass with richer debate and risk formation", 5),
]

RESEARCH_DEPTH_LABELS = {
    1: "Shallow",
    2: "Focused",
    3: "Medium",
    5: "Deep",
}


def get_ticker(default: str = "SPY") -> str:
    """Prompt the user to enter a ticker symbol."""
    ticker = questionary.text(
        f"Enter the exact ticker symbol to analyze ({TICKER_INPUT_EXAMPLES}):",
        default=default,
        validate=lambda x: len(x.strip()) > 0 or "Please enter a valid ticker symbol.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not ticker:
        console.print("\n[red]No ticker symbol provided. Exiting...[/red]")
        exit(1)

    return normalize_ticker_symbol(ticker)


def normalize_ticker_symbol(ticker: str) -> str:
    """Normalize ticker input while preserving exchange suffixes."""
    return ticker.strip().upper()


def get_analysis_date(default: Optional[str] = None, allow_future: bool = False) -> str:
    """Prompt the user to enter a date in YYYY-MM-DD format."""
    import re

    def validate_date(date_str: str) -> bool:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return False
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            if not allow_future and parsed_date.date() > datetime.now().date():
                return False
            return True
        except ValueError:
            return False

    date = questionary.text(
        "Enter the analysis date (YYYY-MM-DD):",
        default=default or datetime.now().strftime("%Y-%m-%d"),
        validate=lambda x: validate_date(x.strip())
        or "Please enter a valid date in YYYY-MM-DD format that is not in the future.",
        style=questionary.Style(
            [
                ("text", "fg:green"),
                ("highlighted", "noinherit"),
            ]
        ),
    ).ask()

    if not date:
        console.print("\n[red]No date provided. Exiting...[/red]")
        exit(1)

    return date.strip()


def select_run_mode() -> Tuple[str, str, int, str]:
    """Select the institution run mode."""
    choice = questionary.select(
        "Select Your [Run Mode]:",
        choices=[
            questionary.Choice(
                f"{preset['label']} - {preset['description']}",
                value=(
                    key,
                    str(preset["label"]),
                    int(preset["suggested_depth"]),
                    str(preset["description"]),
                ),
            )
            for key, preset in RUN_MODE_PRESETS.items()
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:cyan noinherit"),
                ("highlighted", "fg:cyan noinherit"),
                ("pointer", "fg:cyan noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No run mode selected. Exiting...[/red]")
        exit(1)

    return choice


def select_analysts() -> List[AnalystType]:
    """Select abstract research capabilities using an interactive checkbox."""
    choices = questionary.checkbox(
        "Select Your [Signal Stack]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in CAPABILITY_CHOICES
        ],
        instruction="\n- Press Space to select/unselect capabilities\n- Press 'a' to select/unselect all\n- Press Enter when the stack looks right",
        validate=lambda x: len(x) > 0 or "You must select at least one capability.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        console.print("\n[red]No capabilities selected. Exiting...[/red]")
        exit(1)

    return choices


def select_research_depth(recommended_depth: Optional[int] = None) -> int:
    """Select how many institutional review cycles to run."""
    depth_options = list(RESEARCH_DEPTH_OPTIONS)
    if recommended_depth in RESEARCH_DEPTH_LABELS:
        depth_options.sort(key=lambda item: item[1] != recommended_depth)

    choice = questionary.select(
        "Select Your [Research Depth]:",
        choices=[
            questionary.Choice(
                f"{display} [Recommended]" if value == recommended_depth else display,
                value=value,
            )
            for display, value in depth_options
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:yellow noinherit"),
                ("highlighted", "fg:yellow noinherit"),
                ("pointer", "fg:yellow noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No research depth selected. Exiting...[/red]")
        exit(1)

    return choice


def select_position_importance(recommended: Optional[str] = None) -> str:
    """Select how important this seat is to the institution."""
    options = list(POSITION_IMPORTANCE_OPTIONS)
    if recommended in POSITION_IMPORTANCE_LABELS:
        options.sort(key=lambda item: item[1] != recommended)

    choice = questionary.select(
        "Select Your [Position Importance]:",
        choices=[
            questionary.Choice(
                f"{display} [Recommended]" if value == recommended else display,
                value=value,
            )
            for display, value in options
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:yellow noinherit"),
                ("highlighted", "fg:yellow noinherit"),
                ("pointer", "fg:yellow noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No position importance selected. Exiting...[/red]")
        exit(1)

    return choice


def select_token_budget(recommended: Optional[str] = None) -> str:
    """Select the research spend posture for the session."""
    options = list(TOKEN_BUDGET_OPTIONS)
    if recommended in TOKEN_BUDGET_LABELS:
        options.sort(key=lambda item: item[1] != recommended)

    choice = questionary.select(
        "Select Your [Token Budget]:",
        choices=[
            questionary.Choice(
                f"{display} [Recommended]" if value == recommended else display,
                value=value,
            )
            for display, value in options
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:yellow noinherit"),
                ("highlighted", "fg:yellow noinherit"),
                ("pointer", "fg:yellow noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No token budget selected. Exiting...[/red]")
        exit(1)

    return choice


def select_shallow_thinking_agent(provider) -> str:
    """Select shallow thinking llm engine using an interactive selection."""

    # Define shallow thinking llm engine options with their corresponding model names
    # Ordering: medium → light → heavy (balanced first for quick tasks)
    # Within same tier, newer models first
    SHALLOW_AGENT_OPTIONS = {
        "openai": [
            ("GPT-5 Mini - Balanced speed, cost, and capability", "gpt-5-mini"),
            ("GPT-5 Nano - High-throughput, simple tasks", "gpt-5-nano"),
            ("GPT-5.4 - Latest frontier, 1M context", "gpt-5.4"),
            ("GPT-4.1 - Smartest non-reasoning model", "gpt-4.1"),
        ],
        "anthropic": [
            ("Claude Sonnet 4.6 - Best speed and intelligence balance", "claude-sonnet-4-6"),
            ("Claude Haiku 4.5 - Fast, near-instant responses", "claude-haiku-4-5"),
            ("Claude Sonnet 4.5 - Agents and coding", "claude-sonnet-4-5"),
        ],
        "google": [
            ("Gemini 3 Flash - Next-gen fast", "gemini-3-flash-preview"),
            ("Gemini 2.5 Flash - Balanced, stable", "gemini-2.5-flash"),
            ("Gemini 3.1 Flash Lite - Most cost-efficient", "gemini-3.1-flash-lite-preview"),
            ("Gemini 2.5 Flash Lite - Fast, low-cost", "gemini-2.5-flash-lite"),
        ],
        "xai": [
            ("Grok 4.1 Fast (Non-Reasoning) - Speed optimized, 2M ctx", "grok-4-1-fast-non-reasoning"),
            ("Grok 4 Fast (Non-Reasoning) - Speed optimized", "grok-4-fast-non-reasoning"),
            ("Grok 4.1 Fast (Reasoning) - High-performance, 2M ctx", "grok-4-1-fast-reasoning"),
        ],
        "openrouter": [
            ("NVIDIA Nemotron 3 Nano 30B (free)", "nvidia/nemotron-3-nano-30b-a3b:free"),
            ("Z.AI GLM 4.5 Air (free)", "z-ai/glm-4.5-air:free"),
        ],
        "ollama": [
            ("Qwen3:latest (8B, local)", "qwen3:latest"),
            ("GPT-OSS:latest (20B, local)", "gpt-oss:latest"),
            ("GLM-4.7-Flash:latest (30B, local)", "glm-4.7-flash:latest"),
        ],
    }

    choice = questionary.select(
        "Select Your [Scanning Engine]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in SHALLOW_AGENT_OPTIONS[provider.lower()]
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print(
            "\n[red]No shallow thinking llm engine selected. Exiting...[/red]"
        )
        exit(1)

    return choice


def select_deep_thinking_agent(provider) -> str:
    """Select deep thinking llm engine using an interactive selection."""

    # Define deep thinking llm engine options with their corresponding model names
    # Ordering: heavy → medium → light (most capable first for deep tasks)
    # Within same tier, newer models first
    DEEP_AGENT_OPTIONS = {
        "openai": [
            ("GPT-5.4 - Latest frontier, 1M context", "gpt-5.4"),
            ("GPT-5.2 - Strong reasoning, cost-effective", "gpt-5.2"),
            ("GPT-5 Mini - Balanced speed, cost, and capability", "gpt-5-mini"),
            ("GPT-5.4 Pro - Most capable, expensive ($30/$180 per 1M tokens)", "gpt-5.4-pro"),
        ],
        "anthropic": [
            ("Claude Opus 4.6 - Most intelligent, agents and coding", "claude-opus-4-6"),
            ("Claude Opus 4.5 - Premium, max intelligence", "claude-opus-4-5"),
            ("Claude Sonnet 4.6 - Best speed and intelligence balance", "claude-sonnet-4-6"),
            ("Claude Sonnet 4.5 - Agents and coding", "claude-sonnet-4-5"),
        ],
        "google": [
            ("Gemini 3.1 Pro - Reasoning-first, complex workflows", "gemini-3.1-pro-preview"),
            ("Gemini 3 Flash - Next-gen fast", "gemini-3-flash-preview"),
            ("Gemini 2.5 Pro - Stable pro model", "gemini-2.5-pro"),
            ("Gemini 2.5 Flash - Balanced, stable", "gemini-2.5-flash"),
        ],
        "xai": [
            ("Grok 4 - Flagship model", "grok-4-0709"),
            ("Grok 4.1 Fast (Reasoning) - High-performance, 2M ctx", "grok-4-1-fast-reasoning"),
            ("Grok 4 Fast (Reasoning) - High-performance", "grok-4-fast-reasoning"),
            ("Grok 4.1 Fast (Non-Reasoning) - Speed optimized, 2M ctx", "grok-4-1-fast-non-reasoning"),
        ],
        "openrouter": [
            ("Z.AI GLM 4.5 Air (free)", "z-ai/glm-4.5-air:free"),
            ("NVIDIA Nemotron 3 Nano 30B (free)", "nvidia/nemotron-3-nano-30b-a3b:free"),
        ],
        "ollama": [
            ("GLM-4.7-Flash:latest (30B, local)", "glm-4.7-flash:latest"),
            ("GPT-OSS:latest (20B, local)", "gpt-oss:latest"),
            ("Qwen3:latest (8B, local)", "qwen3:latest"),
        ],
    }

    choice = questionary.select(
        "Select Your [Judgment Engine]:",
        choices=[
            questionary.Choice(display, value=value)
            for display, value in DEEP_AGENT_OPTIONS[provider.lower()]
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No deep thinking llm engine selected. Exiting...[/red]")
        exit(1)

    return choice

def select_llm_provider() -> tuple[str, str]:
    """Select the OpenAI api url using interactive selection."""
    # Define OpenAI api options with their corresponding endpoints
    BASE_URLS = [
        ("OpenAI", "https://api.openai.com/v1"),
        ("Google", "https://generativelanguage.googleapis.com/v1"),
        ("Anthropic", "https://api.anthropic.com/"),
        ("xAI", "https://api.x.ai/v1"),
        ("Openrouter", "https://openrouter.ai/api/v1"),
        ("Ollama", "http://localhost:11434/v1"),
    ]
    
    choice = questionary.select(
        "Select Your [Model Backend]:",
        choices=[
            questionary.Choice(display, value=(display, value))
            for display, value in BASE_URLS
        ],
        instruction="\n- Use arrow keys to navigate\n- Press Enter to select",
        style=questionary.Style(
            [
                ("selected", "fg:magenta noinherit"),
                ("highlighted", "fg:magenta noinherit"),
                ("pointer", "fg:magenta noinherit"),
            ]
        ),
    ).ask()

    if choice is None:
        console.print("\n[red]No model backend selected. Exiting...[/red]")
        exit(1)
    
    display_name, url = choice
    return display_name, url


def ask_openai_reasoning_effort() -> str:
    """Ask for OpenAI reasoning effort level."""
    choices = [
        questionary.Choice("Medium (Default)", "medium"),
        questionary.Choice("High (More thorough)", "high"),
        questionary.Choice("Low (Faster)", "low"),
    ]
    return questionary.select(
        "Select Reasoning Effort:",
        choices=choices,
        style=questionary.Style([
            ("selected", "fg:cyan noinherit"),
            ("highlighted", "fg:cyan noinherit"),
            ("pointer", "fg:cyan noinherit"),
        ]),
    ).ask()


def ask_anthropic_effort() -> str | None:
    """Ask for Anthropic effort level.

    Controls token usage and response thoroughness on Claude 4.5+ and 4.6 models.
    """
    return questionary.select(
        "Select Effort Level:",
        choices=[
            questionary.Choice("High (recommended)", "high"),
            questionary.Choice("Medium (balanced)", "medium"),
            questionary.Choice("Low (faster, cheaper)", "low"),
        ],
        style=questionary.Style([
            ("selected", "fg:cyan noinherit"),
            ("highlighted", "fg:cyan noinherit"),
            ("pointer", "fg:cyan noinherit"),
        ]),
    ).ask()


def ask_gemini_thinking_config() -> str | None:
    """Ask for Gemini thinking configuration.

    Returns thinking_level: "high" or "minimal".
    Client maps to appropriate API param based on model series.
    """
    return questionary.select(
        "Select Thinking Mode:",
        choices=[
            questionary.Choice("Enable Thinking (recommended)", "high"),
            questionary.Choice("Minimal/Disable Thinking", "minimal"),
        ],
        style=questionary.Style([
            ("selected", "fg:green noinherit"),
            ("highlighted", "fg:green noinherit"),
            ("pointer", "fg:green noinherit"),
        ]),
    ).ask()


def confirm_launch() -> bool:
    """Ask whether to launch the configured session."""
    choice = questionary.select(
        "Launch this Future Invest session?",
        choices=[
            questionary.Choice("Launch session", value=True),
            questionary.Choice("Cancel", value=False),
        ],
        style=questionary.Style(
            [
                ("selected", "fg:cyan noinherit"),
                ("highlighted", "fg:cyan noinherit"),
                ("pointer", "fg:cyan noinherit"),
            ]
        ),
    ).ask()
    return bool(choice)


def select_post_run_action() -> str:
    """Select the next action after a run completes."""
    choice = questionary.select(
        "Choose the next action:",
        choices=[
            questionary.Choice("Save dossier and display on screen", "save_display"),
            questionary.Choice("Save dossier and finish", "save"),
            questionary.Choice("Display dossier on screen", "display"),
            questionary.Choice("Finish without extra actions", "finish"),
        ],
        style=questionary.Style(
            [
                ("selected", "fg:green noinherit"),
                ("highlighted", "fg:green noinherit"),
                ("pointer", "fg:green noinherit"),
            ]
        ),
    ).ask()

    return choice or "finish"
