from tradingagents.agents.utils.agent_utils import (
    PORTFOLIO_FIT_ENGINE,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    PORTFOLIO_FIT_SECTION_MAP,
    build_dossier_update,
)


def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_conservative_response = risk_debate_state.get("current_conservative_response", "")

        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )

        trader_decision = state["trader_investment_plan"]

        prompt = f"""You are the Portfolio Fit Engine.

Your job is to judge how this trade belongs inside a real portfolio rather than in isolation.

Write exactly these markdown headings:
## Portfolio Fit
## Correlation / Crowding
## Capital Budget

Inputs:
- Execution blueprint: {trader_decision}
- Research orchestration plan: {state.get("analysis_plan", "")}
- Analyst intelligence: {shared_research_context}
- Risk review history: {history}
- Latest upside capture memo: {current_aggressive_response}
- Latest downside guardrail memo: {current_conservative_response}
"""

        response = llm.invoke(prompt)

        argument = f"{PORTFOLIO_FIT_ENGINE}: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": PORTFOLIO_FIT_ENGINE,
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        result = {"risk_debate_state": new_risk_debate_state}
        result.update(
            build_dossier_update(
                state,
                response.content,
                PORTFOLIO_FIT_SECTION_MAP,
            )
        )
        return result

    return neutral_node
