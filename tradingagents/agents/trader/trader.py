import functools

from tradingagents.agents.utils.agent_utils import (
    EXECUTION_ENGINE,
    build_instrument_context,
    build_research_context,
)
from tradingagents.agents.utils.decision_protocol import (
    EXECUTION_ENGINE_SECTION_MAP,
    EXECUTION_DOSSIER_BRIEF_KEYS,
    build_execution_state_update,
    build_dossier_update,
    render_dossier_brief,
    render_portfolio_context_brief,
    render_temporal_context_brief,
)


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        instrument_context = build_instrument_context(company_name)
        thesis_review = state.get("thesis_review", {})
        investment_plan = (
            thesis_review.get("final_memo")
            or state.get("investment_plan", "")
        )
        shared_research_context = build_research_context(
            state, state.get("selected_analysts")
        )
        dossier_snapshot = render_dossier_brief(
            state.get("decision_dossier"),
            EXECUTION_DOSSIER_BRIEF_KEYS,
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
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a research capability stack, here is an investment plan tailored for {company_name}. {instrument_context} This plan incorporates deep business understanding together with faster catalysts and market timing signals. Use this plan as a foundation for evaluating your next trading decision.\n\nCross-functional research brief:\n{state.get('analysis_plan', '')}\n\nCompleted capability intelligence:\n{shared_research_context}\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
        }

        messages = [
            {
                "role": "system",
                "content": f"""You are the Execution Engine inside an AI-native investment institution.

Turn the research memo into a practical execution blueprint. Use exactly these markdown headings:
## Execution Plan
## Entry Framework
## Position Construction
## Liquidity Plan
## Monitoring Plan

End the memo with a single line in the form: FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**

Apply lessons from past decisions to strengthen your analysis. Relevant reflections: {past_memory_str}

Structured dossier snapshot:
{dossier_snapshot}

Front-loaded portfolio context:
{portfolio_context_snapshot}

Temporal context:
{temporal_context_snapshot}

Institutional memory:
{institution_memory_brief}""",
            },
            context,
        ]

        result = llm.invoke(messages)
        updated_execution_state = build_execution_state_update(
            state.get("execution_state"),
            result.content,
        )

        output = {
            "messages": [result],
            "execution_state": updated_execution_state,
            "trader_investment_plan": result.content,
            "sender": name,
        }
        output.update(
            build_dossier_update(
                state,
                result.content,
                EXECUTION_ENGINE_SECTION_MAP,
            )
        )
        return output

    return functools.partial(trader_node, name=EXECUTION_ENGINE)
