from tradingagents.agents.utils.agent_utils import (
    CHALLENGE_ENGINE,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    CHALLENGE_ENGINE_SECTION_MAP,
    build_dossier_update,
)


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )

        curr_situation = shared_research_context
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are the Challenge Engine inside an AI-native long/short investment institution.

Your job is to attack weak theses before capital is deployed. Do not simulate a generic bear. Produce the strongest disconfirming case.

Write a structured memo using exactly these markdown headings:
## Consensus View
## Counterevidence
## Failure Modes
## Kill Criteria

Guidance:
- Consensus View: Describe what the market likely already believes.
- Counterevidence: Surface evidence that weakens the long thesis or questions the edge.
- Failure Modes: Explain the most likely ways this thesis can break.
- Kill Criteria: State explicit conditions that should force a downgrade or exit.
- Address the latest thesis memo directly where helpful.

Research orchestration plan:
{state.get("analysis_plan", "")}

Cross-functional capability intelligence:
{shared_research_context}

Debate history:
{history}

Latest thesis memo:
{current_response}

Relevant lessons from past situations:
{past_memory_str}
"""

        response = llm.invoke(prompt)

        argument = f"{CHALLENGE_ENGINE}: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "latest_speaker": CHALLENGE_ENGINE,
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        result = {"investment_debate_state": new_investment_debate_state}
        result.update(
            build_dossier_update(
                state,
                response.content,
                CHALLENGE_ENGINE_SECTION_MAP,
            )
        )
        return result

    return bear_node
