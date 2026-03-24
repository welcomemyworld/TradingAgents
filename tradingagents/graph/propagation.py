# TradingAgents/graph/propagation.py

from typing import Dict, Any, List, Optional
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.agents.utils.agent_utils import normalize_selected_analysts


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self, company_name: str, trade_date: str, selected_analysts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create the initial state for the agent graph."""
        normalized_analysts = normalize_selected_analysts(selected_analysts)
        return {
            "messages": [("human", company_name)],
            "company_of_interest": company_name,
            "trade_date": str(trade_date),
            "selected_analysts": normalized_analysts,
            "analysis_queue": normalized_analysts.copy(),
            "completed_analysts": [],
            "current_analyst": "",
            "analysis_plan": "",
            "analysis_brief": "",
            "analysis_artifacts": {},
            "orchestration_journal": [],
            "decision_dossier": {},
            "decision_dossier_markdown": "",
            "investment_debate_state": InvestDebateState(
                {
                    "bull_history": "",
                    "bear_history": "",
                    "history": "",
                    "latest_speaker": "",
                    "current_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "risk_debate_state": RiskDebateState(
                {
                    "aggressive_history": "",
                    "conservative_history": "",
                    "neutral_history": "",
                    "history": "",
                    "latest_speaker": "",
                    "current_aggressive_response": "",
                    "current_conservative_response": "",
                    "current_neutral_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "market_expectations_report": "",
            "business_truth_report": "",
            "why_now_report": "",
            "catalyst_path_report": "",
            "investment_plan": "",
            "trader_investment_plan": "",
            "final_trade_decision": "",
        }

    def get_graph_args(self, callbacks: Optional[List] = None) -> Dict[str, Any]:
        """Get arguments for the graph invocation.

        Args:
            callbacks: Optional list of callback handlers for tool execution tracking.
                       Note: LLM callbacks are handled separately via LLM constructor.
        """
        config = {"recursion_limit": self.max_recur_limit}
        if callbacks:
            config["callbacks"] = callbacks
        return {
            "stream_mode": "values",
            "config": config,
        }
