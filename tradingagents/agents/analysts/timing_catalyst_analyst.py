from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_global_news,
    get_insider_transactions,
    get_news,
)
from tradingagents.agents.utils.decision_protocol import (
    TIMING_CATALYST_SECTION_MAP,
    build_dossier_update,
    build_temporal_context_update,
)


def create_timing_catalyst_analyst(llm):
    def timing_catalyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])
        analysis_brief = state.get("analysis_brief", "")

        tools = [
            get_news,
            get_global_news,
            get_insider_transactions,
        ]

        system_message = (
            "You are the Timing & Catalysts capability inside an AI-native investment institution. "
            "Your job is to merge attention, narrative momentum, sentiment change, and the concrete event path "
            "that can force a re-rating. Use get_news(query, start_date, end_date) for company-specific searches, "
            "get_global_news(curr_date, look_back_days, limit) for broader macro and industry flow, and "
            "get_insider_transactions(ticker) when insider activity materially sharpens timing."
            " Write a report with these exact sections: Timing & Catalysts Summary, Attention / Narrative / Sentiment, "
            "Near-Term Catalysts, Re-Rating Path, Timing Risks / Invalidation, and Short-Cycle Execution Window."
            " Keep the report investor-facing: explain what changed, what can change next, and why the window is opening or closing."
            " Separate noisy chatter from usable timing information and end with a Markdown table that summarizes the most decision-relevant signals."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}\n"
                    "Current investment brief:\n{analysis_brief}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)
        prompt = prompt.partial(analysis_brief=analysis_brief)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        output = {
            "messages": [result],
            "timing_catalyst_report": report,
        }
        output.update(
            build_dossier_update(
                state,
                report,
                TIMING_CATALYST_SECTION_MAP,
            )
        )
        output.update(
            build_temporal_context_update(
                state,
                report,
                TIMING_CATALYST_SECTION_MAP,
            )
        )
        return output

    return timing_catalyst_node
