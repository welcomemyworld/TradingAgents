# TradingAgents/graph/setup.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import (
    ANALYST_DISPLAY_NAMES,
    ANALYST_ORDER,
    CAPITAL_ALLOCATION_COMMITTEE,
    CHALLENGE_ENGINE,
    DOWNSIDE_GUARDRAIL_ENGINE,
    EXECUTION_ENGINE,
    INVESTMENT_DIRECTOR,
    PORTFOLIO_FIT_ENGINE,
    THESIS_ENGINE,
    UPSIDE_CAPTURE_ENGINE,
    get_analyst_clear_node_name,
    get_analyst_node_name,
    get_analyst_report,
    get_report_field_for_analyst,
    get_analyst_tool_node_name,
    normalize_selected_analysts,
)
from tradingagents.agents.utils.decision_protocol import (
    BUSINESS_TRUTH_SECTION_MAP,
    MARKET_EXPECTATIONS_SECTION_MAP,
    TIMING_CATALYST_SECTION_MAP,
    build_dossier_update,
    build_temporal_context_update,
)

from .conditional_logic import ConditionalLogic
from .run_trace import get_active_trace_recorder


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    RESEARCH_FANOUT = "Parallel Research Fanout"
    RESEARCH_JOIN = "Parallel Research Join"

    def __init__(
        self,
        quick_thinking_llm: ChatOpenAI,
        deep_thinking_llm: ChatOpenAI,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        portfolio_manager_memory,
        conditional_logic: ConditionalLogic,
        config: Dict[str, Any],
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.portfolio_manager_memory = portfolio_manager_memory
        self.conditional_logic = conditional_logic
        self.config = config

    def _wrap_analyst_node(self, analyst_key: str, node):
        """Persist only the canonical capability report; merge shared state at the join."""
        report_field = get_report_field_for_analyst(analyst_key)

        def wrapped_node(state):
            recorder = get_active_trace_recorder()
            if recorder:
                recorder.record_capability_event(
                    analyst_key,
                    "started",
                    detail={"agent_name": get_analyst_node_name(analyst_key)},
                )
            result = node(state)
            report = result.get(report_field, "")

            if recorder:
                recorder.record_capability_event(
                    analyst_key,
                    "completed",
                    report=report,
                    status="completed" if report else "missing_report",
                    detail={"agent_name": get_analyst_node_name(analyst_key)},
                )

            cleaned_result = dict(result)
            for shared_key in (
                "analysis_artifacts",
                "completed_analysts",
                "analysis_queue",
                "current_analyst",
                "decision_dossier",
                "decision_dossier_markdown",
                "temporal_context",
            ):
                cleaned_result.pop(shared_key, None)
            return cleaned_result

        return wrapped_node

    def _create_parallel_research_fanout(self):
        def fanout_node(state):
            return {
                "analysis_queue": normalize_selected_analysts(
                    state.get("analysis_queue") or state.get("selected_analysts")
                )
            }

        return fanout_node

    def _create_parallel_research_join(self):
        section_maps = {
            "business_truth": BUSINESS_TRUTH_SECTION_MAP,
            "market_expectations": MARKET_EXPECTATIONS_SECTION_MAP,
            "timing_catalyst": TIMING_CATALYST_SECTION_MAP,
        }

        def join_node(state):
            selected = normalize_selected_analysts(state.get("selected_analysts"))
            completed = []
            artifacts = {}
            dossier_state = {
                "decision_dossier": state.get("decision_dossier"),
                "temporal_context": state.get("temporal_context"),
            }

            for analyst_key in selected:
                report = get_analyst_report(state, analyst_key)
                if not report:
                    continue
                report_field = get_report_field_for_analyst(analyst_key)
                completed.append(analyst_key)
                artifacts[analyst_key] = {
                    "agent_name": ANALYST_DISPLAY_NAMES[analyst_key],
                    "report": report,
                    "report_field": report_field,
                }
                dossier_state.update(
                    build_dossier_update(
                        dossier_state,
                        report,
                        section_maps[analyst_key],
                    )
                )
                dossier_state.update(
                    build_temporal_context_update(
                        dossier_state,
                        report,
                        section_maps[analyst_key],
                    )
                )

            missing = [key for key in selected if key not in completed]
            orchestration_state = dict(state.get("orchestration_state") or {})
            orchestration_state["missing_capabilities"] = missing
            orchestration_state["continue_research"] = False
            orchestration_state["research_mode"] = "parallel_hard_loop"
            if missing:
                orchestration_state["stop_reason"] = (
                    "Parallel research bundle completed with gaps; proceed to thesis synthesis with explicit missing evidence."
                )

            recorder = get_active_trace_recorder()
            if recorder:
                recorder.record_capability_event(
                    "parallel_research_bundle",
                    "joined",
                    status="completed_with_gaps" if missing else "completed",
                    detail={
                        "completed_capabilities": completed,
                        "missing_capabilities": missing,
                    },
                )

            return {
                "analysis_artifacts": artifacts,
                "completed_analysts": completed,
                "analysis_queue": [],
                "current_analyst": "",
                "orchestration_state": orchestration_state,
                **dossier_state,
            }

        return join_node

    def _route_parallel_join(self, state):
        selected = normalize_selected_analysts(state.get("selected_analysts"))
        if all(get_analyst_report(state, analyst_key) for analyst_key in selected):
            return self.RESEARCH_JOIN
        return END

    def setup_graph(
        self, selected_analysts=None
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of capability ids to include. Options are:
                - "business_truth"
                - "market_expectations"
                - "timing_catalyst"
        """
        selected_analysts = normalize_selected_analysts(
            selected_analysts or ANALYST_ORDER
        )
        lean_loop = self.config.get("institutional_loop_mode", "full") == "lean"
        compiled_analysts = (
            ANALYST_ORDER
            if self.config.get("enable_dynamic_capability_expansion", True)
            else selected_analysts
        )

        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no capabilities selected!")

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        analyst_factories = {
            "business_truth": create_fundamentals_analyst,
            "market_expectations": create_market_analyst,
            "timing_catalyst": create_timing_catalyst_analyst,
        }

        for analyst_key in compiled_analysts:
            analyst_nodes[analyst_key] = analyst_factories[analyst_key](
                self.quick_thinking_llm
            )
            delete_nodes[analyst_key] = create_msg_delete()
            tool_nodes[analyst_key] = self.tool_nodes[analyst_key]

        # Create researcher and manager nodes
        investment_orchestrator_node = create_investment_orchestrator(
            self.deep_thinking_llm,
            self.config,
        )
        bull_researcher_node = create_bull_researcher(
            self.quick_thinking_llm, self.bull_memory
        )
        bear_researcher_node = create_bear_researcher(
            self.quick_thinking_llm, self.bear_memory
        )
        research_manager_node = create_research_manager(
            self.deep_thinking_llm, self.invest_judge_memory
        )
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)

        # Create risk analysis nodes
        aggressive_analyst = create_aggressive_debator(self.quick_thinking_llm)
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        conservative_analyst = create_conservative_debator(self.quick_thinking_llm)
        portfolio_manager_node = create_portfolio_manager(
            self.deep_thinking_llm, self.portfolio_manager_memory
        )

        # Create workflow
        workflow = StateGraph(AgentState)

        workflow.add_node("Investment Orchestrator", investment_orchestrator_node)
        workflow.add_node(self.RESEARCH_FANOUT, self._create_parallel_research_fanout())
        workflow.add_node(self.RESEARCH_JOIN, self._create_parallel_research_join())

        # Add analyst nodes to the graph
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(
                get_analyst_node_name(analyst_type),
                self._wrap_analyst_node(analyst_type, node),
            )
            workflow.add_node(
                get_analyst_clear_node_name(analyst_type), delete_nodes[analyst_type]
            )
            workflow.add_node(
                get_analyst_tool_node_name(analyst_type), tool_nodes[analyst_type]
            )

        # Add other nodes
        workflow.add_node(THESIS_ENGINE, bull_researcher_node)
        workflow.add_node(CHALLENGE_ENGINE, bear_researcher_node)
        workflow.add_node(INVESTMENT_DIRECTOR, research_manager_node)
        workflow.add_node(EXECUTION_ENGINE, trader_node)
        workflow.add_node(UPSIDE_CAPTURE_ENGINE, aggressive_analyst)
        workflow.add_node(PORTFOLIO_FIT_ENGINE, neutral_analyst)
        workflow.add_node(DOWNSIDE_GUARDRAIL_ENGINE, conservative_analyst)
        workflow.add_node(CAPITAL_ALLOCATION_COMMITTEE, portfolio_manager_node)

        # Define edges
        workflow.add_edge(START, "Investment Orchestrator")
        def route_research_phase(state):
            analysis_queue = normalize_selected_analysts(
                state.get("analysis_queue") or state.get("selected_analysts")
            )
            if analysis_queue and (state.get("orchestration_state") or {}).get(
                "continue_research", True
            ):
                return self.RESEARCH_FANOUT
            return THESIS_ENGINE

        workflow.add_conditional_edges(
            "Investment Orchestrator",
            route_research_phase,
            {
                self.RESEARCH_FANOUT: self.RESEARCH_FANOUT,
                THESIS_ENGINE: THESIS_ENGINE,
            },
        )

        def route_parallel_analysts(state):
            queued = normalize_selected_analysts(
                state.get("analysis_queue") or state.get("selected_analysts")
            )
            return [get_analyst_node_name(analyst_key) for analyst_key in queued]

        workflow.add_conditional_edges(
            self.RESEARCH_FANOUT,
            route_parallel_analysts,
            [
                get_analyst_node_name(analyst_type)
                for analyst_type in compiled_analysts
            ],
        )

        for analyst_type in compiled_analysts:
            current_analyst = get_analyst_node_name(analyst_type)
            current_tools = get_analyst_tool_node_name(analyst_type)
            current_clear = get_analyst_clear_node_name(analyst_type)

            # Add conditional edges for current analyst
            workflow.add_conditional_edges(
                current_analyst,
                self.conditional_logic.route_analyst_tools(analyst_type),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)
            workflow.add_conditional_edges(
                current_clear,
                self._route_parallel_join,
                {
                    self.RESEARCH_JOIN: self.RESEARCH_JOIN,
                    END: END,
                },
            )

        workflow.add_edge(self.RESEARCH_JOIN, THESIS_ENGINE)

        # Add remaining edges
        workflow.add_conditional_edges(
            THESIS_ENGINE,
            self.conditional_logic.should_continue_debate,
            {
                CHALLENGE_ENGINE: CHALLENGE_ENGINE,
                INVESTMENT_DIRECTOR: INVESTMENT_DIRECTOR,
            },
        )
        workflow.add_conditional_edges(
            CHALLENGE_ENGINE,
            self.conditional_logic.should_continue_debate,
            {
                THESIS_ENGINE: THESIS_ENGINE,
                INVESTMENT_DIRECTOR: INVESTMENT_DIRECTOR,
            },
        )
        if lean_loop:
            workflow.add_edge(INVESTMENT_DIRECTOR, CAPITAL_ALLOCATION_COMMITTEE)
        else:
            workflow.add_edge(INVESTMENT_DIRECTOR, EXECUTION_ENGINE)
            workflow.add_edge(EXECUTION_ENGINE, UPSIDE_CAPTURE_ENGINE)
            workflow.add_conditional_edges(
                UPSIDE_CAPTURE_ENGINE,
                self.conditional_logic.should_continue_risk_analysis,
                {
                    DOWNSIDE_GUARDRAIL_ENGINE: DOWNSIDE_GUARDRAIL_ENGINE,
                    CAPITAL_ALLOCATION_COMMITTEE: CAPITAL_ALLOCATION_COMMITTEE,
                },
            )
            workflow.add_conditional_edges(
                DOWNSIDE_GUARDRAIL_ENGINE,
                self.conditional_logic.should_continue_risk_analysis,
                {
                    PORTFOLIO_FIT_ENGINE: PORTFOLIO_FIT_ENGINE,
                    CAPITAL_ALLOCATION_COMMITTEE: CAPITAL_ALLOCATION_COMMITTEE,
                },
            )
            workflow.add_conditional_edges(
                PORTFOLIO_FIT_ENGINE,
                self.conditional_logic.should_continue_risk_analysis,
                {
                    UPSIDE_CAPTURE_ENGINE: UPSIDE_CAPTURE_ENGINE,
                    CAPITAL_ALLOCATION_COMMITTEE: CAPITAL_ALLOCATION_COMMITTEE,
                },
            )

        workflow.add_edge(CAPITAL_ALLOCATION_COMMITTEE, END)

        # Compile and return
        return workflow.compile()
