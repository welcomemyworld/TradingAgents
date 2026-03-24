from tradingagents.agents.utils.agent_utils import (
    CAPITAL_ALLOCATION_COMMITTEE,
    build_instrument_context,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    CAPITAL_ALLOCATION_SECTION_MAP,
    CAPITAL_ALLOCATION_DOSSIER_BRIEF_KEYS,
    build_final_decision_state_update,
    build_legacy_risk_debate_state,
    build_dossier_update,
    finalize_review_loop,
    render_dossier_brief,
    render_portfolio_context_brief,
    render_temporal_context_brief,
    render_review_transcript,
)


def create_portfolio_manager(llm, memory):
    def portfolio_manager_node(state) -> dict:

        instrument_context = build_instrument_context(state["company_of_interest"])

        allocation_review = state.get("allocation_review", {})
        history = render_review_transcript(allocation_review)
        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )
        execution_state = state.get("execution_state", {})
        thesis_review = state.get("thesis_review", {})
        trader_plan = (
            execution_state.get("full_blueprint")
            or state.get("trader_investment_plan")
            or thesis_review.get("final_memo")
            or state.get("investment_plan", "")
        )
        dossier_snapshot = render_dossier_brief(
            state.get("decision_dossier"),
            CAPITAL_ALLOCATION_DOSSIER_BRIEF_KEYS,
        )
        portfolio_context_snapshot = render_portfolio_context_brief(
            state.get("portfolio_context")
        )
        temporal_context_snapshot = render_temporal_context_brief(
            state.get("temporal_context")
        )
        institution_memory_brief = state.get("institution_memory_brief", "")

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
## Portfolio Mandate
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
- Capability intelligence: {shared_research_context}
- Structured dossier snapshot: {dossier_snapshot}
- Front-loaded portfolio context: {portfolio_context_snapshot}
- Temporal context: {temporal_context_snapshot}
- Institutional memory: {institution_memory_brief}
- Risk review history: {history}

Be decisive and tie every allocation choice to specific evidence. If you override the front-loaded portfolio context, explain why."""

        response = llm.invoke(prompt)
        finalized_review = finalize_review_loop(
            allocation_review,
            CAPITAL_ALLOCATION_COMMITTEE,
            response.content,
            completion_reason="capital_committee_decision",
        )
        updated_final_decision = build_final_decision_state_update(
            state.get("final_decision"),
            response.content,
        )

        result = {
            "allocation_review": finalized_review,
            "risk_debate_state": build_legacy_risk_debate_state(finalized_review),
            "final_decision": updated_final_decision,
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
