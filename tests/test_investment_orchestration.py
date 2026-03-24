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
            '{"objective":"Blend speed and depth","thesis_focus":"Focus on quality first","risk_focus":"Watch downside","catalyst_focus":"Look for re-rating triggers","key_questions":["What is misunderstood?"],"ordered_capabilities":["business_truth","market_expectations"],"token_budget":"balanced","position_importance":"high","uncertainty_level":"medium","evidence_conflict_level":"medium","continue_research":true,"trigger_counterevidence_search":false}'
        )
        node = create_investment_orchestrator(
            llm,
            {
                "enable_investment_orchestrator": True,
                "analysis_routing_mode": "adaptive",
                "enable_dynamic_capability_expansion": True,
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
        self.assertEqual(result["orchestration_state"]["position_importance"], "high")
        self.assertTrue(result["orchestration_state"]["continue_research"])
        self.assertIn("portfolio_context", result)
        self.assertTrue(result["portfolio_context"]["full_context"])
        self.assertIn("temporal_context", result)
        self.assertIn("portfolio_role", result["decision_dossier"])

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

    def test_orchestrator_can_activate_reserve_capabilities(self):
        llm = FakeLLM(
            '{"objective":"Escalate the work for a higher-value idea","ordered_capabilities":["business_truth","market_expectations"],"add_capabilities":["business_truth"],"continue_research":true,"uncertainty_level":"high","evidence_conflict_level":"medium","token_budget":"balanced","position_importance":"critical","trigger_counterevidence_search":true,"counterevidence_focus":"Validate unit economics before sizing."}'
        )
        node = create_investment_orchestrator(
            llm,
            {
                "enable_investment_orchestrator": True,
                "analysis_routing_mode": "adaptive",
                "enable_dynamic_capability_expansion": True,
            },
        )
        state = {
            "company_of_interest": "NVDA",
            "trade_date": "2024-05-10",
            "selected_analysts": ["market_expectations"],
            "completed_analysts": [],
            "analysis_artifacts": {},
            "orchestration_journal": [],
            "decision_dossier": {},
        }

        result = node(state)

        self.assertEqual(result["selected_analysts"], ["market_expectations", "business_truth"])
        self.assertEqual(result["analysis_queue"], ["business_truth", "market_expectations"])
        self.assertEqual(result["current_analyst"], "business_truth")
        self.assertEqual(result["orchestration_state"]["add_capabilities"], ["business_truth"])
        self.assertTrue(result["orchestration_state"]["trigger_counterevidence_search"])
        self.assertIn("Added reserve capabilities", result["analysis_plan"])
        self.assertTrue(result["portfolio_context"]["full_context"])

    def test_orchestrator_can_stop_research_early(self):
        llm = FakeLLM(
            '{"objective":"Stop when the picture is already coherent","ordered_capabilities":["catalyst_path"],"continue_research":false,"stop_reason":"Evidence is coherent enough under the current budget.","uncertainty_level":"low","evidence_conflict_level":"low","token_budget":"tight","position_importance":"standard","trigger_counterevidence_search":false}'
        )
        node = create_investment_orchestrator(
            llm,
            {
                "enable_investment_orchestrator": True,
                "analysis_routing_mode": "adaptive",
                "enable_dynamic_capability_expansion": True,
            },
        )
        state = {
            "company_of_interest": "NVDA",
            "trade_date": "2024-05-10",
            "selected_analysts": ["market_expectations", "catalyst_path"],
            "completed_analysts": ["market_expectations"],
            "analysis_artifacts": {
                "market_expectations": {"report": "Market expectations already look consistent."}
            },
            "orchestration_journal": [],
            "decision_dossier": {},
        }

        result = node(state)

        self.assertEqual(result["analysis_queue"], [])
        self.assertEqual(result["current_analyst"], "")
        self.assertFalse(result["orchestration_state"]["continue_research"])
        self.assertEqual(
            result["orchestration_state"]["stop_reason"],
            "Evidence is coherent enough under the current budget.",
        )
        self.assertIn("Stop rule", result["analysis_plan"])

    def test_orchestrator_front_loads_portfolio_context(self):
        llm = FakeLLM(
            '{"objective":"Frame the idea like a real book manager","ordered_capabilities":["market_expectations"],"continue_research":true,"uncertainty_level":"medium","evidence_conflict_level":"medium","token_budget":"balanced","position_importance":"critical","portfolio_role":"Core alpha sleeve if the edge survives challenge.","position_archetype":"Event-driven alpha seat.","book_correlation_view":"High overlap with crowded AI growth risk unless hedged.","crowding_risk":"Elevated around catalyst windows.","capital_budget":"Reserve significant but staged capital.","risk_budget":"Use staged risk until portfolio fit is proven.","trigger_counterevidence_search":true,"counterevidence_focus":"Find what would make this overlap unacceptable."}'
        )
        node = create_investment_orchestrator(
            llm,
            {
                "enable_investment_orchestrator": True,
                "analysis_routing_mode": "adaptive",
                "enable_dynamic_capability_expansion": True,
            },
        )
        state = {
            "company_of_interest": "NVDA",
            "trade_date": "2024-05-10",
            "selected_analysts": ["market_expectations"],
            "completed_analysts": [],
            "analysis_artifacts": {},
            "orchestration_journal": [],
            "decision_dossier": {},
            "portfolio_context": {},
        }

        result = node(state)

        self.assertIn("Core alpha sleeve", result["portfolio_context"]["portfolio_role"])
        self.assertIn("Event-driven alpha seat", result["portfolio_context"]["position_archetype"])
        self.assertIn("crowded AI growth risk", result["portfolio_context"]["book_correlation_view"])
        self.assertIn("Reserve significant but staged capital", result["portfolio_context"]["capital_budget"])
        self.assertIn("Core alpha sleeve", result["analysis_plan"])
        self.assertIn("Event-driven alpha seat", result["analysis_brief"])
        self.assertIn("book_correlation_view", result["decision_dossier"])

    def test_orchestrator_preserves_temporal_context_in_brief(self):
        llm = FakeLLM(
            '{"objective":"Keep horizons separate","ordered_capabilities":["business_truth"],"continue_research":true,"uncertainty_level":"medium","evidence_conflict_level":"medium","token_budget":"balanced","position_importance":"high","trigger_counterevidence_search":false}'
        )
        node = create_investment_orchestrator(
            llm,
            {
                "enable_investment_orchestrator": True,
                "analysis_routing_mode": "adaptive",
                "enable_dynamic_capability_expansion": True,
            },
        )
        state = {
            "company_of_interest": "NVDA",
            "trade_date": "2024-05-10",
            "selected_analysts": ["business_truth"],
            "completed_analysts": [],
            "analysis_artifacts": {},
            "orchestration_journal": [],
            "decision_dossier": {},
            "portfolio_context": {},
            "temporal_context": {
                "long_cycle_mispricing": "Durable earnings power is mispriced.",
                "medium_cycle_rerating_path": "Execution plus revisions can re-rate over quarters.",
                "short_cycle_execution_window": "Wait for a softer tape before entry.",
            },
            "institution_memory_brief": "",
        }

        result = node(state)

        self.assertIn("Durable earnings power is mispriced.", result["analysis_plan"])
        self.assertIn("re-rate over quarters", result["analysis_brief"])
        self.assertIn("Wait for a softer tape", result["analysis_brief"])


if __name__ == "__main__":
    unittest.main()
