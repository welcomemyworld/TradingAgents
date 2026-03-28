# Future Invest

Future Invest is not an AI stock picker. It is a lean institutional operating system for turning research into position construction.

<div align="center">

🚀 [Overview](#future-invest-framework) | 🗂️ [Project Index](PROJECT_INDEX.md) | ⚡ [Installation & CLI](#installation-and-cli) | 📦 [Python Runtime](#python-runtime) | 🤝 [Contributing](#contributing) | 📄 [Citation](#citation)

</div>

Future Invest is built for AI builders who want something more opinionated than a finance chatbot and more operational than a research memo generator. The default product is a lean loop: frame the mandate, run capability-native research, debate the thesis, and compress the result into a position-construction packet with explicit kill criteria and monitoring.

## Why It Exists

Most finance agents stop at “here is my analysis.” Future Invest is designed to keep going until the system can express an institutional view: what the variant is, whether the setup belongs in the book, how large the position should be, what would kill it, and what should be monitored after entry.

### What You Get
- A lean-by-default institutional loop instead of a generic research chat flow
- A final packet centered on `stance`, `size`, `entry framework`, `kill criteria`, and `monitoring triggers`
- A full committee extension when the lean loop is not enough
- Institutional memory and an evaluation harness so the system can be reviewed as a workflow, not just a one-off answer

<p align="center">
  <img src="assets/schema.png" style="width: 100%; height: auto;">
</p>

> Future Invest is designed for research purposes. Trading performance may vary based on model choice, market regime, data quality, and other non-deterministic inputs. It is not financial, investment, or trading advice.

### Why It Feels Different

| Category | Typical Research Agent | Future Invest |
| --- | --- | --- |
| Unit of work | Answer or memo | Institutional decision loop |
| Final artifact | Research narrative | Position-construction packet |
| Reasoning structure | Single-run assistant | Orchestrated debate + synthesis |
| Portfolio context | Usually late or implicit | Introduced before thesis formation |
| Memory | Mostly stateless | Institutional memory across runs |

## Quickstart

1. Install the package:
   ```bash
   pip install -e .
   ```
2. Set one supported API key:
   ```bash
   export OPENAI_API_KEY=...
   ```
3. Launch the product surface you want:
   ```bash
   future-invest
   # or
   future-invest-web
   ```
4. Use the recommended lean config:
   `Run Mode = Hard Loop`, `Provider = OpenAI`, `Quick = gpt-5-mini`, `Deep = gpt-5.4`

### Known-Good Launch Path

The blessed public path for first-time users is:

```yaml
llm_provider: openai
backend_url: https://api.openai.com/v1
quick_think_llm: gpt-5-mini
deep_think_llm: gpt-5.4
institutional_loop_mode: lean
run_mode: hard_loop
selected_analysts:
  - business_truth
  - market_expectations
  - timing_catalyst
```

If your provider is rate-limited, first retry the same lean setup before increasing depth. The public launch path should optimize for consistency, not the largest possible graph.

<p align="center">
  <img src="assets/cli/cli_init.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

### Optional OpenAI-Compatible Backends

Future Invest also supports OpenAI-compatible backends such as `VectorEngine` and `OpenRouter`. They are useful when you need routing flexibility, but they are intentionally not the primary launch path.

- `VectorEngine`: use `https://api.vectorengine.ai/v1`
- `OpenRouter`: use `https://openrouter.ai/api/v1`

Treat these as optional backends, not the default recommendation in public docs.

## Future Invest Framework

Future Invest is an AI-native investment institution framework for long/short equity research and capital allocation. Instead of treating LLMs as isolated analysts, the system organizes them as a coordinated institutional stack: an investment orchestrator frames the mandate, three parallel research engines build a shared world model, thesis and challenge engines debate variant perception, and the institution either resolves directly into a lean position-construction packet or expands into a full committee path for deeper execution and allocation review.

### Research Capability Stack
- Business Truth: Establishes what is economically real about the company, including earnings power, balance-sheet resilience, and the assumptions that must hold.
- Market Expectations: Infers what the tape, trend, momentum, and positioning imply the market already expects.
- Timing & Catalysts: Combines attention, narrative momentum, near-term catalysts, re-rating paths, and invalidation risks into one canonical research capability.

<p align="center">
  <img src="assets/analyst.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

### Lean Loop
- Thesis Engine: Builds the strongest investable upside case and makes variant perception explicit.
- Challenge Engine: Attacks weak assumptions, surfaces counterevidence, and defines failure modes.
- Investment Director: Synthesizes the debate into a shared world model, portfolio role, time horizon, and initial sizing view.
- Position Construction Packet: The default path compresses the run into stance, size, entry framework, kill criteria, monitoring triggers, and missing evidence.

<p align="center">
  <img src="assets/researcher.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Full Loop Extension
- Execution Engine: Converts the institutional view into an execution blueprint, including entry framework, position construction, liquidity plan, and monitoring triggers.

<p align="center">
  <img src="assets/trader.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Committee and Capital Formation
- Upside Capture Engine: Protects the fund from under-sizing asymmetric opportunities.
- Downside Guardrail Engine: Defines hard limits, scenario maps, and explicit kill criteria.
- Portfolio Fit Engine: Judges correlation, crowding, capital budget, and the trade's role inside the book.
- Capital Allocation Committee: Issues the final rating, position size, monitoring triggers, and capital-allocation rationale when the full loop is enabled.

<p align="center">
  <img src="assets/risk.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

## Installation and CLI

### Installation

Clone your Future Invest repository:
```bash
git clone <your-repo-url> FutureInvest
cd FutureInvest
```

Create a virtual environment in any of your favorite environment managers:
```bash
conda create -n futureinvest python=3.13
conda activate futureinvest
```

Install the package in editable mode:
```bash
pip install -e .
```

### Required APIs

Future Invest supports multiple LLM providers. Set the API key for your chosen provider:

```bash
export OPENAI_API_KEY=...          # OpenAI (GPT)
export GOOGLE_API_KEY=...          # Google (Gemini)
export ANTHROPIC_API_KEY=...       # Anthropic (Claude)
export XAI_API_KEY=...             # xAI (Grok)
export OPENROUTER_API_KEY=...      # OpenRouter
export VECTORENGINE_API_KEY=...    # VectorEngine (optional OpenAI-compatible backend)
export ALPHA_VANTAGE_API_KEY=...   # Alpha Vantage
```

For local models, configure Ollama with `llm_provider: "ollama"` in your config.

Alternatively, copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### CLI Usage

Launch the interactive CLI:
```bash
future-invest          # primary installed command
tradingagents          # legacy compatibility alias
python -m cli.main     # run directly from source
```
You will see a live interface where you can configure the research capability stack, lean or full institutional loop depth, LLM provider, and model pairing for an institution run.

### Web Interface

Launch the local Future Invest web control room:

```bash
python -m futureinvest_web.app
```

Or, after reinstalling editable scripts:

```bash
future-invest-web
```

Then open `http://127.0.0.1:8000` in your browser. The web interface uses the same `FutureInvestGraph` runtime as the CLI, but renders the institution dossier as a lean-first control room with an optional full committee path.

<p align="center">
  <img src="assets/cli/cli_init.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

As the run progresses, the CLI shows capability outputs, institutional debate, execution planning, capital formation, and the evolving AI Investment Dossier in real time.

<p align="center">
  <img src="assets/cli/cli_news.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

<p align="center">
  <img src="assets/cli/cli_transaction.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

### Launch Pack

- Release checklist: [docs/github-launch-checklist.md](docs/github-launch-checklist.md)
- Launch copy draft: [docs/github-launch-copy.md](docs/github-launch-copy.md)

### Quick Smoke Tests

Run the publish-facing smoke tests from the repo root:

```bash
python -m unittest \
  tests.test_investment_orchestration \
  tests.test_state_schema_consolidation \
  tests.test_evaluation_harness \
  tests.test_institutional_memory
```

These smoke tests are the default release gate. Broader end-to-end checks may require provider credentials, market-data access, and network connectivity.

## Python Runtime

### Implementation Details

Future Invest uses LangGraph to keep the institution modular, inspectable, and easy to re-route. The framework supports multiple LLM providers: OpenAI, Google, Anthropic, xAI, OpenRouter, and Ollama.

### Python Usage

The runtime currently keeps the legacy Python package path `tradingagents`, but the primary graph entrypoint is now `FutureInvestGraph()`. `TradingAgentsGraph()` remains available as a compatibility alias.

You can run `main.py`, or use the runtime directly:

```python
from tradingagents.graph.trading_graph import FutureInvestGraph
from tradingagents.default_config import DEFAULT_CONFIG

ta = FutureInvestGraph(debug=True, config=DEFAULT_CONFIG.copy())

# forward propagate
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)
```

You can also adjust the default configuration to set your own capability stack, model pairing, orchestration depth, and debate intensity.

```python
from tradingagents.graph.trading_graph import FutureInvestGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"        # openai, google, anthropic, xai, openrouter, ollama
config["deep_think_llm"] = "gpt-5.2"     # Model for complex reasoning
config["quick_think_llm"] = "gpt-5-mini" # Model for quick tasks
config["max_debate_rounds"] = 2

ta = FutureInvestGraph(debug=True, config=config)
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)
```

See `tradingagents/default_config.py` for all configuration options.

## Contributing

We welcome contributions that improve the institution design, research quality, capital-allocation logic, evaluation stack, and operator experience.

## Citation

If you build on this codebase, please cite:

```
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
      title={Future Invest: AI-Native Investment Institution Framework},
      author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
      year={2025},
      eprint={2412.20138},
      archivePrefix={arXiv},
      primaryClass={q-fin.TR},
      url={https://arxiv.org/abs/2412.20138}, 
}
```
