import unittest

from tradingagents.agents.utils.decision_protocol import (
    BUSINESS_TRUTH_SECTION_MAP,
    EXECUTION_DOSSIER_BRIEF_KEYS,
    THESIS_REVIEW_STAGE_ORDER,
    THESIS_STAGE_KEY,
    CHALLENGE_STAGE_KEY,
    append_review_stage_output,
    build_dossier_update,
    build_execution_state_update,
    build_final_decision_state_update,
    build_portfolio_context_state_update,
    build_temporal_context_state_update,
    create_review_loop_state,
    finalize_review_loop,
    render_review_transcript,
    render_dossier_brief,
    render_portfolio_context,
    render_temporal_context,
)


class DecisionProtocolTests(unittest.TestCase):
    def test_capability_report_populates_structured_dossier(self):
        state = {"decision_dossier": {"world_model": "Existing view"}}
        report = """## Business Reality
The company has structurally advantaged distribution.

## Earnings Power
Normalized margins can expand with scale.

## Balance Sheet / Resilience
Net cash and low refinancing risk.

## What Must Be True
Customer retention must stay above 95%.
"""

        update = build_dossier_update(
            state,
            report,
            BUSINESS_TRUTH_SECTION_MAP,
        )

        dossier = update["decision_dossier"]
        self.assertEqual(dossier["world_model"], "Existing view")
        self.assertIn("structurally advantaged distribution", dossier["business_truth"])
        self.assertIn("Normalized margins", dossier["earnings_power"])
        self.assertIn("Net cash", dossier["balance_sheet_resilience"])
        self.assertIn("95%", dossier["critical_assumptions"])

    def test_render_dossier_brief_filters_and_has_placeholder(self):
        empty_brief = render_dossier_brief({}, EXECUTION_DOSSIER_BRIEF_KEYS)
        self.assertIn("No structured dossier fields", empty_brief)

        dossier = {
            "world_model": "The market underestimates duration.",
            "portfolio_role": "Core long",
            "capital_budget": "Start at 3%.",
        }
        brief = render_dossier_brief(dossier, EXECUTION_DOSSIER_BRIEF_KEYS)

        self.assertIn("World Model", brief)
        self.assertIn("Core long", brief)
        self.assertIn("Capital Budget", brief)

    def test_review_loop_state_accumulates_outputs_and_final_memo(self):
        review_state = create_review_loop_state(THESIS_REVIEW_STAGE_ORDER)
        review_state = append_review_stage_output(
            review_state,
            THESIS_STAGE_KEY,
            "Thesis Engine",
            "## Core Thesis\nDemand is inflecting.",
        )
        review_state = append_review_stage_output(
            review_state,
            CHALLENGE_STAGE_KEY,
            "Challenge Engine",
            "## Counterevidence\nCompetition is intensifying.",
        )
        review_state = finalize_review_loop(
            review_state,
            "Investment Director",
            "## World Model\nThe edge is modest but actionable.",
        )

        self.assertEqual(review_state["round_index"], 2)
        self.assertIn("Demand is inflecting", review_state["outputs"][THESIS_STAGE_KEY])
        self.assertIn(
            "Competition is intensifying",
            review_state["outputs"][CHALLENGE_STAGE_KEY],
        )
        self.assertIn("The edge is modest", review_state["final_memo"])
        self.assertIn("Thesis Engine", render_review_transcript(review_state))

    def test_execution_and_final_decision_state_updates_parse_sections(self):
        execution_state = build_execution_state_update(
            {},
            """## Execution Plan
Work the order over several sessions.

## Entry Framework
Scale in around weakness.

## Position Construction
Start at one-third size.

## Liquidity Plan
Avoid open and close.

## Monitoring Plan
Track revisions and volume.
""",
        )
        final_decision_state = build_final_decision_state_update(
            {},
            """## Rating
Overweight

## Portfolio Mandate
High-conviction core long.

## Position Size
Start at 3%.

## Entry / Exit
Accumulate on pullbacks.

## Kill Criteria
Exit if revenue growth decelerates below guide.

## Monitoring Triggers
Watch estimate revisions weekly.

## Capital Allocation Rationale
Asymmetric upside with manageable crowding.
""",
        )

        self.assertIn("Work the order", execution_state["full_blueprint"])
        self.assertEqual(execution_state["entry_framework"], "Scale in around weakness.")
        self.assertEqual(final_decision_state["rating"], "Overweight")
        self.assertEqual(final_decision_state["position_size"], "Start at 3%.")
        self.assertIn(
            "Asymmetric upside",
            final_decision_state["capital_allocation_rationale"],
        )

    def test_portfolio_context_state_update_renders_front_loaded_mandate(self):
        portfolio_context = build_portfolio_context_state_update(
            {},
            {
                "portfolio_role": "Core alpha sleeve with clear catalysts.",
                "position_archetype": "Event-driven alpha seat.",
                "book_correlation_view": "Likely overlaps with crowded growth exposure.",
                "crowding_risk": "Moderate to high during earnings season.",
                "capital_budget": "Start with measured but meaningful capital.",
                "risk_budget": "Earn additional risk only after portfolio-fit review.",
            },
        )

        rendered = render_portfolio_context(portfolio_context)

        self.assertIn("Portfolio Role", rendered)
        self.assertIn("Event-driven alpha seat", rendered)
        self.assertIn("crowded growth exposure", rendered)
        self.assertIn("measured but meaningful capital", rendered)

    def test_temporal_context_state_update_separates_long_medium_short(self):
        temporal_context = build_temporal_context_state_update(
            {},
            {
                "long_cycle_mispricing": "The market is underestimating normalized earnings power.",
                "medium_cycle_rerating_path": "Two clean quarters can force a multi-month re-rating.",
                "short_cycle_execution_window": "Near-term pullbacks around event noise create the best entry.",
            },
        )

        rendered = render_temporal_context(temporal_context)

        self.assertIn("Long-Cycle Mispricing", rendered)
        self.assertIn("normalized earnings power", rendered)
        self.assertIn("multi-month re-rating", rendered)
        self.assertIn("best entry", rendered)


if __name__ == "__main__":
    unittest.main()
