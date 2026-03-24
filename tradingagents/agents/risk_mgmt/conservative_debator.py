from tradingagents.agents.utils.agent_utils import (
    DOWNSIDE_GUARDRAIL_ENGINE,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    DOWNSIDE_GUARDRAIL_SECTION_MAP,
    build_dossier_update,
)


def create_conservative_debator(llm):
    def conservative_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        conservative_history = risk_debate_state.get("conservative_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )

        trader_decision = state["trader_investment_plan"]

        prompt = f"""You are the Downside Guardrail Engine.

Your job is to define what must be true for the fund to stay in the trade and what limits protect capital if the thesis degrades.

Write exactly these markdown headings:
## Downside Map
## Hard Limits
## Kill Criteria

Inputs:
- Execution blueprint: {trader_decision}
- Research orchestration plan: {state.get("analysis_plan", "")}
- Analyst intelligence: {shared_research_context}
- Risk review history: {history}
- Latest upside capture memo: {current_aggressive_response}
- Latest portfolio fit memo: {current_neutral_response}
"""

        response = llm.invoke(prompt)

        argument = f"{DOWNSIDE_GUARDRAIL_ENGINE}: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": conservative_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": DOWNSIDE_GUARDRAIL_ENGINE,
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        result = {"risk_debate_state": new_risk_debate_state}
        result.update(
            build_dossier_update(
                state,
                response.content,
                DOWNSIDE_GUARDRAIL_SECTION_MAP,
            )
        )
        return result

    return conservative_node
