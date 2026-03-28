from tradingagents.agents.utils.agent_utils import (
    CHALLENGE_ENGINE,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    CHALLENGE_STAGE_KEY,
    CHALLENGE_ENGINE_SECTION_MAP,
    THESIS_STAGE_KEY,
    append_review_stage_output,
    build_legacy_investment_debate_state,
    build_dossier_update,
    get_review_output,
    render_review_transcript,
)


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        thesis_review = state.get("thesis_review", {})
        history = render_review_transcript(thesis_review)
        current_response = get_review_output(thesis_review, THESIS_STAGE_KEY)
        orchestration_state = state.get("orchestration_state", {})
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
- If counterevidence search has been intensified by the orchestrator, prioritize the named weak spot and push harder than usual on disconfirming evidence.

Research orchestration plan:
{state.get("analysis_plan", "")}

Orchestration controls:
- Counterevidence search: {"intensified" if orchestration_state.get("trigger_counterevidence_search") else "standard"}
- Counterevidence focus: {orchestration_state.get("counterevidence_focus") or "Challenge the weakest assumptions in the current thesis."}
- Evidence conflict: {orchestration_state.get("evidence_conflict_level", "medium")}
- Uncertainty: {orchestration_state.get("uncertainty_level", "medium")}

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
        updated_review = append_review_stage_output(
            thesis_review,
            CHALLENGE_STAGE_KEY,
            CHALLENGE_ENGINE,
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
                CHALLENGE_ENGINE_SECTION_MAP,
            )
        )
        return result

    return bear_node
