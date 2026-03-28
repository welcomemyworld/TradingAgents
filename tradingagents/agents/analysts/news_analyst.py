from tradingagents.agents.analysts.timing_catalyst_analyst import (
    create_timing_catalyst_analyst,
)


def create_news_analyst(llm):
    """Backward-compatible alias for the merged Timing & Catalysts capability."""
    return create_timing_catalyst_analyst(llm)
