from tradingagents.agents.utils.agent_utils import (
    INVESTMENT_DIRECTOR,
    build_instrument_context,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    INVESTMENT_DIRECTOR_SECTION_MAP,
    build_legacy_investment_debate_state,
    build_dossier_update,
    finalize_review_loop,
    render_dossier_brief,
    render_portfolio_context_brief,
    render_temporal_context_brief,
    render_review_transcript,
    RESEARCH_DOSSIER_BRIEF_KEYS,
)


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])
        thesis_review = state.get("thesis_review", {})
        history = render_review_transcript(thesis_review)
        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )
        missing_capabilities = (
            (state.get("orchestration_state") or {}).get("missing_capabilities") or []
        )

        dossier_snapshot = render_dossier_brief(
            state.get("decision_dossier"),
            RESEARCH_DOSSIER_BRIEF_KEYS,
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

        prompt = f"""You are the Investment Director for an AI-native long/short platform.

Your job is to synthesize the thesis and challenge engines into an investable research memo that can be handed to execution and capital allocation.

Write the memo using exactly these markdown headings:
## World Model
## Recommended Stance
## Mispricing Narrative
## What The Market Is Missing
## Evidence That Matters
## Long-Cycle Mispricing
## Medium-Cycle Re-Rating Path
## Short-Cycle Execution Window
## Timing & Catalysts
## Time Horizon
## Portfolio Role
## Initial Sizing View
## Kill Criteria

Rules:
- Take a stand. Do not hide behind balance.
- Translate debate into a clear institutional recommendation.
- Focus on what is both true and tradable.
- Use past lessons where relevant.
- If any research capability is missing, name the gap explicitly, lower confidence accordingly, and state the next evidence that would close it.

Past reflections:
\"{past_memory_str}\"

{instrument_context}

Cross-functional research brief:
{state.get("analysis_plan", "")}

Completed capability intelligence:
{shared_research_context}

Missing capability evidence:
{", ".join(missing_capabilities) if missing_capabilities else "None"}

Structured dossier snapshot:
{dossier_snapshot}

Front-loaded portfolio context:
{portfolio_context_snapshot}

Temporal context:
{temporal_context_snapshot}

Institutional memory:
{institution_memory_brief}

Structured debate history:
{history}"""
        response = llm.invoke(prompt)

        finalized_review = finalize_review_loop(
            thesis_review,
            INVESTMENT_DIRECTOR,
            response.content,
            completion_reason="director_synthesis",
        )

        result = {
            "thesis_review": finalized_review,
            "investment_debate_state": build_legacy_investment_debate_state(
                finalized_review
            ),
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
