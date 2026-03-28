# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional

from langgraph.prebuilt import ToolNode

from tradingagents.llm_clients import create_llm_client

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import (
    FinancialSituationMemory,
    InstitutionalMemoryStore,
)
from tradingagents.agents.utils.agent_states import (
    AgentState,
)
from tradingagents.agents.utils.agent_utils import (
    ANALYST_ORDER,
    ANALYST_REPORT_FIELDS,
    normalize_selected_analysts,
)
from tradingagents.agents.utils.decision_protocol import (
    build_institutional_loop_packet,
    render_institutional_loop_packet,
)
from tradingagents.dataflows.config import set_config

# Import the new abstract tool methods from agent_utils
from tradingagents.agents.utils.agent_utils import (
    get_stock_data,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_insider_transactions,
    get_global_news
)

from .conditional_logic import ConditionalLogic
from .run_trace import RunTraceRecorder, activate_run_trace, wrap_tool_with_trace
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class FutureInvestGraph:
    """Main class that orchestrates the Future Invest runtime."""

    def __init__(
        self,
        selected_analysts=None,
        debug=False,
        config: Dict[str, Any] = None,
        callbacks: Optional[List] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of capability ids to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
            callbacks: Optional list of callback handlers (e.g., for tracking LLM/tool stats)
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG
        self.callbacks = callbacks or []
        self.selected_analysts = normalize_selected_analysts(
            selected_analysts or ANALYST_ORDER
        )

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs with provider-specific thinking configuration
        llm_kwargs = self._get_provider_kwargs()

        # Add callbacks to kwargs if provided (passed to LLM constructor)
        if self.callbacks:
            llm_kwargs["callbacks"] = self.callbacks

        deep_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["deep_think_llm"],
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )
        quick_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["quick_think_llm"],
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )

        self.deep_thinking_llm = deep_client.get_llm()
        self.quick_thinking_llm = quick_client.get_llm()
        
        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.portfolio_manager_memory = FinancialSituationMemory("portfolio_manager_memory", self.config)
        self.institutional_memory = InstitutionalMemoryStore(self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.config["max_debate_rounds"],
            max_risk_discuss_rounds=self.config["max_risk_discuss_rounds"],
        )
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.portfolio_manager_memory,
            self.conditional_logic,
            self.config,
        )

        self.propagator = Propagator(
            max_recur_limit=self.config.get("max_recur_limit", 100)
        )
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(self.selected_analysts)

    def _get_provider_kwargs(self) -> Dict[str, Any]:
        """Get provider-specific kwargs for LLM client creation."""
        kwargs = {}
        provider = self.config.get("llm_provider", "").lower()

        if provider == "google":
            thinking_level = self.config.get("google_thinking_level")
            if thinking_level:
                kwargs["thinking_level"] = thinking_level

        elif provider in {"openai", "vectorengine"}:
            reasoning_effort = self.config.get("openai_reasoning_effort")
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort
            kwargs["transient_retry_attempts"] = self.config.get(
                "transient_retry_attempts", 3
            )
            kwargs["retry_base_delay_seconds"] = self.config.get(
                "retry_base_delay_seconds", 1.5
            )
            kwargs["retry_max_delay_seconds"] = self.config.get(
                "retry_max_delay_seconds", 8.0
            )

        elif provider == "anthropic":
            effort = self.config.get("anthropic_effort")
            if effort:
                kwargs["effort"] = effort

        return kwargs

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources using abstract methods."""
        wrapped_get_stock_data = wrap_tool_with_trace(get_stock_data)
        wrapped_get_indicators = wrap_tool_with_trace(get_indicators)
        wrapped_get_news = wrap_tool_with_trace(get_news)
        wrapped_get_global_news = wrap_tool_with_trace(get_global_news)
        wrapped_get_insider_transactions = wrap_tool_with_trace(
            get_insider_transactions
        )
        wrapped_get_fundamentals = wrap_tool_with_trace(get_fundamentals)
        wrapped_get_balance_sheet = wrap_tool_with_trace(get_balance_sheet)
        wrapped_get_cashflow = wrap_tool_with_trace(get_cashflow)
        wrapped_get_income_statement = wrap_tool_with_trace(get_income_statement)

        return {
            "business_truth": ToolNode(
                [
                    # Fundamental analysis tools
                    wrapped_get_fundamentals,
                    wrapped_get_balance_sheet,
                    wrapped_get_cashflow,
                    wrapped_get_income_statement,
                ]
            ),
            "market_expectations": ToolNode(
                [
                    # Core stock data tools
                    wrapped_get_stock_data,
                    # Technical indicators
                    wrapped_get_indicators,
                ]
            ),
            "timing_catalyst": ToolNode(
                [
                    # News, macro flow, and insider information for timing-aware catalyst work
                    wrapped_get_news,
                    wrapped_get_global_news,
                    wrapped_get_insider_transactions,
                ]
            ),
        }

    def propagate(self, company_name, trade_date):
        """Run the trading agents graph for a company on a specific date."""

        self.ticker = company_name
        loop_mode = self.config.get("institutional_loop_mode", "full")
        recorder = RunTraceRecorder(
            self.config,
            company_name,
            str(trade_date),
            self.selected_analysts,
            loop_mode,
        )

        # Initialize state
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date, self.selected_analysts
        )
        init_agent_state["institution_memory_snapshot"] = (
            self.institutional_memory.get_company_memory_snapshot(company_name)
        )
        init_agent_state["institution_memory_brief"] = (
            self.institutional_memory.render_company_brief(company_name)
        )
        args = self.propagator.get_graph_args()

        with activate_run_trace(recorder):
            if self.debug:
                # Debug mode with tracing
                trace = []
                for chunk in self.graph.stream(init_agent_state, **args):
                    if len(chunk["messages"]) == 0:
                        pass
                    else:
                        chunk["messages"][-1].pretty_print()
                        trace.append(chunk)

                final_state = trace[-1]
            else:
                # Standard mode without tracing
                final_state = self.graph.invoke(init_agent_state, **args)

        # Store current state for reflection
        self.curr_state = final_state

        final_state["institutional_loop_mode"] = loop_mode
        final_state["institutional_trace"] = recorder.summary()
        final_state["institutional_loop_packet"] = build_institutional_loop_packet(
            final_state
        )
        final_state["institutional_loop_packet_markdown"] = (
            render_institutional_loop_packet(final_state["institutional_loop_packet"])
        )

        # Return decision and processed signal
        final_decision_text = extract_final_decision_text(final_state)
        processed_signal = self.process_signal(final_decision_text)
        recorder.finalize(final_state, processed_signal)
        final_state["institutional_trace"] = recorder.summary()
        self.institutional_memory.record_run(company_name, trade_date, final_state)

        # Log state after trace finalization so downstream surfaces see the final summary.
        self._log_state(trade_date, final_state)
        return final_state, processed_signal

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        log_entry = build_state_log_entry(final_state)
        self.log_states_dict[str(trade_date)] = log_entry

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        bull_reflection = self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        bear_reflection = self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        trader_reflection = self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        director_reflection = self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        allocator_reflection = self.reflector.reflect_portfolio_manager(
            self.curr_state, returns_losses, self.portfolio_manager_memory
        )
        self.institutional_memory.record_outcome(
            self.ticker,
            self.curr_state.get("trade_date", date.today()),
            self.curr_state,
            returns_losses,
            reflections={
                "engine::thesis_engine": bull_reflection,
                "engine::challenge_engine": bear_reflection,
                "engine::execution_engine": trader_reflection,
                "engine::investment_director": director_reflection,
                "engine::capital_allocation_committee": allocator_reflection,
            },
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)


# Compatibility alias for existing code paths.
TradingAgentsGraph = FutureInvestGraph


def extract_final_decision_text(final_state: Dict[str, Any]) -> str:
    """Return the canonical final-decision memo, falling back to compatibility fields."""
    return (
        final_state.get("final_decision", {}).get("full_decision")
        or final_state.get("final_trade_decision", "")
    )


def build_state_log_entry(final_state: Dict[str, Any]) -> Dict[str, Any]:
    """Build the canonical state log entry with a nested compatibility snapshot."""
    log_entry = {
        "company_of_interest": final_state["company_of_interest"],
        "trade_date": final_state["trade_date"],
        "selected_analysts": final_state.get("selected_analysts", []),
        "analysis_plan": final_state.get("analysis_plan", ""),
        "analysis_brief": final_state.get("analysis_brief", ""),
        "analysis_artifacts": final_state.get("analysis_artifacts", {}),
        "orchestration_journal": final_state.get("orchestration_journal", []),
        "orchestration_state": final_state.get("orchestration_state", {}),
        "portfolio_context": final_state.get("portfolio_context", {}),
        "temporal_context": final_state.get("temporal_context", {}),
        "institution_memory_snapshot": final_state.get("institution_memory_snapshot", {}),
        "institution_memory_brief": final_state.get("institution_memory_brief", ""),
        "decision_dossier": final_state.get("decision_dossier", {}),
        "decision_dossier_markdown": final_state.get("decision_dossier_markdown", ""),
        "institutional_loop_mode": final_state.get("institutional_loop_mode", "full"),
        "institutional_trace": final_state.get("institutional_trace", {}),
        "institutional_loop_packet": final_state.get("institutional_loop_packet", {}),
        "institutional_loop_packet_markdown": final_state.get(
            "institutional_loop_packet_markdown", ""
        ),
        "thesis_review": final_state.get("thesis_review", {}),
        "execution_state": final_state.get("execution_state", {}),
        "allocation_review": final_state.get("allocation_review", {}),
        "final_decision": final_state.get("final_decision", {}),
        "compatibility_snapshot": {
            "investment_debate_state": final_state.get("investment_debate_state", {}),
            "investment_plan": final_state.get("investment_plan", ""),
            "trader_investment_plan": final_state.get("trader_investment_plan", ""),
            "risk_debate_state": final_state.get("risk_debate_state", {}),
            "final_trade_decision": final_state.get("final_trade_decision", ""),
        },
    }
    for report_field in ANALYST_REPORT_FIELDS.values():
        log_entry[report_field] = final_state[report_field]
    return log_entry
