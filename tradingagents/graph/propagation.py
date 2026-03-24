# TradingAgents/graph/propagation.py

from typing import Dict, Any, List, Optional
from tradingagents.agents.utils.agent_states import (
    AgentState,
)
from tradingagents.agents.utils.agent_utils import normalize_selected_analysts
from tradingagents.agents.utils.decision_protocol import (
    ALLOCATION_REVIEW_STAGE_ORDER,
    THESIS_REVIEW_STAGE_ORDER,
    build_legacy_investment_debate_state,
    build_legacy_risk_debate_state,
    create_execution_state,
    create_final_decision_state,
    create_orchestration_state,
    create_portfolio_context_state,
    create_temporal_context_state,
    create_review_loop_state,
)


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
            "orchestration_state": create_orchestration_state(),
            "portfolio_context": create_portfolio_context_state(),
            "temporal_context": create_temporal_context_state(),
            "institution_memory_snapshot": {},
            "institution_memory_brief": "",
            "decision_dossier": {},
            "decision_dossier_markdown": "",
            "thesis_review": create_review_loop_state(THESIS_REVIEW_STAGE_ORDER),
            "execution_state": create_execution_state(),
            "allocation_review": create_review_loop_state(ALLOCATION_REVIEW_STAGE_ORDER),
            "final_decision": create_final_decision_state(),
            "investment_debate_state": build_legacy_investment_debate_state(
                create_review_loop_state(THESIS_REVIEW_STAGE_ORDER)
            ),
            "risk_debate_state": build_legacy_risk_debate_state(
                create_review_loop_state(ALLOCATION_REVIEW_STAGE_ORDER)
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
