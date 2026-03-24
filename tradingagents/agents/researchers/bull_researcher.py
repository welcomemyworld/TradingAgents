from tradingagents.agents.utils.agent_utils import (
    THESIS_ENGINE,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    CHALLENGE_STAGE_KEY,
    THESIS_STAGE_KEY,
    THESIS_ENGINE_SECTION_MAP,
    append_review_stage_output,
    build_legacy_investment_debate_state,
    build_dossier_update,
    get_review_output,
    render_review_transcript,
)


def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        thesis_review = state.get("thesis_review", {})
        history = render_review_transcript(thesis_review)
        current_response = get_review_output(thesis_review, CHALLENGE_STAGE_KEY)
        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )

        curr_situation = shared_research_context
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are the Thesis Engine inside an AI-native long/short investment institution.

Your job is not to roleplay a person. Your job is to build the strongest investable upside case that combines deep business understanding with monetizable market insight.

Write a structured memo using exactly these markdown headings:
## Core Thesis
## Variant Perception
## Supporting Evidence
## Catalyst Path

Guidance:
- Core Thesis: State the highest-conviction reason this company can outperform or rerate.
- Variant Perception: Explain what the market is likely misunderstanding or underpricing.
- Supporting Evidence: Use the capability intelligence to make the case with specifics.
- Catalyst Path: Explain why this thesis can matter on a tradable time horizon.
- Address the latest challenge directly where relevant.
- Be decisive, specific, and investment-oriented.

Research orchestration plan:
{state.get("analysis_plan", "")}

Cross-functional capability intelligence:
{shared_research_context}

Debate history:
{history}

Latest challenge:
{current_response}

Relevant lessons from past situations:
{past_memory_str}
"""

        response = llm.invoke(prompt)
        updated_review = append_review_stage_output(
            thesis_review,
            THESIS_STAGE_KEY,
            THESIS_ENGINE,
            response.content,
        )

        result = {
            "thesis_review": updated_review,
            "investment_debate_state": build_legacy_investment_debate_state(
                updated_review
            ),
        }
        result.update(
            build_dossier_update(
                state,
                response.content,
                THESIS_ENGINE_SECTION_MAP,
            )
        )
        return result

    return bull_node
