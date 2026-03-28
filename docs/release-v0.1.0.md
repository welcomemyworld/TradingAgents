# Future Invest v0.1.0

Public launch of Future Invest.

Future Invest is an AI-native investment operating system built to turn research into a portfolio-aware decision packet:

- stance
- position size
- kill criteria
- monitoring triggers

This release is the first public snapshot of the project surface. The goal is to make the repo understandable, runnable, and shareable.

## What Is In This Release

- A lean-first institutional loop: `mandate -> research -> thesis vs challenge -> position packet`
- A web control room and CLI built on the same runtime
- A Chinese README surface in addition to the English README
- Evaluation and smoke-test paths for the public repo
- Public-surface cleanup for docs, assets, and repository history

## Core Product Idea

Most finance AI tools stop at analysis.

Future Invest tries to go one step further and turn research into something closer to an investable packet. Instead of ending with a memo, it tries to end with a view that can be discussed at the portfolio level.

## Getting Started

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
future-invest
```

You can also run the local web control room:

```bash
future-invest-web
```

## Supported Provider Paths

Future Invest is bring-your-own-provider. The runtime currently supports:

- OpenAI
- VectorEngine
- OpenRouter
- Google
- Anthropic
- xAI
- Ollama

## Known Limits

- You need your own API key or local model runtime.
- Free-model routes can be rate-limited.
- The project is designed for workflow prototyping and decision-systems experimentation, not financial advice.

## Recommended Reading Order

- [README.md](../README.md)
- [README.zh-CN.md](../README.zh-CN.md)
- [PROJECT_INDEX.md](../PROJECT_INDEX.md)
- [docs/future-invest-proposal.md](future-invest-proposal.md)

## Suggested GitHub Release Title

`Future Invest v0.1.0 — Public Launch`

## Suggested Short Release Body

Future Invest is an AI-native investment operating system for turning research into a portfolio-aware decision packet.

This first public release includes:

- a lean institutional loop
- CLI and web control room entrypoints
- English and Chinese README surfaces
- evaluation and smoke-test paths

Repository:
<https://github.com/welcomemyworld/TradingAgents>
