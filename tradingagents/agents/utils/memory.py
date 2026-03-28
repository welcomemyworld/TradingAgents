"""Financial situation memory using BM25 for lexical similarity matching.

Uses BM25 (Best Matching 25) algorithm for retrieval - no API calls,
no token limits, works offline with any LLM provider.
"""

from rank_bm25 import BM25Okapi
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
from datetime import datetime, timezone
import re


class FinancialSituationMemory:
    """Memory system for storing and retrieving financial situations using BM25."""

    def __init__(self, name: str, config: dict = None):
        """Initialize the memory system.

        Args:
            name: Name identifier for this memory instance
            config: Configuration dict (kept for API compatibility, not used for BM25)
        """
        self.name = name
        self.documents: List[str] = []
        self.recommendations: List[str] = []
        self.bm25 = None

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25 indexing.

        Simple whitespace + punctuation tokenization with lowercasing.
        """
        # Lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

    def _rebuild_index(self):
        """Rebuild the BM25 index after adding documents."""
        if self.documents:
            tokenized_docs = [self._tokenize(doc) for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_docs)
        else:
            self.bm25 = None

    def add_situations(self, situations_and_advice: List[Tuple[str, str]]):
        """Add financial situations and their corresponding advice.

        Args:
            situations_and_advice: List of tuples (situation, recommendation)
        """
        for situation, recommendation in situations_and_advice:
            self.documents.append(situation)
            self.recommendations.append(recommendation)

        # Rebuild BM25 index with new documents
        self._rebuild_index()

    def get_memories(self, current_situation: str, n_matches: int = 1) -> List[dict]:
        """Find matching recommendations using BM25 similarity.

        Args:
            current_situation: The current financial situation to match against
            n_matches: Number of top matches to return

        Returns:
            List of dicts with matched_situation, recommendation, and similarity_score
        """
        if not self.documents or self.bm25 is None:
            return []

        # Tokenize query
        query_tokens = self._tokenize(current_situation)

        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(query_tokens)

        # Get top-n indices sorted by score (descending)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_matches]

        # Build results
        results = []
        max_score = max(scores) if max(scores) > 0 else 1  # Normalize scores

        for idx in top_indices:
            # Normalize score to 0-1 range for consistency
            normalized_score = scores[idx] / max_score if max_score > 0 else 0
            results.append({
                "matched_situation": self.documents[idx],
                "recommendation": self.recommendations[idx],
                "similarity_score": normalized_score,
            })

        return results

    def clear(self):
        """Clear all stored memories."""
        self.documents = []
        self.recommendations = []
        self.bm25 = None


class InstitutionalMemoryStore:
    """Persistent institutional memory across runs for a single codebase."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        project_dir = Path(self.config.get("project_dir", "."))
        self.memory_dir = Path(
            self.config.get("institution_memory_dir", project_dir / "institution_memory")
        )
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.history_limit = int(self.config.get("institution_memory_history_limit", 50))

    def _company_key(self, ticker: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(ticker).strip().upper())
        return cleaned or "UNKNOWN"

    def _company_path(self, ticker: str) -> Path:
        return self.memory_dir / f"{self._company_key(ticker)}.json"

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _default_company_memory(self, ticker: str) -> Dict[str, Any]:
        return {
            "ticker": self._company_key(ticker),
            "last_updated": "",
            "latest_snapshot": {},
            "world_model_history": [],
            "thesis_history": [],
            "forecast_records": [],
            "agent_reliability": {
                "agents": {},
                "regimes": {},
            },
        }

    def load_company_memory(self, ticker: str) -> Dict[str, Any]:
        path = self._company_path(ticker)
        if not path.exists():
            return self._default_company_memory(ticker)

        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return self._default_company_memory(ticker)

        memory = self._default_company_memory(ticker)
        memory.update(data if isinstance(data, dict) else {})
        memory.setdefault("latest_snapshot", {})
        memory.setdefault("world_model_history", [])
        memory.setdefault("thesis_history", [])
        memory.setdefault("forecast_records", [])
        memory.setdefault("agent_reliability", {})
        memory["agent_reliability"].setdefault("agents", {})
        memory["agent_reliability"].setdefault("regimes", {})
        return memory

    def save_company_memory(self, ticker: str, memory: Dict[str, Any]) -> None:
        path = self._company_path(ticker)
        path.write_text(json.dumps(memory, indent=2, ensure_ascii=True))

    def _clean_text(self, value: Any) -> str:
        return str(value).strip() if value else ""

    def _numeric_return(self, returns_losses: Any) -> float | None:
        if isinstance(returns_losses, (int, float)):
            return float(returns_losses)
        if isinstance(returns_losses, str):
            try:
                return float(returns_losses.strip())
            except ValueError:
                return None
        return None

    def _outcome_label(self, returns_losses: Any) -> str:
        numeric = self._numeric_return(returns_losses)
        if numeric is None:
            return "unknown"
        if numeric > 0:
            return "win"
        if numeric < 0:
            return "loss"
        return "flat"

    def _replace_or_append(
        self,
        items: List[Dict[str, Any]],
        entry: Dict[str, Any],
        trade_date: str,
        unique_key: str,
    ) -> List[Dict[str, Any]]:
        updated = list(items)
        for idx, item in enumerate(updated):
            if (
                item.get("trade_date") == trade_date
                and item.get(unique_key) == entry.get(unique_key)
            ):
                updated[idx] = entry
                return updated[-self.history_limit :]
        updated.append(entry)
        return updated[-self.history_limit :]

    def _regime_tag(self, final_state: Dict[str, Any]) -> str:
        portfolio_context = final_state.get("portfolio_context", {}) or {}
        orchestration_state = final_state.get("orchestration_state", {}) or {}
        archetype = self._clean_text(portfolio_context.get("position_archetype")) or "unknown_archetype"
        importance = self._clean_text(orchestration_state.get("position_importance")) or "unknown_importance"
        normalized_archetype = re.sub(r"[^a-z0-9]+", "_", archetype.lower()).strip("_")
        normalized_importance = re.sub(r"[^a-z0-9]+", "_", importance.lower()).strip("_")
        return f"{normalized_archetype or 'unknown'}::{normalized_importance or 'unknown'}"

    def _component_entries(self, final_state: Dict[str, Any]) -> List[tuple[str, str]]:
        components = []
        dossier = final_state.get("decision_dossier", {}) or {}
        selected_analysts = list(final_state.get("selected_analysts", []) or [])
        for analyst_key in selected_analysts:
            components.append((analyst_key, f"capability::{analyst_key}"))

        thesis_review = final_state.get("thesis_review", {}) or {}
        if self._clean_text(thesis_review.get("outputs", {}).get("thesis_case")):
            components.append(("thesis_engine", "engine::thesis_engine"))
        if self._clean_text(thesis_review.get("outputs", {}).get("challenge_case")):
            components.append(("challenge_engine", "engine::challenge_engine"))
        if self._clean_text(thesis_review.get("final_memo")):
            components.append(("investment_director", "engine::investment_director"))

        execution_state = final_state.get("execution_state", {}) or {}
        if self._clean_text(execution_state.get("full_blueprint")):
            components.append(("execution_engine", "engine::execution_engine"))

        allocation_review = final_state.get("allocation_review", {}) or {}
        outputs = allocation_review.get("outputs", {}) or {}
        if self._clean_text(outputs.get("upside_case")):
            components.append(("upside_capture_engine", "engine::upside_capture_engine"))
        if self._clean_text(outputs.get("downside_case")):
            components.append(("downside_guardrail_engine", "engine::downside_guardrail_engine"))
        if self._clean_text(outputs.get("portfolio_fit_case")):
            components.append(("portfolio_fit_engine", "engine::portfolio_fit_engine"))
        if self._clean_text(final_state.get("final_decision", {}).get("full_decision")):
            components.append(
                ("capital_allocation_committee", "engine::capital_allocation_committee")
            )

        # Deduplicate while preserving order.
        seen = set()
        deduped = []
        for display_name, stable_key in components:
            if stable_key not in seen:
                seen.add(stable_key)
                deduped.append((display_name, stable_key))
        return deduped

    def _update_component_stats(
        self,
        bucket: Dict[str, Dict[str, Any]],
        key: str,
        display_name: str,
        trade_date: str,
        returns_losses: Any | None = None,
        reflection: str | None = None,
        count_run: bool = True,
    ) -> None:
        stats = dict(bucket.get(key) or {})
        stats.setdefault("display_name", display_name)
        stats["runs"] = int(stats.get("runs", 0)) + (1 if count_run else 0)
        stats["last_trade_date"] = trade_date
        if reflection:
            stats["last_reflection"] = reflection

        numeric_return = self._numeric_return(returns_losses)
        outcome_label = self._outcome_label(returns_losses)
        if numeric_return is not None:
            stats["scored_runs"] = int(stats.get("scored_runs", 0)) + 1
            stats["wins"] = int(stats.get("wins", 0)) + (1 if numeric_return > 0 else 0)
            stats["losses"] = int(stats.get("losses", 0)) + (1 if numeric_return < 0 else 0)
            stats["flats"] = int(stats.get("flats", 0)) + (1 if numeric_return == 0 else 0)
            stats["cumulative_return"] = float(stats.get("cumulative_return", 0.0)) + numeric_return
            scored_runs = max(int(stats.get("scored_runs", 1)), 1)
            stats["average_return"] = stats["cumulative_return"] / scored_runs
            stats["last_outcome"] = outcome_label
            stats["last_return"] = numeric_return

        bucket[key] = stats

    def get_company_memory_snapshot(self, ticker: str) -> Dict[str, Any]:
        memory = self.load_company_memory(ticker)
        latest = dict(memory.get("latest_snapshot") or {})
        latest["recent_world_models"] = list(memory.get("world_model_history", [])[-3:])
        latest["recent_thesis_versions"] = list(memory.get("thesis_history", [])[-3:])
        latest["recent_forecasts"] = list(memory.get("forecast_records", [])[-3:])
        return latest

    def render_company_brief(self, ticker: str) -> str:
        memory = self.load_company_memory(ticker)
        latest = memory.get("latest_snapshot") or {}
        parts = ["## Institutional Memory Snapshot"]

        long_term_world_model = self._clean_text(latest.get("world_model"))
        if long_term_world_model:
            parts.append(f"### Long-Term World Model\n{long_term_world_model}")

        temporal_lines = []
        if self._clean_text(latest.get("long_cycle_mispricing")):
            temporal_lines.append(
                f"- Long cycle: {latest.get('long_cycle_mispricing')}"
            )
        if self._clean_text(latest.get("medium_cycle_rerating_path")):
            temporal_lines.append(
                f"- Medium cycle: {latest.get('medium_cycle_rerating_path')}"
            )
        if self._clean_text(latest.get("short_cycle_execution_window")):
            temporal_lines.append(
                f"- Short cycle: {latest.get('short_cycle_execution_window')}"
            )
        if temporal_lines:
            parts.append("### Temporal Split\n" + "\n".join(temporal_lines))

        thesis_versions = memory.get("thesis_history", [])[-3:]
        if thesis_versions:
            lines = []
            for item in thesis_versions:
                thesis = self._clean_text(item.get("core_thesis"))
                variant = self._clean_text(item.get("variant_perception"))
                lines.append(
                    f"- {item.get('trade_date', 'unknown')}: thesis={thesis or 'n/a'} | variant={variant or 'n/a'}"
                )
            parts.append("### Thesis Version History\n" + "\n".join(lines))

        forecasts = memory.get("forecast_records", [])[-3:]
        if forecasts:
            lines = []
            for item in forecasts:
                outcome = item.get("outcome_label") or item.get("status") or "open"
                realized = item.get("realized_return")
                realized_str = f" ({realized})" if realized is not None else ""
                lines.append(
                    f"- {item.get('trade_date', 'unknown')}: {item.get('rating', 'n/a')} | {outcome}{realized_str}"
                )
            parts.append("### Forecast Track Record\n" + "\n".join(lines))

        agent_stats = memory.get("agent_reliability", {}).get("agents", {})
        scored_agents = [
            stats for stats in agent_stats.values() if int(stats.get("scored_runs", 0)) > 0
        ]
        scored_agents.sort(
            key=lambda item: (
                -float(item.get("average_return", 0.0)),
                -int(item.get("scored_runs", 0)),
            )
        )
        if scored_agents:
            lines = []
            for stats in scored_agents[:5]:
                lines.append(
                    f"- {stats.get('display_name', 'unknown')}: avg_return={stats.get('average_return', 0.0):.4f} over {stats.get('scored_runs', 0)} scored runs"
                )
            parts.append("### Agent Reliability\n" + "\n".join(lines))

        if len(parts) == 1:
            parts.append("No institutional memory has been accumulated for this instrument yet.")

        return "\n\n".join(parts)

    def record_run(
        self,
        ticker: str,
        trade_date: str,
        final_state: Dict[str, Any],
    ) -> None:
        memory = self.load_company_memory(ticker)
        dossier = final_state.get("decision_dossier", {}) or {}
        portfolio_context = final_state.get("portfolio_context", {}) or {}
        final_decision = final_state.get("final_decision", {}) or {}
        recorded_at = self._utc_now()

        world_model_entry = {
            "trade_date": str(trade_date),
            "recorded_at": recorded_at,
            "world_model": self._clean_text(dossier.get("world_model")),
            "business_truth": self._clean_text(dossier.get("business_truth")),
            "long_cycle_mispricing": self._clean_text(
                dossier.get("long_cycle_mispricing")
            ),
            "market_expectations_view": self._clean_text(dossier.get("market_expectations_view")),
            "medium_cycle_rerating_path": self._clean_text(
                dossier.get("medium_cycle_rerating_path")
            ),
            "short_cycle_execution_window": self._clean_text(
                dossier.get("short_cycle_execution_window")
            ),
            "final_recommendation": self._clean_text(dossier.get("final_recommendation") or final_decision.get("rating")),
            "portfolio_role": self._clean_text(dossier.get("portfolio_role") or portfolio_context.get("portfolio_role")),
            "position_archetype": self._clean_text(portfolio_context.get("position_archetype")),
            "capital_budget": self._clean_text(dossier.get("capital_budget") or portfolio_context.get("capital_budget")),
            "risk_budget": self._clean_text(dossier.get("risk_budget") or portfolio_context.get("risk_budget")),
        }
        if any(self._clean_text(value) for key, value in world_model_entry.items() if key not in {"trade_date", "recorded_at"}):
            memory["world_model_history"] = self._replace_or_append(
                memory.get("world_model_history", []),
                world_model_entry,
                str(trade_date),
                "world_model",
            )

        thesis_entry = {
            "trade_date": str(trade_date),
            "recorded_at": recorded_at,
            "core_thesis": self._clean_text(dossier.get("core_thesis")),
            "variant_perception": self._clean_text(dossier.get("variant_perception")),
            "long_cycle_mispricing": self._clean_text(
                dossier.get("long_cycle_mispricing")
            ),
            "medium_cycle_rerating_path": self._clean_text(
                dossier.get("medium_cycle_rerating_path")
            ),
            "short_cycle_execution_window": self._clean_text(
                dossier.get("short_cycle_execution_window")
            ),
            "counterevidence": self._clean_text(dossier.get("counterevidence")),
            "timing_catalyst": self._clean_text(
                dossier.get("timing_catalyst") or dossier.get("catalyst_path")
            ),
            "time_horizon": self._clean_text(dossier.get("time_horizon")),
            "kill_criteria": self._clean_text(dossier.get("kill_criteria") or final_decision.get("kill_criteria")),
            "final_recommendation": self._clean_text(dossier.get("final_recommendation") or final_decision.get("rating")),
        }
        if any(self._clean_text(value) for key, value in thesis_entry.items() if key not in {"trade_date", "recorded_at"}):
            memory["thesis_history"] = self._replace_or_append(
                memory.get("thesis_history", []),
                thesis_entry,
                str(trade_date),
                "core_thesis",
            )

        forecast_entry = {
            "trade_date": str(trade_date),
            "recorded_at": recorded_at,
            "rating": self._clean_text(final_decision.get("rating")),
            "position_size": self._clean_text(final_decision.get("position_size") or dossier.get("position_sizing")),
            "portfolio_role": self._clean_text(final_decision.get("portfolio_mandate") or dossier.get("portfolio_role") or portfolio_context.get("portfolio_role")),
            "position_archetype": self._clean_text(portfolio_context.get("position_archetype")),
            "time_horizon": self._clean_text(dossier.get("time_horizon")),
            "long_cycle_mispricing": self._clean_text(
                dossier.get("long_cycle_mispricing")
            ),
            "medium_cycle_rerating_path": self._clean_text(
                dossier.get("medium_cycle_rerating_path")
            ),
            "short_cycle_execution_window": self._clean_text(
                dossier.get("short_cycle_execution_window")
            ),
            "timing_catalyst": self._clean_text(
                dossier.get("timing_catalyst") or dossier.get("catalyst_path")
            ),
            "kill_criteria": self._clean_text(final_decision.get("kill_criteria") or dossier.get("kill_criteria")),
            "monitoring_triggers": self._clean_text(final_decision.get("monitoring_triggers") or dossier.get("monitoring_triggers")),
            "status": "open",
            "realized_return": None,
            "outcome_label": None,
        }
        if any(
            self._clean_text(forecast_entry.get(key))
            for key in ("rating", "position_size", "portfolio_role", "timing_catalyst", "kill_criteria")
        ):
            memory["forecast_records"] = self._replace_or_append(
                memory.get("forecast_records", []),
                forecast_entry,
                str(trade_date),
                "rating",
            )

        memory["latest_snapshot"] = {
            "trade_date": str(trade_date),
            "recorded_at": recorded_at,
            "world_model": world_model_entry.get("world_model", ""),
            "core_thesis": thesis_entry.get("core_thesis", ""),
            "variant_perception": thesis_entry.get("variant_perception", ""),
            "long_cycle_mispricing": thesis_entry.get("long_cycle_mispricing", ""),
            "medium_cycle_rerating_path": thesis_entry.get(
                "medium_cycle_rerating_path", ""
            ),
            "short_cycle_execution_window": thesis_entry.get(
                "short_cycle_execution_window", ""
            ),
            "portfolio_role": world_model_entry.get("portfolio_role", ""),
            "position_archetype": world_model_entry.get("position_archetype", ""),
            "capital_budget": world_model_entry.get("capital_budget", ""),
            "risk_budget": world_model_entry.get("risk_budget", ""),
            "latest_rating": forecast_entry.get("rating", ""),
        }

        regime_tag = self._regime_tag(final_state)
        agent_reliability = memory.setdefault("agent_reliability", {})
        agent_reliability.setdefault("agents", {})
        agent_reliability.setdefault("regimes", {})
        for display_name, stable_key in self._component_entries(final_state):
            self._update_component_stats(
                agent_reliability["agents"],
                stable_key,
                display_name,
                str(trade_date),
            )
            self._update_component_stats(
                agent_reliability["regimes"],
                f"{stable_key}::{regime_tag}",
                f"{display_name} [{regime_tag}]",
                str(trade_date),
            )

        memory["last_updated"] = recorded_at
        self.save_company_memory(ticker, memory)

    def record_outcome(
        self,
        ticker: str,
        trade_date: str,
        final_state: Dict[str, Any],
        returns_losses: Any,
        reflections: Dict[str, str] | None = None,
    ) -> None:
        memory = self.load_company_memory(ticker)
        trade_date = str(trade_date)
        outcome_label = self._outcome_label(returns_losses)
        numeric_return = self._numeric_return(returns_losses)

        forecast_records = list(memory.get("forecast_records", []))
        updated = False
        for idx, item in enumerate(forecast_records):
            if item.get("trade_date") == trade_date:
                item = dict(item)
                item["status"] = "closed"
                item["outcome_label"] = outcome_label
                item["realized_return"] = numeric_return
                forecast_records[idx] = item
                updated = True
                break
        if not updated:
            forecast_records.append(
                {
                    "trade_date": trade_date,
                    "status": "closed",
                    "outcome_label": outcome_label,
                    "realized_return": numeric_return,
                }
            )
        memory["forecast_records"] = forecast_records[-self.history_limit :]

        regime_tag = self._regime_tag(final_state)
        agent_reliability = memory.setdefault("agent_reliability", {})
        agent_reliability.setdefault("agents", {})
        agent_reliability.setdefault("regimes", {})

        reflections = reflections or {}
        for display_name, stable_key in self._component_entries(final_state):
            self._update_component_stats(
                agent_reliability["agents"],
                stable_key,
                display_name,
                trade_date,
                returns_losses=returns_losses,
                reflection=reflections.get(stable_key),
                count_run=False,
            )
            self._update_component_stats(
                agent_reliability["regimes"],
                f"{stable_key}::{regime_tag}",
                f"{display_name} [{regime_tag}]",
                trade_date,
                returns_losses=returns_losses,
                reflection=reflections.get(stable_key),
                count_run=False,
            )

        latest_snapshot = dict(memory.get("latest_snapshot") or {})
        latest_snapshot["last_realized_outcome"] = outcome_label
        latest_snapshot["last_realized_return"] = numeric_return
        latest_snapshot["last_outcome_trade_date"] = trade_date
        memory["latest_snapshot"] = latest_snapshot
        memory["last_updated"] = self._utc_now()
        self.save_company_memory(ticker, memory)


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory("test_memory")

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
