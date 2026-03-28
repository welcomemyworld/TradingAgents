from typing import Annotated

from typing_extensions import TypedDict
from langgraph.graph import MessagesState


class ReviewTurn(TypedDict):
    stage: Annotated[str, "Stable stage key inside a review loop"]
    agent: Annotated[str, "Institutional engine that produced the turn"]
    content: Annotated[str, "Rendered memo for the turn"]


class ReviewLoopState(TypedDict):
    stage_order: Annotated[list[str], "Ordered review stages inside the loop"]
    active_stage: Annotated[str, "Current engine active in the loop"]
    round_index: Annotated[int, "Number of completed review turns"]
    transcript: Annotated[list[ReviewTurn], "Ordered review transcript"]
    outputs: Annotated[dict[str, str], "Latest memo per review stage"]
    final_memo: Annotated[str, "Final synthesis memo for the loop"]
    completion_reason: Annotated[str, "Why the loop ended"]


class ExecutionState(TypedDict):
    full_blueprint: Annotated[str, "Full execution memo produced by the Execution Engine"]
    execution_plan: Annotated[str, "Execution plan section"]
    entry_framework: Annotated[str, "Entry framework section"]
    position_construction: Annotated[str, "Position construction section"]
    liquidity_plan: Annotated[str, "Liquidity plan section"]
    monitoring_plan: Annotated[str, "Monitoring plan section"]


class FinalDecisionState(TypedDict):
    full_decision: Annotated[str, "Full capital allocation memo"]
    rating: Annotated[str, "Rating section"]
    portfolio_mandate: Annotated[str, "Portfolio mandate section"]
    position_size: Annotated[str, "Position size section"]
    entry_exit: Annotated[str, "Entry and exit section"]
    kill_criteria: Annotated[str, "Kill criteria section"]
    monitoring_triggers: Annotated[str, "Monitoring triggers section"]
    capital_allocation_rationale: Annotated[str, "Capital allocation rationale section"]


class OrchestrationState(TypedDict):
    token_budget: Annotated[str, "Current research token budget posture"]
    position_importance: Annotated[str, "How important this potential position is"]
    uncertainty_level: Annotated[str, "Current uncertainty assessment"]
    evidence_conflict_level: Annotated[str, "Current evidence conflict assessment"]
    continue_research: Annotated[bool, "Whether to continue capability research"]
    stop_reason: Annotated[str, "Why research should stop or continue"]
    add_capabilities: Annotated[list[str], "Reserve capabilities added by the orchestrator"]
    active_capabilities: Annotated[list[str], "Capabilities currently activated for this run"]
    reserve_capabilities: Annotated[list[str], "Capabilities available but not yet activated"]
    trigger_counterevidence_search: Annotated[
        bool, "Whether downstream counterevidence search should intensify"
    ]
    counterevidence_focus: Annotated[
        str, "Specific focus area for downstream challenge or disconfirming work"
    ]
    research_mode: Annotated[
        str, "How the research front-end is being executed, e.g. parallel_hard_loop"
    ]
    missing_capabilities: Annotated[
        list[str], "Capabilities that did not produce a completed report before synthesis"
    ]


class PortfolioContextState(TypedDict):
    full_context: Annotated[str, "Rendered portfolio-context memo produced early in the run"]
    portfolio_role: Annotated[str, "What role the position should play inside the portfolio"]
    position_archetype: Annotated[str, "What type of position this is: alpha, hedge, event, duration, etc."]
    book_correlation_view: Annotated[str, "Expected correlation and factor overlap with the current book"]
    crowding_risk: Annotated[str, "Assessment of crowding or consensus overlap risk"]
    capital_budget: Annotated[str, "Initial capital budget hypothesis for the seat"]
    risk_budget: Annotated[str, "Initial risk budget hypothesis for the seat"]


class TemporalContextState(TypedDict):
    full_context: Annotated[str, "Rendered temporal-context memo across long, medium, and short horizons"]
    long_cycle_mispricing: Annotated[str, "Long-cycle mispricing view anchored in durable business reality"]
    medium_cycle_rerating_path: Annotated[str, "Medium-cycle re-rating path through catalysts and expectation change"]
    short_cycle_execution_window: Annotated[str, "Short-cycle execution window for timing, tape, and sentiment"]


# Legacy compatibility state retained during migration
class InvestDebateState(TypedDict):
    bull_history: Annotated[str, "Legacy thesis history"]
    bear_history: Annotated[str, "Legacy challenge history"]
    history: Annotated[str, "Legacy combined review history"]
    latest_speaker: Annotated[str, "Last investment review agent that spoke"]
    current_response: Annotated[str, "Latest review response"]
    judge_decision: Annotated[str, "Final investment memo"]
    count: Annotated[int, "Length of the legacy conversation"]


class RiskDebateState(TypedDict):
    aggressive_history: Annotated[str, "Legacy upside capture history"]
    conservative_history: Annotated[str, "Legacy downside guardrail history"]
    neutral_history: Annotated[str, "Legacy portfolio fit history"]
    history: Annotated[str, "Legacy combined allocation review history"]
    latest_speaker: Annotated[str, "Last allocation review engine that spoke"]
    current_aggressive_response: Annotated[str, "Latest upside capture response"]
    current_conservative_response: Annotated[str, "Latest downside guardrail response"]
    current_neutral_response: Annotated[str, "Latest portfolio fit response"]
    judge_decision: Annotated[str, "Final capital allocation memo"]
    count: Annotated[int, "Length of the legacy allocation conversation"]


class AgentState(MessagesState):
    company_of_interest: Annotated[str, "Company that we are interested in trading"]
    trade_date: Annotated[str, "What date we are trading at"]
    sender: Annotated[str, "Agent that sent this message"]

    selected_analysts: Annotated[list[str], "Research capabilities selected for this run"]
    analysis_queue: Annotated[list[str], "Remaining research capabilities in planned order"]
    completed_analysts: Annotated[list[str], "Research capabilities that have finished"]
    current_analyst: Annotated[str, "Current research capability being executed"]
    analysis_plan: Annotated[str, "Cross-functional research plan created by the orchestrator"]
    analysis_brief: Annotated[str, "Current investment brief shared across the capability stack"]
    analysis_artifacts: Annotated[
        dict[str, dict[str, str]], "Capability-level report artifacts for downstream use"
    ]
    orchestration_journal: Annotated[list[str], "Routing log produced by the orchestrator"]
    orchestration_state: Annotated[
        OrchestrationState, "Institution-level orchestration controls and stop rules"
    ]
    portfolio_context: Annotated[
        PortfolioContextState,
        "Front-loaded portfolio mandate and risk context produced before full synthesis",
    ]
    temporal_context: Annotated[
        TemporalContextState,
        "Explicit long/medium/short horizon split to keep mispricing, re-rating, and execution windows distinct",
    ]
    institution_memory_snapshot: Annotated[
        dict[str, object], "Persistent institutional memory snapshot loaded before the run"
    ]
    institution_memory_brief: Annotated[
        str, "Condensed institutional memory brief shared across the workflow"
    ]
    decision_dossier: Annotated[
        dict[str, str], "Structured investment dossier accumulated across the workflow"
    ]
    decision_dossier_markdown: Annotated[
        str, "Rendered markdown version of the structured investment dossier"
    ]

    market_expectations_report: Annotated[str, "Report from the Market Expectations capability"]
    timing_catalyst_report: Annotated[
        str, "Report from the merged Timing & Catalysts capability"
    ]
    why_now_report: Annotated[str, "Legacy report slot retained for compatibility"]
    catalyst_path_report: Annotated[str, "Legacy report slot retained for compatibility"]
    business_truth_report: Annotated[str, "Report from the Business Truth capability"]

    thesis_review: Annotated[
        ReviewLoopState, "Unified thesis review loop state shared by thesis/challenge/director"
    ]
    execution_state: Annotated[
        ExecutionState, "Unified execution state shared by downstream capital review"
    ]
    allocation_review: Annotated[
        ReviewLoopState,
        "Unified allocation review loop state shared by upside/downside/portfolio fit engines",
    ]
    final_decision: Annotated[
        FinalDecisionState, "Structured final capital allocation decision"
    ]

    # Legacy compatibility fields retained until downstream surfaces fully migrate.
    investment_debate_state: Annotated[
        InvestDebateState, "Legacy thesis debate state"
    ]
    investment_plan: Annotated[str, "Legacy memo generated by the Investment Director"]
    trader_investment_plan: Annotated[
        str, "Legacy execution blueprint generated by the Execution Engine"
    ]
    risk_debate_state: Annotated[
        RiskDebateState, "Legacy allocation review state"
    ]
    final_trade_decision: Annotated[str, "Legacy final capital allocation decision"]
