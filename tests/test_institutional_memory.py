import tempfile
import unittest
from pathlib import Path

from tradingagents.agents.utils.decision_protocol import (
    create_execution_state,
    create_final_decision_state,
    create_portfolio_context_state,
    create_review_loop_state,
    THESIS_REVIEW_STAGE_ORDER,
    ALLOCATION_REVIEW_STAGE_ORDER,
)
from tradingagents.agents.utils.memory import InstitutionalMemoryStore


def make_final_state():
    thesis_review = create_review_loop_state(THESIS_REVIEW_STAGE_ORDER)
    thesis_review["outputs"] = {
        "thesis_case": "## Core Thesis\nDemand is accelerating.",
        "challenge_case": "## Counterevidence\nValuation is stretched.",
    }
    thesis_review["final_memo"] = "## World Model\nThe market is underestimating duration."

    execution_state = create_execution_state()
    execution_state["full_blueprint"] = "## Execution Plan\nAccumulate over several sessions."

    allocation_review = create_review_loop_state(ALLOCATION_REVIEW_STAGE_ORDER)
    allocation_review["outputs"] = {
        "upside_case": "## Upside Capture\nPress on clean beats.",
        "downside_case": "## Downside Map\nTrim if revisions stall.",
        "portfolio_fit_case": "## Portfolio Role\nFits as a core alpha sleeve.",
    }

    final_decision = create_final_decision_state()
    final_decision["full_decision"] = (
        "## Rating\nOverweight\n\n"
        "## Position Size\nStart at 3%.\n\n"
        "## Kill Criteria\nExit if demand inflects down.\n\n"
        "## Monitoring Triggers\nWatch revisions weekly.\n\n"
        "## Capital Allocation Rationale\nStrong asymmetric setup."
    )
    final_decision["rating"] = "Overweight"
    final_decision["position_size"] = "Start at 3%."
    final_decision["kill_criteria"] = "Exit if demand inflects down."
    final_decision["monitoring_triggers"] = "Watch revisions weekly."
    final_decision["capital_allocation_rationale"] = "Strong asymmetric setup."

    portfolio_context = create_portfolio_context_state()
    portfolio_context["portfolio_role"] = "Core alpha sleeve."
    portfolio_context["position_archetype"] = "Event-driven alpha seat."
    portfolio_context["book_correlation_view"] = "Moderate overlap with crowded growth."
    portfolio_context["crowding_risk"] = "Elevated around catalysts."
    portfolio_context["capital_budget"] = "Reserve meaningful capital."
    portfolio_context["risk_budget"] = "Stage risk until fit is proven."
    portfolio_context["full_context"] = (
        "## Portfolio Role\nCore alpha sleeve.\n\n"
        "## Position Archetype\nEvent-driven alpha seat."
    )

    return {
        "company_of_interest": "NVDA",
        "trade_date": "2024-05-10",
        "selected_analysts": ["business_truth", "market_expectations"],
        "orchestration_state": {"position_importance": "critical"},
        "portfolio_context": portfolio_context,
        "decision_dossier": {
            "world_model": "The market is underestimating duration.",
            "business_truth": "Demand is broadening across products.",
            "long_cycle_mispricing": "Normalized earnings power is underappreciated.",
            "market_expectations_view": "Consensus expects deceleration.",
            "medium_cycle_rerating_path": "Two clean quarters can force a re-rating.",
            "short_cycle_execution_window": "Use near-term volatility to build the position.",
            "core_thesis": "Earnings power is inflecting higher.",
            "variant_perception": "Street is too bearish on margin durability.",
            "counterevidence": "Valuation leaves less room for error.",
            "catalyst_path": "Product cycle plus estimate revisions.",
            "time_horizon": "6-12 months",
            "kill_criteria": "Demand inflects down materially.",
            "final_recommendation": "Overweight",
            "portfolio_role": "Core alpha sleeve.",
            "capital_budget": "Reserve meaningful capital.",
            "risk_budget": "Stage risk until fit is proven.",
        },
        "thesis_review": thesis_review,
        "execution_state": execution_state,
        "allocation_review": allocation_review,
        "final_decision": final_decision,
    }


class InstitutionalMemoryTests(unittest.TestCase):
    def test_record_run_persists_world_model_thesis_and_forecast_history(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = InstitutionalMemoryStore(
                {
                    "institution_memory_dir": str(Path(tmp_dir) / "memory"),
                    "institution_memory_history_limit": 10,
                }
            )
            final_state = make_final_state()
            store.record_run("NVDA", "2024-05-10", final_state)

            memory = store.load_company_memory("NVDA")

        self.assertEqual(memory["latest_snapshot"]["latest_rating"], "Overweight")
        self.assertEqual(len(memory["world_model_history"]), 1)
        self.assertEqual(len(memory["thesis_history"]), 1)
        self.assertEqual(len(memory["forecast_records"]), 1)
        self.assertIn(
            "underestimating duration",
            memory["world_model_history"][0]["world_model"],
        )
        self.assertIn(
            "Earnings power is inflecting higher.",
            memory["thesis_history"][0]["core_thesis"],
        )
        self.assertEqual(memory["forecast_records"][0]["status"], "open")

    def test_record_outcome_updates_forecast_and_agent_reliability(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = InstitutionalMemoryStore(
                {
                    "institution_memory_dir": str(Path(tmp_dir) / "memory"),
                    "institution_memory_history_limit": 10,
                }
            )
            final_state = make_final_state()
            store.record_run("NVDA", "2024-05-10", final_state)
            store.record_outcome(
                "NVDA",
                "2024-05-10",
                final_state,
                0.12,
                reflections={"engine::investment_director": "Director was right to focus on duration."},
            )
            memory = store.load_company_memory("NVDA")

        forecast = memory["forecast_records"][0]
        self.assertEqual(forecast["status"], "closed")
        self.assertEqual(forecast["outcome_label"], "win")
        self.assertEqual(forecast["realized_return"], 0.12)

        director_stats = memory["agent_reliability"]["agents"]["engine::investment_director"]
        self.assertEqual(director_stats["runs"], 1)
        self.assertEqual(director_stats["scored_runs"], 1)
        self.assertEqual(director_stats["wins"], 1)
        self.assertAlmostEqual(director_stats["average_return"], 0.12)
        self.assertIn("duration", director_stats["last_reflection"])

    def test_render_company_brief_includes_memory_layers(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = InstitutionalMemoryStore(
                {
                    "institution_memory_dir": str(Path(tmp_dir) / "memory"),
                    "institution_memory_history_limit": 10,
                }
            )
            final_state = make_final_state()
            store.record_run("NVDA", "2024-05-10", final_state)
            store.record_outcome("NVDA", "2024-05-10", final_state, -0.05)
            brief = store.render_company_brief("NVDA")

        self.assertIn("Long-Term World Model", brief)
        self.assertIn("Thesis Version History", brief)
        self.assertIn("Forecast Track Record", brief)
        self.assertIn("Agent Reliability", brief)
        self.assertIn("Temporal Split", brief)
        self.assertIn("Overweight", brief)


if __name__ == "__main__":
    unittest.main()
