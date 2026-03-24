import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.run_eval import load_cases
from evaluation.scoring import (
    CANONICAL_SECTION_KEYS,
    build_case_summary,
    build_manual_scorecard_rows,
    get_decision_quality_flags,
    get_research_coverage,
    get_section_presence,
    render_sections_markdown,
    score_final_state,
)
from tradingagents.agents.utils.decision_protocol import (
    ALLOCATION_REVIEW_STAGE_ORDER,
    CHALLENGE_STAGE_KEY,
    PORTFOLIO_FIT_STAGE_KEY,
    THESIS_REVIEW_STAGE_ORDER,
    THESIS_STAGE_KEY,
    UPSIDE_STAGE_KEY,
    create_execution_state,
    create_final_decision_state,
    create_portfolio_context_state,
    create_review_loop_state,
    create_temporal_context_state,
)


def make_eval_state():
    thesis_review = create_review_loop_state(THESIS_REVIEW_STAGE_ORDER)
    thesis_review["outputs"] = {
        THESIS_STAGE_KEY: "Canonical thesis case.",
        CHALLENGE_STAGE_KEY: "Canonical counterevidence.",
    }
    thesis_review["final_memo"] = "Canonical director synthesis."

    execution_state = create_execution_state()
    execution_state["full_blueprint"] = "Canonical execution blueprint."
    execution_state["execution_plan"] = "Stage in over weakness."

    allocation_review = create_review_loop_state(ALLOCATION_REVIEW_STAGE_ORDER)
    allocation_review["outputs"] = {
        UPSIDE_STAGE_KEY: "Canonical upside case.",
        PORTFOLIO_FIT_STAGE_KEY: "Canonical portfolio fit case.",
    }

    final_decision = create_final_decision_state()
    final_decision["full_decision"] = "Canonical final decision."
    final_decision["rating"] = "BUY"
    final_decision["kill_criteria"] = "Break thesis if demand weakens."

    portfolio_context = create_portfolio_context_state()
    portfolio_context["portfolio_role"] = "Core alpha sleeve."
    portfolio_context["full_context"] = "Canonical portfolio mandate."

    temporal_context = create_temporal_context_state()
    temporal_context["full_context"] = "Canonical time horizon split."
    temporal_context["long_cycle_mispricing"] = "Long cycle."
    temporal_context["medium_cycle_rerating_path"] = "Medium cycle."
    temporal_context["short_cycle_execution_window"] = "Short cycle."

    return {
        "selected_analysts": ["business_truth", "market_expectations"],
        "analysis_plan": "Canonical orchestration plan.",
        "portfolio_context": portfolio_context,
        "temporal_context": temporal_context,
        "institution_memory_brief": "Canonical memory brief.",
        "business_truth_report": "Canonical business truth report.",
        "market_expectations_report": "Canonical expectations report.",
        "why_now_report": "",
        "catalyst_path_report": "",
        "thesis_review": thesis_review,
        "execution_state": execution_state,
        "allocation_review": allocation_review,
        "final_decision": final_decision,
        "decision_dossier_markdown": "Canonical dossier markdown.",
    }


class EvaluationHarnessTests(unittest.TestCase):
    def test_load_cases_normalizes_selection_and_case_id(self):
        payload = [
            {
                "ticker": "NVDA",
                "analysis_date": "2024-05-10",
                "selected_analysts": ["why_now", "business_truth", "why_now"],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "cases.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            cases = load_cases(path)

        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["case_id"], "nvda_20240510")
        self.assertEqual(cases[0]["selected_analysts"], ["why_now", "business_truth"])

    def test_section_presence_and_scores_use_canonical_state(self):
        state = make_eval_state()

        section_presence = get_section_presence(state)
        self.assertTrue(section_presence["analysis_plan"])
        self.assertTrue(section_presence["portfolio_context"])
        self.assertTrue(section_presence["final_decision"])
        self.assertEqual(set(section_presence.keys()), set(CANONICAL_SECTION_KEYS))

        research_coverage = get_research_coverage(state)
        self.assertEqual(research_coverage["coverage_ratio"], 1.0)

        quality_flags = get_decision_quality_flags(state, "BUY")
        self.assertTrue(quality_flags["has_counterevidence"])
        self.assertTrue(quality_flags["has_kill_criteria"])

        scores = score_final_state(state, "BUY")
        self.assertGreater(scores["overall_score"], 0.9)

    def test_build_case_summary_and_manual_scorecard(self):
        state = make_eval_state()
        case = {
            "case_id": "nvda_20240510",
            "ticker": "NVDA",
            "analysis_date": "2024-05-10",
            "selected_analysts": ["business_truth", "market_expectations"],
        }

        summary = build_case_summary(case, state, "BUY", 12.345)
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["processed_signal"], "BUY")
        self.assertEqual(summary["runtime_seconds"], 12.345)
        self.assertEqual(summary["portfolio_role"], "Core alpha sleeve.")
        self.assertFalse(summary["missing_sections"])

        rows = build_manual_scorecard_rows([summary])
        self.assertEqual(rows[0]["case_id"], "nvda_20240510")
        self.assertEqual(rows[0]["processed_signal"], "BUY")
        self.assertEqual(rows[0]["reviewer_notes"], "")

    def test_render_sections_markdown_outputs_titled_document(self):
        markdown = render_sections_markdown(
            [
                {"title": "Portfolio Mandate", "content": "Canonical context."},
                {"title": "Final Decision", "content": "BUY"},
            ]
        )
        self.assertIn("## 1. Portfolio Mandate", markdown)
        self.assertIn("## 2. Final Decision", markdown)


if __name__ == "__main__":
    unittest.main()
