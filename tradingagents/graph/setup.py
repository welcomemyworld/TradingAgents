# TradingAgents/graph/setup.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import (
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
    get_report_field_for_analyst,
    get_analyst_tool_node_name,
    normalize_selected_analysts,
)

from .conditional_logic import ConditionalLogic


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

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
        """Persist analyst outputs into the shared artifact store."""
        report_field = get_report_field_for_analyst(analyst_key)

        def wrapped_node(state):
            result = node(state)
            report = result.get(report_field, "")

            if not report:
                return result

            artifacts = dict(state.get("analysis_artifacts", {}))
            artifacts[analyst_key] = {
                "agent_name": get_analyst_node_name(analyst_key),
                "report": report,
                "report_field": report_field,
            }

            completed = list(state.get("completed_analysts", []))
            if analyst_key not in completed:
                completed.append(analyst_key)

            remaining = [key for key in state.get("analysis_queue", []) if key != analyst_key]

            result.update(
                {
                    "analysis_artifacts": artifacts,
                    "completed_analysts": completed,
                    "analysis_queue": remaining,
                    "current_analyst": "",
                }
            )
            return result

        return wrapped_node

    def setup_graph(
        self, selected_analysts=None
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of capability ids to include. Options are:
                - "market_expectations"
                - "why_now"
                - "catalyst_path"
                - "business_truth"
        """
        selected_analysts = normalize_selected_analysts(
            selected_analysts or ANALYST_ORDER
        )

        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no capabilities selected!")

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        analyst_factories = {
            "market_expectations": create_market_analyst,
            "why_now": create_social_media_analyst,
            "catalyst_path": create_news_analyst,
            "business_truth": create_fundamentals_analyst,
        }

        for analyst_key in selected_analysts:
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
        workflow.add_conditional_edges(
            "Investment Orchestrator",
            self.conditional_logic.route_next_analyst,
            {
                get_analyst_node_name(analyst_type): get_analyst_node_name(analyst_type)
                for analyst_type in selected_analysts
            }
            | {THESIS_ENGINE: THESIS_ENGINE},
        )

        # Analysts are now dynamically re-routed after each completion.
        for analyst_type in selected_analysts:
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
            workflow.add_edge(current_clear, "Investment Orchestrator")

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
