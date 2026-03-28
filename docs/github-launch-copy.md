# Future Invest Launch Copy

## One-Line Hook

Future Invest is not an AI stock picker. It is a lean institutional operating system for turning research into position construction.

## Short Launch Post

We just open-sourced `Future Invest`.

Most finance agents stop at “here is my analysis.”
Future Invest is built to keep going until the system can express an institutional view:

- what the variant is
- whether it belongs in the book
- how large the position should be
- what kills the trade
- what to monitor after entry

The default product is a lean loop, with a fuller committee path when deeper review is needed.

If you care about agent systems, decision loops, memory, or portfolio-aware workflows, this is the repo:

`Future Invest = investment institution operating system`

## HN / Forum Version

Future Invest is an open-source attempt to build an AI-native investment institution instead of another finance chatbot.

The core design choice is to organize the system around an institutional decision loop:

1. frame mandate and time horizon
2. run capability-native research
3. debate thesis vs challenge
4. compress the result into a position-construction packet
5. keep memory and evaluation around the workflow

The repo includes:

- CLI and web control room
- lean and full institutional loops
- institutional memory
- evaluation harness

The public launch path recommends the lean loop first and keeps OpenAI-compatible backends optional.
