# TradingAgents/graph/conditional_logic.py

from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import (
    CAPITAL_ALLOCATION_COMMITTEE,
    CHALLENGE_ENGINE,
    DOWNSIDE_GUARDRAIL_ENGINE,
    INVESTMENT_DIRECTOR,
    PORTFOLIO_FIT_ENGINE,
    THESIS_ENGINE,
    UPSIDE_CAPTURE_ENGINE,
    get_analyst_clear_node_name,
    get_analyst_node_name,
    get_analyst_tool_node_name,
)


class ConditionalLogic:
    """Handles conditional logic for determining graph flow."""

    def __init__(self, max_debate_rounds=1, max_risk_discuss_rounds=1):
        """Initialize with configuration parameters."""
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def route_analyst_tools(self, analyst_key: str):
        """Build a router that decides whether a capability should use tools again."""

        def _router(state: AgentState):
            messages = state["messages"]
            last_message = messages[-1]
            if last_message.tool_calls:
                return get_analyst_tool_node_name(analyst_key)
            return get_analyst_clear_node_name(analyst_key)

        return _router

    def route_next_analyst(self, state: AgentState) -> str:
        """Route from the orchestrator to the next analyst or research team."""
        current_analyst = state.get("current_analyst", "")
        if current_analyst:
            return get_analyst_node_name(current_analyst)
        return THESIS_ENGINE

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue."""

        if (
            state["investment_debate_state"]["count"] >= 2 * self.max_debate_rounds
        ):  # 3 rounds of back-and-forth between 2 agents
            return INVESTMENT_DIRECTOR
        if state["investment_debate_state"].get("latest_speaker") == THESIS_ENGINE:
            return CHALLENGE_ENGINE
        return THESIS_ENGINE

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """Determine if risk analysis should continue."""
        if (
            state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds
        ):  # 3 rounds of back-and-forth between 3 agents
            return CAPITAL_ALLOCATION_COMMITTEE
        if state["risk_debate_state"]["latest_speaker"] == UPSIDE_CAPTURE_ENGINE:
            return DOWNSIDE_GUARDRAIL_ENGINE
        if state["risk_debate_state"]["latest_speaker"] == DOWNSIDE_GUARDRAIL_ENGINE:
            return PORTFOLIO_FIT_ENGINE
        return UPSIDE_CAPTURE_ENGINE
