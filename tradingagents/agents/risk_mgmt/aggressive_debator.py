from tradingagents.agents.utils.agent_utils import (
    UPSIDE_CAPTURE_ENGINE,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    DOWNSIDE_STAGE_KEY,
    PORTFOLIO_FIT_STAGE_KEY,
    RISK_DOSSIER_BRIEF_KEYS,
    UPSIDE_STAGE_KEY,
    UPSIDE_CAPTURE_SECTION_MAP,
    append_review_stage_output,
    build_legacy_risk_debate_state,
    build_dossier_update,
    get_review_output,
    render_dossier_brief,
    render_portfolio_context_brief,
    render_temporal_context_brief,
    render_review_transcript,
)


def create_aggressive_debator(llm):
    def aggressive_node(state) -> dict:
        allocation_review = state.get("allocation_review", {})
        history = render_review_transcript(allocation_review)
        current_conservative_response = get_review_output(
            allocation_review, DOWNSIDE_STAGE_KEY
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

        prompt = f"""You are the Upside Capture Engine.

Your mandate is to protect the fund from under-sizing great ideas. Look for the best way to express upside if the thesis is right.

Write exactly these markdown headings:
## Upside Capture
## If Right, Press Here
## Asymmetric Expressions

Inputs:
- Execution blueprint: {trader_decision}
- Research orchestration plan: {state.get("analysis_plan", "")}
- Capability intelligence: {shared_research_context}
- Structured dossier snapshot: {dossier_snapshot}
- Front-loaded portfolio context: {portfolio_context_snapshot}
- Temporal context: {temporal_context_snapshot}
- Risk review history: {history}
- Latest downside guardrail memo: {current_conservative_response}
- Latest portfolio fit memo: {current_neutral_response}
"""

        response = llm.invoke(prompt)
        updated_review = append_review_stage_output(
            allocation_review,
            UPSIDE_STAGE_KEY,
            UPSIDE_CAPTURE_ENGINE,
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
                UPSIDE_CAPTURE_SECTION_MAP,
            )
        )
        return result

    return aggressive_node
