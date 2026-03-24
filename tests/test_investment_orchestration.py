import unittest

from tradingagents.agents.managers.investment_orchestrator import (
    create_investment_orchestrator,
)
from tradingagents.agents.utils.agent_utils import (
    ANALYST_DISPLAY_NAMES,
    build_research_context,
    get_capability_catalog,
    normalize_selected_analysts,
)


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self, content):
        self.content = content
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return FakeResponse(self.content)


class InvestmentOrchestrationTests(unittest.TestCase):
    def test_normalize_selected_analysts_deduplicates_and_filters(self):
        self.assertEqual(
            normalize_selected_analysts(
                ["catalyst_path", "invalid", "catalyst_path", "market_expectations"]
            ),
            ["market_expectations", "catalyst_path"],
        )

    def test_build_research_context_prefers_shared_artifacts(self):
        state = {
            "analysis_artifacts": {
                "catalyst_path": {"report": "Shared catalyst report"},
                "market_expectations": {"report": "Shared expectations report"},
            },
            "market_expectations_report": "State expectations report",
            "catalyst_path_report": "State catalyst report",
        }

        context = build_research_context(
            state, ["market_expectations", "catalyst_path"]
        )

        self.assertIn("Shared expectations report", context)
        self.assertIn("Shared catalyst report", context)
        self.assertNotIn("State expectations report", context)
        self.assertIn(ANALYST_DISPLAY_NAMES["market_expectations"], context)
        self.assertIn(ANALYST_DISPLAY_NAMES["catalyst_path"], context)

    def test_capability_catalog_uses_abstract_capability_titles(self):
        catalog = get_capability_catalog(["market_expectations", "business_truth"])

        self.assertIn("Market Expectations", catalog)
        self.assertIn("Business Truth", catalog)
        self.assertIn("market_expectations", catalog)
        self.assertIn("business_truth", catalog)

    def test_orchestrator_respects_model_ordering(self):
        llm = FakeLLM(
            '{"objective":"Blend speed and depth","thesis_focus":"Focus on quality first","risk_focus":"Watch downside","catalyst_focus":"Look for re-rating triggers","key_questions":["What is misunderstood?"],"ordered_capabilities":["business_truth","market_expectations"]}'
        )
        node = create_investment_orchestrator(
            llm,
            {
                "enable_investment_orchestrator": True,
                "analysis_routing_mode": "adaptive",
            },
        )
        state = {
            "company_of_interest": "NVDA",
            "trade_date": "2024-05-10",
            "selected_analysts": ["market_expectations", "business_truth"],
            "completed_analysts": [],
            "analysis_artifacts": {},
            "orchestration_journal": [],
        }

        result = node(state)

        self.assertEqual(
            result["analysis_queue"], ["business_truth", "market_expectations"]
        )
        self.assertEqual(result["current_analyst"], "business_truth")
        self.assertIn("Blend speed and depth", result["analysis_plan"])
        self.assertIn("Focus on quality first", result["analysis_brief"])

    def test_orchestrator_falls_back_to_default_order_on_invalid_json(self):
        llm = FakeLLM("not-json")
        node = create_investment_orchestrator(
            llm,
            {
                "enable_investment_orchestrator": True,
                "analysis_routing_mode": "adaptive",
            },
        )
        state = {
            "company_of_interest": "NVDA",
            "trade_date": "2024-05-10",
            "selected_analysts": ["catalyst_path", "market_expectations"],
            "completed_analysts": [],
            "analysis_artifacts": {},
            "orchestration_journal": [],
        }

        result = node(state)

        self.assertEqual(
            result["analysis_queue"], ["market_expectations", "catalyst_path"]
        )
        self.assertEqual(result["current_analyst"], "market_expectations")
        self.assertIn("Current priority order", result["analysis_plan"])


if __name__ == "__main__":
    unittest.main()
