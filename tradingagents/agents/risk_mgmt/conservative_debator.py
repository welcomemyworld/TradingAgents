from tradingagents.agents.utils.agent_utils import (
    DOWNSIDE_GUARDRAIL_ENGINE,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    DOWNSIDE_STAGE_KEY,
    DOWNSIDE_GUARDRAIL_SECTION_MAP,
    PORTFOLIO_FIT_STAGE_KEY,
    RISK_DOSSIER_BRIEF_KEYS,
    UPSIDE_STAGE_KEY,
    append_review_stage_output,
    build_legacy_risk_debate_state,
    build_dossier_update,
    get_review_output,
    render_dossier_brief,
    render_portfolio_context_brief,
    render_temporal_context_brief,
    render_review_transcript,
)


def create_conservative_debator(llm):
    def conservative_node(state) -> dict:
        allocation_review = state.get("allocation_review", {})
        history = render_review_transcript(allocation_review)
        current_aggressive_response = get_review_output(
            allocation_review, UPSIDE_STAGE_KEY
        )
        current_neutral_response = get_review_output(
            allocation_review, PORTFOLIO_FIT_STAGE_KEY
        )

        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )
        dossier_snapshot = render_dossier_brief(
            state.get("decision_dossier"),
            RISK_DOSSIER_BRIEF_KEYS,
        )
        portfolio_context_snapshot = render_portfolio_context_brief(
            state.get("portfolio_context")
        )
        temporal_context_snapshot = render_temporal_context_brief(
            state.get("temporal_context")
        )

        execution_state = state.get("execution_state", {})
        trader_decision = execution_state.get("full_blueprint") or state.get(
            "trader_investment_plan", ""
        )

        prompt = f"""You are the Downside Guardrail Engine.

Your job is to define what must be true for the fund to stay in the trade and what limits protect capital if the thesis degrades.

Write exactly these markdown headings:
## Downside Map
## Hard Limits
## Kill Criteria
## Scenario Map

Inputs:
- Execution blueprint: {trader_decision}
- Research orchestration plan: {state.get("analysis_plan", "")}
- Capability intelligence: {shared_research_context}
- Structured dossier snapshot: {dossier_snapshot}
- Front-loaded portfolio context: {portfolio_context_snapshot}
- Temporal context: {temporal_context_snapshot}
- Risk review history: {history}
- Latest upside capture memo: {current_aggressive_response}
- Latest portfolio fit memo: {current_neutral_response}
"""

        response = llm.invoke(prompt)
        updated_review = append_review_stage_output(
            allocation_review,
            DOWNSIDE_STAGE_KEY,
            DOWNSIDE_GUARDRAIL_ENGINE,
            response.content,
        )

        result = {
            "allocation_review": updated_review,
            "risk_debate_state": build_legacy_risk_debate_state(updated_review),
        }
        result.update(
            build_dossier_update(
                state,
                response.content,
                DOWNSIDE_GUARDRAIL_SECTION_MAP,
            )
        )
        return result

    return conservative_node
