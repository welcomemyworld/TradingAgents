# Future Invest

AI-native investment institution framework for long/short equity research, execution design, and capital allocation.

<div align="center">

🚀 [Overview](#future-invest-framework) | 🗂️ [Project Index](PROJECT_INDEX.md) | ⚡ [Installation & CLI](#installation-and-cli) | 📦 [Python Runtime](#python-runtime) | 🤝 [Contributing](#contributing) | 📄 [Citation](#citation)

</div>

## Current Focus
- AI-native orchestration instead of fixed human-role pipelines
- Portfolio mandate and time-horizon splits surfaced before research begins
- Long-term institutional memory for company context, thesis history, prediction tracking, and agent reliability

## Future Invest Framework

Future Invest is an AI-native investment institution framework for long/short equity research and capital allocation. Instead of treating LLMs as isolated analysts, the system organizes them as a coordinated institutional stack: an investment orchestrator plans the research path, capability modules build a shared world model, thesis and challenge engines debate variant perception, execution turns that view into a tradable expression, and capital-allocation engines decide how the idea belongs inside a portfolio.

<p align="center">
  <img src="assets/schema.png" style="width: 100%; height: auto;">
</p>

> Future Invest is designed for research purposes. Trading performance may vary based on model choice, market regime, data quality, and other non-deterministic inputs. It is not financial, investment, or trading advice.

The current architecture is aimed at teams that want to blend:
- deep business understanding and long-horizon variant perception
- catalyst awareness, timing, and faster alpha capture
- explicit portfolio constraints, kill criteria, and capital budgeting

The framework decomposes investment work into capabilities and institutional protocols instead of a simple human-role replica. That makes the system easier to route, audit, and evolve.

### Research Capability Stack
- Business Truth: Establishes what is economically real about the company, including earnings power, balance-sheet resilience, and the assumptions that must hold.
- Market Expectations: Infers what the tape, trend, momentum, and positioning imply the market already expects.
- Why Now: Tracks attention, narrative momentum, and sentiment inflections to explain why the idea matters on this horizon.
- Catalyst Path: Maps the event chain that can compress uncertainty, shift expectations, or force a re-rating.

<p align="center">
  <img src="assets/analyst.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

### Institutional Debate Layer
- Thesis Engine: Builds the strongest investable upside case and makes variant perception explicit.
- Challenge Engine: Attacks weak assumptions, surfaces counterevidence, and defines failure modes.
- Investment Director: Synthesizes the debate into a shared world model, portfolio role, time horizon, and initial sizing view.

<p align="center">
  <img src="assets/researcher.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Execution Layer
- Execution Engine: Converts the institutional view into an execution blueprint, including entry framework, position construction, liquidity plan, and monitoring triggers.

<p align="center">
  <img src="assets/trader.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Capital Formation Layer
- Upside Capture Engine: Protects the fund from under-sizing asymmetric opportunities.
- Downside Guardrail Engine: Defines hard limits, scenario maps, and explicit kill criteria.
- Portfolio Fit Engine: Judges correlation, crowding, capital budget, and the trade's role inside the book.
- Capital Allocation Committee: Issues the final rating, position size, monitoring triggers, and capital-allocation rationale.

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

Install the package and its dependencies:
```bash
pip install .
```

### Required APIs

Future Invest supports multiple LLM providers. Set the API key for your chosen provider:

```bash
export OPENAI_API_KEY=...          # OpenAI (GPT)
export GOOGLE_API_KEY=...          # Google (Gemini)
export ANTHROPIC_API_KEY=...       # Anthropic (Claude)
export XAI_API_KEY=...             # xAI (Grok)
export OPENROUTER_API_KEY=...      # OpenRouter
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
You will see a live interface where you can configure the research capability stack, orchestration depth, LLM provider, and model pairing for an institution run.

### Web Interface

Launch the local Future Invest web control room:

```bash
python -m futureinvest_web.app
```

Or, after reinstalling editable scripts:

```bash
future-invest-web
```

Then open `http://127.0.0.1:8000` in your browser. The web interface uses the same `FutureInvestGraph` runtime as the CLI, but renders the institution dossier in a cyberpunk single-page dashboard.

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
