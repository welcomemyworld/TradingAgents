from tradingagents.agents.utils.agent_utils import (
    UPSIDE_CAPTURE_ENGINE,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    RISK_DOSSIER_BRIEF_KEYS,
    UPSIDE_CAPTURE_SECTION_MAP,
    build_dossier_update,
    render_dossier_brief,
)


def create_aggressive_debator(llm):
    def aggressive_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        aggressive_history = risk_debate_state.get("aggressive_history", "")

        current_conservative_response = risk_debate_state.get("current_conservative_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )
        dossier_snapshot = render_dossier_brief(
            state.get("decision_dossier"),
            RISK_DOSSIER_BRIEF_KEYS,
        )

        trader_decision = state["trader_investment_plan"]

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
- Risk review history: {history}
- Latest downside guardrail memo: {current_conservative_response}
- Latest portfolio fit memo: {current_neutral_response}
"""

        response = llm.invoke(prompt)

        argument = f"{UPSIDE_CAPTURE_ENGINE}: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": aggressive_history + "\n" + argument,
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": UPSIDE_CAPTURE_ENGINE,
            "current_aggressive_response": argument,
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
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
                UPSIDE_CAPTURE_SECTION_MAP,
            )
        )
        return result

    return aggressive_node
