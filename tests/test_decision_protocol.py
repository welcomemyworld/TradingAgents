import unittest

from tradingagents.agents.utils.decision_protocol import (
    BUSINESS_TRUTH_SECTION_MAP,
    EXECUTION_DOSSIER_BRIEF_KEYS,
    build_dossier_update,
    render_dossier_brief,
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
        self.assertNotIn("Capital Budget", brief)


if __name__ == "__main__":
    unittest.main()
