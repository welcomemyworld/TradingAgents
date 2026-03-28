# Future Invest Project Index

This file is the fastest way to find the important parts of the repository.

## 1. Product Surfaces

- `cli/main.py`
  - Primary terminal operator interface.
  - Entry point for `future-invest` and legacy `tradingagents`.
- `futureinvest_web/app.py`
  - Local web control room server.
  - Entry point for `future-invest-web`.
- `futureinvest_web/static/index.html`
  - Main web dashboard layout.
- `futureinvest_web/static/styles.css`
  - Web brand system, editorial-console styling, and layout.
- `futureinvest_web/static/app.js`
  - Browser-side workflow and API calls.
- `futureinvest_web/static/cci-monogram.svg`
  - Custom Future Invest monogram asset.

## Proposal and Narrative Docs

- `docs/future-invest-proposal.md`
  - Proposal-style narrative for the Future Invest project.
  - Includes motivation, problem statement, timing-and-catalyst research design, lean/full workflow, evaluation plan, and contribution framing.
- `docs/future-invest-pitch-memo.md`
  - Pitch-oriented narrative for fund, investor, and strategy discussions.
  - Emphasizes positioning, differentiation, lean-first workflow, defensibility, and near-term milestones.
- `docs/github-launch-checklist.md`
  - Release-surface checklist for a star-oriented GitHub launch.
- `docs/github-launch-copy.md`
  - Draft launch copy for social posts, HN-style intros, and release messaging.
- `docs/release-v0.1.0.md`
  - First public release notes for the repo launch.
- `docs/github-upload-guide.md`
  - Visual guide for what should and should not be committed to GitHub.
- `assets/future-invest-workflow.svg`
  - Reusable workflow figure for decks, documents, and proposal material.
- `assets/github-upload-workflow.svg`
  - Visual workflow for deciding what belongs in a GitHub commit.

## 2. Runtime Entry

- `main.py`
  - Minimal source example for running the graph directly.
- `tradingagents/graph/trading_graph.py`
  - Main runtime entry.
  - Defines `FutureInvestGraph`.
  - Loads config, tools, graph, memory, and state logging.
- `tradingagents/default_config.py`
  - Default runtime config.
  - LLM provider, model pairing, orchestration settings, memory location, and output directories.

## 3. Graph Assembly

- `tradingagents/graph/setup.py`
  - Builds the LangGraph node topology.
- `tradingagents/graph/conditional_logic.py`
  - Controls routing, stage transitions, and stop conditions.
- `tradingagents/graph/propagation.py`
  - Creates the initial canonical state for a run.
- `tradingagents/graph/reflection.py`
  - Post-run reflection hooks.
- `tradingagents/graph/signal_processing.py`
  - Extracts the final rating signal from the full decision memo.

## 4. Canonical State and Protocol

- `tradingagents/agents/utils/agent_states.py`
  - Canonical state schema.
  - Key objects:
    - `orchestration_state`
    - `portfolio_context`
    - `temporal_context`
    - `institution_memory_snapshot`
    - `decision_dossier`
    - `thesis_review`
    - `execution_state`
    - `allocation_review`
    - `final_decision`
- `tradingagents/agents/utils/decision_protocol.py`
  - Shared parsing and rendering contract.
  - Converts engine outputs into dossier sections and structured state.
- `futureinvest_web/serializer.py`
  - Shared section builder for web-facing dossier rendering.

## 5. Institutional Engines

### Orchestration

- `tradingagents/agents/managers/investment_orchestrator.py`
  - Institution-level control brain.
  - Handles token budget, position importance, dynamic capability expansion, counterevidence triggers, early stopping, portfolio mandate, and time-horizon split.
  - In hard-loop mode it fans research into parallel engines before synthesis.

### Research Capability Stack

- `tradingagents/agents/analysts/fundamentals_analyst.py`
  - Business Truth
- `tradingagents/agents/analysts/market_analyst.py`
  - Market Expectations
- `tradingagents/agents/analysts/timing_catalyst_analyst.py`
  - Timing & Catalysts
- `tradingagents/agents/analysts/social_media_analyst.py`
  - Legacy compatibility wrapper that maps to `timing_catalyst`
- `tradingagents/agents/analysts/news_analyst.py`
  - Legacy compatibility wrapper that maps to `timing_catalyst`

### Decision and Capital Layers

- `tradingagents/agents/researchers/bull_researcher.py`
  - Thesis Engine
- `tradingagents/agents/researchers/bear_researcher.py`
  - Challenge Engine
- `tradingagents/agents/managers/research_manager.py`
  - Investment Director
- `tradingagents/agents/trader/trader.py`
  - Execution Engine
- `tradingagents/agents/risk_mgmt/aggressive_debator.py`
  - Upside Capture Engine
- `tradingagents/agents/risk_mgmt/conservative_debator.py`
  - Downside Guardrail Engine
- `tradingagents/agents/risk_mgmt/neutral_debator.py`
  - Portfolio Fit Engine
- `tradingagents/agents/managers/portfolio_manager.py`
  - Capital Allocation Committee

## 6. Institutional Memory

- `tradingagents/agents/utils/memory.py`
  - Persistent institution memory store.
  - Holds:
    - company memory
    - world model history
    - thesis history
    - prediction ledger
    - agent reliability memory

Default memory location:

- `tradingagents/institution_memory/`

## 7. Evaluation Stack

- `evaluation/run_eval.py`
  - Batch evaluation runner.
- `evaluation/scoring.py`
  - Automatic scoring logic for completeness, coverage, and decision quality.
- `evaluation/cases.sample.json`
  - Starter historical case set.
- `evaluation/README.md`
  - How to run evaluations.

Evaluation outputs are written to:

- `evaluation/results/`

## 8. Tests

- `tests/test_decision_protocol.py`
  - Decision protocol helpers
- `tests/test_evaluation_harness.py`
  - Evaluation harness
- `tests/test_institutional_memory.py`
  - Institution memory
- `tests/test_investment_orchestration.py`
  - Orchestrator routing and expansion
- `tests/test_state_schema_consolidation.py`
  - Canonical state and report rendering
- `tests/test_ticker_symbol_handling.py`
  - Ticker parsing and exact-symbol handling

## 9. Typical Commands

Install editable package:

```bash
pip install -e .
```

Launch CLI:

```bash
future-invest
```

Launch web UI:

```bash
future-invest-web
```

Run batch evaluation:

```bash
future-invest-eval --cases evaluation/cases.sample.json --label baseline
```

Run tests:

```bash
python -m unittest \
  tests.test_investment_orchestration \
  tests.test_state_schema_consolidation \
  tests.test_evaluation_harness \
  tests.test_institutional_memory
```

## 10. Output Locations

- CLI / runtime reports:
  - `results/<ticker>/<analysis_date>/`
- Evaluation batches:
  - `evaluation/results/<timestamp>_<label>/`
- Institution traces:
  - `tradingagents/institution_traces/`
- Institution memory:
  - `tradingagents/institution_memory/`

## 11. Best Files To Open First

If you want to understand the system quickly, open these in order:

1. `PROJECT_INDEX.md`
2. `README.md`
3. `tradingagents/graph/trading_graph.py`
4. `tradingagents/agents/managers/investment_orchestrator.py`
5. `tradingagents/agents/utils/agent_states.py`
6. `tradingagents/agents/utils/decision_protocol.py`
7. `futureinvest_web/app.py`
8. `evaluation/run_eval.py`
