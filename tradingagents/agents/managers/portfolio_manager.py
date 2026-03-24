from tradingagents.agents.utils.agent_utils import (
    CAPITAL_ALLOCATION_COMMITTEE,
    build_instrument_context,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    CAPITAL_ALLOCATION_SECTION_MAP,
    build_dossier_update,
)


def create_portfolio_manager(llm, memory):
    def portfolio_manager_node(state) -> dict:

        instrument_context = build_instrument_context(state["company_of_interest"])

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )
        trader_plan = state["trader_investment_plan"] or state["investment_plan"]

        curr_situation = shared_research_context
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are the Capital Allocation Committee for an AI-native investment institution.

Your job is to convert the accumulated dossier into a final capital allocation decision.

{instrument_context}

---

Write exactly these markdown headings:
## Rating
## Position Size
## Entry / Exit
## Kill Criteria
## Monitoring Triggers
## Capital Allocation Rationale

Rating must be exactly one of: Buy, Overweight, Hold, Underweight, Sell.

Context:
- Execution blueprint: {trader_plan}
- Lessons from past decisions: {past_memory_str}
- Research orchestration plan: {state.get("analysis_plan", "")}
- Analyst intelligence: {shared_research_context}
- Risk review history: {history}

Be decisive and tie every allocation choice to specific evidence."""

        response = llm.invoke(prompt)

        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": CAPITAL_ALLOCATION_COMMITTEE,
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        result = {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }
        result.update(
            build_dossier_update(
                state,
                response.content,
                CAPITAL_ALLOCATION_SECTION_MAP,
            )
        )
        return result
    return portfolio_manager_node
