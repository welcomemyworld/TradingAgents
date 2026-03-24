from tradingagents.agents.utils.agent_utils import (
    INVESTMENT_DIRECTOR,
    build_instrument_context,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    INVESTMENT_DIRECTOR_SECTION_MAP,
    build_dossier_update,
    render_dossier_brief,
    RESEARCH_DOSSIER_BRIEF_KEYS,
)


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["investment_debate_state"].get("history", "")
        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )

        investment_debate_state = state["investment_debate_state"]
        dossier_snapshot = render_dossier_brief(
            state.get("decision_dossier"),
            RESEARCH_DOSSIER_BRIEF_KEYS,
        )

        curr_situation = shared_research_context
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are the Investment Director for an AI-native long/short platform.

Your job is to synthesize the thesis and challenge engines into an investable research memo that can be handed to execution and capital allocation.

Write the memo using exactly these markdown headings:
## World Model
## Recommended Stance
## Mispricing Narrative
## What The Market Is Missing
## Evidence That Matters
## Catalyst Path
## Time Horizon
## Portfolio Role
## Initial Sizing View
## Kill Criteria

Rules:
- Take a stand. Do not hide behind balance.
- Translate debate into a clear institutional recommendation.
- Focus on what is both true and tradable.
- Use past lessons where relevant.

Past reflections:
\"{past_memory_str}\"

{instrument_context}

Cross-functional research brief:
{state.get("analysis_plan", "")}

Completed capability intelligence:
{shared_research_context}

Structured dossier snapshot:
{dossier_snapshot}

Structured debate history:
{history}"""
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "latest_speaker": INVESTMENT_DIRECTOR,
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        result = {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }
        result.update(
            build_dossier_update(
                state,
                response.content,
                INVESTMENT_DIRECTOR_SECTION_MAP,
            )
        )
        return result
    return research_manager_node
