from io import StringIO
import tempfile
import unittest
from pathlib import Path

from rich.console import Console

from cli.main import (
    build_report_sections_map,
    create_launch_brief_panel,
    save_report_to_disk,
)
from tradingagents.agents.utils.agent_utils import (
    DOWNSIDE_GUARDRAIL_ENGINE,
    INVESTMENT_DIRECTOR,
    PORTFOLIO_FIT_ENGINE,
    THESIS_ENGINE,
    UPSIDE_CAPTURE_ENGINE,
)
from tradingagents.agents.utils.decision_protocol import (
    ALLOCATION_REVIEW_STAGE_ORDER,
    CHALLENGE_STAGE_KEY,
    DOWNSIDE_STAGE_KEY,
    PORTFOLIO_FIT_STAGE_KEY,
    THESIS_REVIEW_STAGE_ORDER,
    THESIS_STAGE_KEY,
    UPSIDE_STAGE_KEY,
    create_execution_state,
    create_final_decision_state,
    create_portfolio_context_state,
    create_temporal_context_state,
    create_review_loop_state,
)
from tradingagents.graph.propagation import Propagator
from tradingagents.graph.trading_graph import (
    build_state_log_entry,
    extract_final_decision_text,
)


def make_canonical_state():
    thesis_review = create_review_loop_state(THESIS_REVIEW_STAGE_ORDER)
    thesis_review["active_stage"] = INVESTMENT_DIRECTOR
    thesis_review["round_index"] = 2
    thesis_review["outputs"] = {
        THESIS_STAGE_KEY: "## Core Thesis\nCanonical upside thesis.",
        CHALLENGE_STAGE_KEY: "## Counterevidence\nCanonical challenge memo.",
    }
    thesis_review["final_memo"] = "## World Model\nCanonical director synthesis."
    thesis_review["completion_reason"] = "director_synthesis"

    execution_state = create_execution_state()
    execution_state["full_blueprint"] = "## Execution Plan\nCanonical execution state."
    execution_state["execution_plan"] = "Canonical execution state."

    allocation_review = create_review_loop_state(ALLOCATION_REVIEW_STAGE_ORDER)
    allocation_review["active_stage"] = PORTFOLIO_FIT_ENGINE
    allocation_review["round_index"] = 3
    allocation_review["outputs"] = {
        UPSIDE_STAGE_KEY: "## Upside Capture\nCanonical upside review.",
        DOWNSIDE_STAGE_KEY: "## Downside Map\nCanonical downside review.",
        PORTFOLIO_FIT_STAGE_KEY: "## Portfolio Role\nCanonical portfolio fit review.",
    }

    final_decision = create_final_decision_state()
    final_decision["full_decision"] = "## Rating\nOverweight\n\n## Capital Allocation Rationale\nCanonical final decision."
    final_decision["rating"] = "Overweight"
    final_decision["capital_allocation_rationale"] = "Canonical final decision."

    portfolio_context = create_portfolio_context_state()
    portfolio_context["portfolio_role"] = "Core alpha sleeve."
    portfolio_context["position_archetype"] = "Event-driven alpha seat."
    portfolio_context["book_correlation_view"] = "Moderate overlap with crowded growth book."
    portfolio_context["crowding_risk"] = "Elevated around catalysts."
    portfolio_context["capital_budget"] = "Reserve meaningful capital."
    portfolio_context["risk_budget"] = "Stage risk until fit is proven."
    portfolio_context["full_context"] = (
        "## Portfolio Role\nCore alpha sleeve.\n\n"
        "## Position Archetype\nEvent-driven alpha seat.\n\n"
        "## Correlation To Current Book\nModerate overlap with crowded growth book.\n\n"
        "## Crowding / Factor Overlap\nElevated around catalysts.\n\n"
        "## Capital Budget\nReserve meaningful capital.\n\n"
        "## Risk Budget\nStage risk until fit is proven."
    )

    temporal_context = create_temporal_context_state()
    temporal_context["long_cycle_mispricing"] = "Normalized earnings power is underappreciated."
    temporal_context["medium_cycle_rerating_path"] = "Clean execution can drive a multi-quarter re-rating."
    temporal_context["short_cycle_execution_window"] = "Near-term weakness creates the best entry."
    temporal_context["full_context"] = (
        "## Long-Cycle Mispricing\nNormalized earnings power is underappreciated.\n\n"
        "## Medium-Cycle Re-Rating Path\nClean execution can drive a multi-quarter re-rating.\n\n"
        "## Short-Cycle Execution Window\nNear-term weakness creates the best entry."
    )

    institution_memory_snapshot = {
        "latest_snapshot": {
            "world_model": "Canonical long-memory world model.",
            "latest_thesis": "Canonical prior thesis.",
        },
        "world_model_history": [
            {
                "trade_date": "2024-04-01",
                "world_model": "Canonical long-memory world model.",
            }
        ],
        "thesis_history": [
            {
                "trade_date": "2024-04-01",
                "thesis": "Canonical prior thesis.",
            }
        ],
        "forecast_records": [
            {
                "trade_date": "2024-04-01",
                "prediction": "Canonical prediction ledger entry.",
            }
        ],
        "agent_reliability": {
            "agents": {"Investment Director": {"hit_rate": 0.67}},
            "regimes": {"earnings": {"hit_rate": 0.71}},
        },
    }

    institution_memory_brief = (
        "## Long-Term World Model\nCanonical long-memory world model.\n\n"
        "## Thesis History\nCanonical prior thesis.\n\n"
        "## Prediction Ledger\nCanonical prediction ledger entry.\n\n"
        "## Agent Reliability Memory\nInvestment Director performs well in earnings regimes."
    )

    return {
        "company_of_interest": "NVDA",
        "trade_date": "2024-05-10",
        "selected_analysts": ["business_truth", "market_expectations"],
        "analysis_plan": "Canonical orchestration plan.",
        "analysis_brief": "Canonical brief.",
        "analysis_artifacts": {},
        "orchestration_journal": [],
        "portfolio_context": portfolio_context,
        "temporal_context": temporal_context,
        "institution_memory_snapshot": institution_memory_snapshot,
        "institution_memory_brief": institution_memory_brief,
        "decision_dossier": {"world_model": "Canonical world model."},
        "decision_dossier_markdown": "## AI Investment Dossier\n\n### World Model\nCanonical world model.",
        "market_expectations_report": "Canonical expectations report.",
        "business_truth_report": "Canonical business truth report.",
        "timing_catalyst_report": "",
        "why_now_report": "",
        "catalyst_path_report": "",
        "thesis_review": thesis_review,
        "execution_state": execution_state,
        "allocation_review": allocation_review,
        "final_decision": final_decision,
        "investment_debate_state": {
            "bull_history": "",
            "bear_history": "",
            "history": "",
            "latest_speaker": "",
            "current_response": "",
            "judge_decision": "",
            "count": 0,
        },
        "investment_plan": "",
        "trader_investment_plan": "",
        "risk_debate_state": {
            "aggressive_history": "",
            "conservative_history": "",
            "neutral_history": "",
            "history": "",
            "latest_speaker": "",
            "current_aggressive_response": "",
            "current_conservative_response": "",
            "current_neutral_response": "",
            "judge_decision": "",
            "count": 0,
        },
        "final_trade_decision": "LEGACY DECISION SHOULD NOT WIN",
    }


def make_session_context():
    return {
        "ticker": "NVDA",
        "analysis_date": "2024-05-10",
        "run_mode_label": "Capital Committee",
        "run_mode_summary": "Full institutional review for sizing and allocation decisions",
        "position_importance": "critical",
        "position_importance_label": "Critical",
        "token_budget": "expansive",
        "token_budget_label": "Expansive",
        "analysts": [],
        "research_depth": 5,
        "research_depth_label": "Deep",
        "llm_provider": "openai",
        "backend_url": "https://api.openai.com/v1",
        "shallow_thinker": "gpt-5-mini",
        "deep_thinker": "gpt-5.2",
        "google_thinking_level": None,
        "openai_reasoning_effort": "high",
        "anthropic_effort": None,
    }


class StateSchemaConsolidationTests(unittest.TestCase):
    def test_propagator_initializes_canonical_and_compatibility_state(self):
        state = Propagator().create_initial_state(
            "NVDA", "2024-05-10", ["market_expectations"]
        )

        self.assertIn("thesis_review", state)
        self.assertIn("execution_state", state)
        self.assertIn("allocation_review", state)
        self.assertIn("final_decision", state)
        self.assertIn("orchestration_state", state)
        self.assertIn("portfolio_context", state)
        self.assertIn("temporal_context", state)
        self.assertIn("institution_memory_snapshot", state)
        self.assertIn("institution_memory_brief", state)
        self.assertEqual(state["thesis_review"]["round_index"], 0)
        self.assertEqual(state["allocation_review"]["outputs"], {})
        self.assertEqual(state["orchestration_state"]["token_budget"], "balanced")
        self.assertEqual(state["portfolio_context"]["full_context"], "")
        self.assertEqual(state["temporal_context"]["full_context"], "")
        self.assertEqual(state["investment_debate_state"]["count"], 0)
        self.assertEqual(state["risk_debate_state"]["count"], 0)

    def test_cli_report_sections_use_canonical_state_without_legacy_fields(self):
        sections = build_report_sections_map(make_canonical_state())

        self.assertIn("portfolio_context", sections)
        self.assertIn("Core alpha sleeve", sections["portfolio_context"])
        self.assertIn("Event-driven alpha seat", sections["portfolio_context"])
        self.assertIn("temporal_context", sections)
        self.assertIn("Normalized earnings power is underappreciated", sections["temporal_context"])
        self.assertIn("multi-quarter re-rating", sections["temporal_context"])
        self.assertIn("best entry", sections["temporal_context"])
        self.assertIn("institution_memory_brief", sections)
        self.assertIn("Canonical long-memory world model", sections["institution_memory_brief"])
        self.assertIn("Canonical prediction ledger entry", sections["institution_memory_brief"])
        self.assertIn("thesis_review", sections)
        self.assertIn("Canonical upside thesis", sections["thesis_review"])
        self.assertIn("Canonical challenge memo", sections["thesis_review"])
        self.assertIn("Canonical director synthesis", sections["thesis_review"])
        self.assertIn("Canonical execution state", sections["execution_state"])
        self.assertIn("Canonical upside review", sections["allocation_review"])
        self.assertIn("Canonical final decision", sections["final_decision"])
        self.assertNotIn("LEGACY DECISION SHOULD NOT WIN", sections["final_decision"])

    def test_save_report_to_disk_prefers_canonical_sections(self):
        state = make_canonical_state()
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_file = save_report_to_disk(
                state,
                "NVDA",
                Path(tmp_dir),
                session_context=make_session_context(),
            )
            report_text = Path(report_file).read_text()

        self.assertIn("## II. Portfolio Mandate", report_text)
        self.assertIn("Core alpha sleeve", report_text)
        self.assertIn("## III. Time Horizon Split", report_text)
        self.assertIn("Normalized earnings power is underappreciated", report_text)
        self.assertIn("## IV. Institutional Memory", report_text)
        self.assertIn("Canonical long-memory world model", report_text)
        self.assertIn("## VI. Thesis Review", report_text)
        self.assertIn("## VII. Execution State", report_text)
        self.assertIn("## VIII. Allocation Review", report_text)
        self.assertIn("## IX. Final Decision", report_text)
        self.assertIn("Position Importance: Critical", report_text)
        self.assertIn("Token Budget: Expansive", report_text)
        self.assertIn("Canonical director synthesis", report_text)
        self.assertIn("Canonical final decision", report_text)
        self.assertNotIn("LEGACY DECISION SHOULD NOT WIN", report_text)

    def test_launch_brief_panel_displays_institution_controls(self):
        console = Console(record=True, width=160, file=StringIO())
        console.print(create_launch_brief_panel(make_session_context()))
        rendered = console.export_text()

        self.assertIn("Position Importance", rendered)
        self.assertIn("Critical", rendered)
        self.assertIn("Token Budget", rendered)
        self.assertIn("Expansive", rendered)

    def test_graph_logging_and_signal_extraction_prefer_canonical_state(self):
        state = make_canonical_state()

        self.assertIn("Canonical final decision", extract_final_decision_text(state))

        log_entry = build_state_log_entry(state)

        self.assertIn("final_decision", log_entry)
        self.assertIn("portfolio_context", log_entry)
        self.assertIn("temporal_context", log_entry)
        self.assertIn("institution_memory_snapshot", log_entry)
        self.assertIn("institution_memory_brief", log_entry)
        self.assertIn("compatibility_snapshot", log_entry)
        self.assertNotIn("final_trade_decision", log_entry)
        self.assertEqual(
            log_entry["compatibility_snapshot"]["final_trade_decision"],
            "LEGACY DECISION SHOULD NOT WIN",
        )


if __name__ == "__main__":
    unittest.main()
