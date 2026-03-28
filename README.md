# Future Invest

Future Invest is not an AI stock picker.

It is an AI-native investment operating system that turns research into a portfolio-aware decision packet: stance, position size, kill criteria, and monitoring.

Instead of stopping at a memo, Future Invest runs a lean institutional loop:
research, challenge, synthesis, and position construction.

What you get:
- A portfolio-aware stance, not a generic market opinion
- A position packet, not just a research summary
- Explicit kill criteria and monitoring triggers
- A lean default loop, with a fuller institutional path when needed

<div align="center">

Not a stock picker. Not a memo generator. A lean institutional loop for portfolio-aware investing.

🚀 [Why It Matters](#why-it-matters) | ⚡ [Quickstart](#5-minute-quickstart) | 🧠 [How It Works](#how-it-works) | 🖥️ [Interfaces](#interfaces) | 📦 [Python Runtime](#python-runtime) | 🗂️ [Project Index](PROJECT_INDEX.md)

</div>

Future Invest is easiest to read as one institutional sequence:

`mandate and context -> parallel research -> thesis vs challenge -> position packet -> memory and evaluation`

In `lean` mode, the loop stops when the packet is investable. In `full` mode, the same packet can escalate into deeper execution and committee review.

## Why It Matters

Most finance agents stop at analysis.

Future Invest is built around a harder endpoint:

`mandate -> research -> thesis vs challenge -> position packet`

That packet is the product. Instead of ending with "here is my memo," Future Invest tries to end with:

- `stance`
- `size`
- `entry framework`
- `kill criteria`
- `monitoring triggers`

This repo is for AI builders who want something more opinionated than a finance chatbot and more operational than a research copilot.

### Why It Gets Attention

- It is built around an institutional decision loop, not a generic question-answer flow.
- It compresses output into a position-construction packet instead of a long narrative memo.
- It introduces portfolio context before conviction hardens.
- It keeps a persistent memory layer so runs can compound over time.
- It includes an evaluation harness, so workflow quality can be tested rather than guessed.

### Why It Feels Different

| Category | Typical Research Agent | Future Invest |
| --- | --- | --- |
| Unit of work | Answer or memo | Institutional decision loop |
| Final artifact | Research narrative | Position packet |
| Reasoning structure | Single-run assistant | Orchestrated debate + synthesis |
| Portfolio context | Usually late or implicit | Introduced before thesis formation |
| Memory | Mostly stateless | Institutional memory across runs |

> Future Invest is designed for research and workflow prototyping. It is not financial, investment, or trading advice.

## What You Get

One successful run is supposed to feel less like "analysis complete" and more like "a seat is ready to discuss."

Example packet shape:

```yaml
stance: long
variant: market underestimates earnings durability
portfolio_role: core growth seat
size: medium
entry_framework: build on weakness around catalyst window
kill_criteria:
  - thesis breaks if demand normalization stalls for two quarters
  - cut if catalyst path slips and expectations reset higher anyway
monitoring:
  - estimate revisions
  - positioning and crowding
  - next catalyst date
missing_evidence:
  - channel check quality
  - management credibility under new guidance
```

## 5-Minute Quickstart

1. Clone and install:
   ```bash
   git clone https://github.com/welcomemyworld/TradingAgents.git future-invest
   cd future-invest
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
2. Set your provider key:
   ```bash
   export OPENAI_API_KEY=...
   ```
3. Launch the product:
   ```bash
   future-invest
   # or
   future-invest-web
   ```
4. Choose your provider, model pair, and loop mode in the CLI or web control room.

### Environment Note

Install Future Invest in a dedicated virtual environment.

If you install it into an existing Anaconda or research environment, `pip` may warn about unrelated packages such as `streamlit`, `wrds`, or `aext-*` that were already present in that environment. Those warnings usually reflect environment mixing rather than a Future Invest packaging bug.

The clean path is:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Provider Paths

Future Invest is bring-your-own-provider. Use the path that matches your account, quota, and model access.

| Provider | `llm_provider` | `backend_url` | Auth |
| --- | --- | --- | --- |
| OpenAI | `openai` | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| VectorEngine | `vectorengine` | `https://api.vectorengine.ai/v1` | `VECTORENGINE_API_KEY` or `OPENAI_API_KEY` |
| OpenRouter | `openrouter` | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |
| Google | `google` | `https://generativelanguage.googleapis.com/v1` | `GOOGLE_API_KEY` |
| Anthropic | `anthropic` | `https://api.anthropic.com/` | `ANTHROPIC_API_KEY` |
| xAI | `xai` | `https://api.x.ai/v1` | `XAI_API_KEY` |
| Ollama | `ollama` | `http://localhost:11434/v1` | local runtime |

Example config shape:

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

If your provider is rate-limited, retry the same lean configuration before increasing loop depth.

## How It Works

Future Invest is built as an AI-native institution rather than a collection of isolated analysts.

The loop is intentionally short, but each stage has a distinct institutional job.

### 1. Mandate And Context

The run begins by defining what kind of decision the system is being asked to make. That means setting the ticker, trade date, portfolio role, capital budget, risk budget, and loop depth.

This matters because Future Invest is not trying to produce a generic company memo. It is trying to produce a decision that makes sense for a specific seat inside a portfolio.

### 2. Parallel Research Rails

Future Invest then runs three capability-native research rails in parallel:

- `Business Truth`: what is economically true about the company, industry, or asset
- `Market Expectations`: what the tape, consensus, and positioning already imply
- `Timing & Catalysts`: what makes the decision urgent, actionable, or vulnerable right now

These rails are intentionally separated so the system does not collapse everything into one narrative too early. One rail asks what is real, another asks what is already priced, and the third asks why this decision matters now instead of later.

### 3. Thesis Versus Challenge

Once the research bundle exists, Future Invest forces a structured internal debate.

- The `Thesis Engine` builds the strongest investable case.
- The `Challenge Engine` attacks that case and surfaces counterevidence.
- The `Investment Director` synthesizes both sides into one institutional view.

This is the core discipline of the system. Instead of treating confidence as quality, it asks whether the idea can survive structured opposition before capital is assigned.

### 4. Position Packet

The main output is a position packet rather than a narrative memo.

In practice, that packet is supposed to answer a concrete set of questions:

- what is the stance
- how large should the position be
- what is the entry framework
- what breaks the thesis
- what should be monitored after entry
- what evidence is still missing

In `lean` mode, this is the natural stopping point. The system has done enough work to produce an opinionated, reviewable, and monitorable decision packet.

### 5. Memory And Evaluation

After the packet is produced, the run does not disappear. Future Invest writes back trace information, prediction residue, and case history so that later runs can compound instead of starting from zero.

This is also where evaluation matters. The project includes repeatable test paths and batch evaluation so the workflow can be judged on whether it improves decision quality, not just whether it sounds persuasive.

### 6. Full Loop Extension

Some decisions deserve more than the lean loop. When the seat is important enough, the same front-end packet can expand into deeper institutional review:

- execution planning
- upside capture logic
- downside guardrails
- portfolio fit
- capital allocation committee review

The point of the `full` path is not to add ceremony by default. It exists so larger or more complex positions can go through a deeper review process without changing the logic of the front-end research loop.

### What Keeps Compounding

- institutional memory
- prediction ledgers
- run traces
- evaluation against repeatable case sets

## Interfaces

### CLI

```bash
future-invest
python -m cli.main
```

The CLI is the main operator surface. It lets you choose:

- provider and model pair
- lean vs full loop depth
- capability stack
- mandate intensity and run posture

A legacy CLI alias still exists for backward compatibility, but the product surface is Future Invest.

### Web Control Room

```bash
future-invest-web
# or
python -m futureinvest_web.app
```

Then open `http://127.0.0.1:8000`.

The web control room uses the same runtime as the CLI, but renders the institution dossier in a lean-first interface with an optional full committee path.

## Evaluation

Future Invest includes a batch evaluation path so workflow quality can be measured.

Run the publish-facing smoke tests from the repo root:

```bash
python -m unittest \
  tests.test_investment_orchestration \
  tests.test_state_schema_consolidation \
  tests.test_evaluation_harness \
  tests.test_institutional_memory
```

For broader experiments, see:

- [PROJECT_INDEX.md](PROJECT_INDEX.md)
- [evaluation/README.md](evaluation/README.md)
- [docs/future-invest-proposal.md](docs/future-invest-proposal.md)

## Python Runtime

Future Invest uses LangGraph to keep the institution modular, inspectable, and reroutable.

The public brand is Future Invest. The current Python package path remains `tradingagents` for compatibility.

Example:

```python
from tradingagents.graph.trading_graph import FutureInvestGraph
from tradingagents.default_config import DEFAULT_CONFIG

graph = FutureInvestGraph(debug=True, config=DEFAULT_CONFIG.copy())
_, decision = graph.propagate("NVDA", "2026-01-15")
print(decision)
```

You can adjust the runtime configuration to change:

- provider and backend URL
- quick and deep model pair
- capability selection
- debate depth
- lean vs full institutional loop mode

See `tradingagents/default_config.py` for the full configuration surface.

## Repo Map

- [PROJECT_INDEX.md](PROJECT_INDEX.md): fastest way to find the important files
- [docs/future-invest-proposal.md](docs/future-invest-proposal.md): proposal-style framing
- [docs/future-invest-pitch-memo.md](docs/future-invest-pitch-memo.md): pitch-oriented positioning memo
- [docs/github-launch-checklist.md](docs/github-launch-checklist.md): release checklist
- [docs/github-upload-guide.md](docs/github-upload-guide.md): what should and should not be committed

## Contributing

Contributions are most useful when they improve one of these layers:

- institution design
- research quality
- decision protocol quality
- evaluation quality
- operator experience

## Citation

If you build on Future Invest, please cite the repository:

```bibtex
@software{futureinvest2026,
  author = {{Future Invest Project}},
  title = {Future Invest: AI-Native Institution Operating System},
  year = {2026},
  url = {https://github.com/welcomemyworld/TradingAgents},
  note = {GitHub repository}
}
```
