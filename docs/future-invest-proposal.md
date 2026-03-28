# Future Invest Proposal

## Title

**Future Invest: Toward an AI-Native Investment Institution for Long/Short Equity Research, Execution Design, and Capital Allocation**

## Abstract

This proposal introduces **Future Invest**, an AI-native investment institution designed for long/short equity research, execution design, and portfolio-aware capital allocation. The central argument is that current multi-agent finance systems remain too close to human organizational charts: they are interpretable, but they are often static, weakly capital-aware, and effectively stateless across runs. Future Invest addresses this gap by combining four design elements within a unified operating system: capability-native research modules, institution-level orchestration, front-loaded portfolio constraints, and durable institutional memory. Instead of asking isolated agents to produce disconnected reports, the system coordinates a shared dossier that integrates business truth, market expectations, timing and catalysts, execution planning, and capital allocation logic. The proposal advances the hypothesis that such a system will generate more coherent, more portfolio-aware, and more testable investment decisions than both static role-based multi-agent baselines and simplified single-agent baselines. The repository already contains a working runtime, a batch evaluation harness, and persistent memory infrastructure, allowing the proposal to be evaluated not only as a conceptual design but also as an empirical systems contribution.

## 1. Motivation

Modern investment organizations face a persistent bottleneck: high-quality investment cognition is fragmented across functions, expensive to scale, and slow to recombine. Fundamental long/short platforms are often strongest at company understanding, industry structure, financial modeling, and long-horizon variant perception. However, they may be weaker in short-cycle timing, catalyst compression, and portfolio-level execution speed. By contrast, multi-manager and faster long/short equity platforms often excel in portfolio discipline, timing, and rapid capital allocation, but they can underinvest in durable company understanding and long-horizon mispricing.

An AI-native institution should not merely imitate one of these legacy structures, nor should it simply translate a human org chart into software. The more ambitious opportunity is to combine deep business understanding with faster timing, explicit portfolio constraints, and institutional learning. Future Invest is motivated by that opportunity.

## 2. Problem Statement

Most current multi-agent systems in finance still decompose work into fixed human-like roles such as analyst, trader, risk manager, and portfolio manager. This is useful for interpretability, but it leaves several structural limitations unresolved:

- workflows are usually fixed rather than dynamically routed;
- capital allocation is often treated as a terminal stage rather than a standing constraint;
- long-cycle mispricing, medium-cycle re-rating, and short-cycle execution are frequently conflated;
- memory is shallow, so systems repeatedly reason from scratch instead of compounding institutional knowledge;
- evaluation is often anecdotal, with limited infrastructure for comparing system variants over historical cases.

The result is that many systems are better at generating research-style narratives than at behaving like a genuine investment institution.

## 3. Research Objective

The objective of this project is to design and evaluate an AI-native investment institution that combines:

- the depth of fundamental long/short investing,
- the timing and portfolio discipline of faster platform-style investing,
- and the compounding advantage of machine memory and adaptive workflow control.

The practical goal is not simply to produce better reports. It is to build a system that can generate decisions that are clearer, more falsifiable, more portfolio-aware, and easier to evaluate over time.

## 4. Proposed System

Future Invest is designed around four architectural principles.

### 4.1 Capability-Native Research

The front-end research layer is organized around investment questions rather than legacy job titles:

- **Business Truth**: What is economically real about the company?
- **Market Expectations**: What is already priced into the market?
- **Timing & Catalysts**: Why does the idea matter on this horizon, what event chain could force a re-rating, and what signals would invalidate that timing?

This decomposition is intended to reduce role mimicry and sharpen the informational function of each module.

### 4.2 Institution-Level Orchestration

An **Investment Orchestrator** acts as the institutional control layer rather than a static scheduler. It determines:

- which capability modules to activate,
- whether additional research is worth the token and time budget,
- when to intensify counterevidence search,
- when to stop research and move into execution and capital formation.

In other words, the orchestrator allocates research effort in response to uncertainty, evidence conflict, and mandate importance.

### 4.3 Capital-Aware Decision Protocol

Portfolio reasoning is surfaced early instead of being appended after thesis formation. Before the thesis is finalized, the system constructs:

- a **Portfolio Mandate**,
- a **Time Horizon Split**,
- an **Institutional Memory Brief**.

This makes the downstream workflow explicitly conditional on portfolio role, risk budget, capital budget, and temporal structure.

### 4.4 Long-Term Institutional Memory

Future Invest maintains durable company-level memory that includes:

- world model history,
- thesis history,
- prediction ledger,
- agent reliability memory.

This memory is meant to let the system behave more like a persistent institution and less like a stateless assistant.

## 5. Workflow Overview

Figure 1 summarizes the proposed workflow.

![Figure 1. Future Invest workflow.](../assets/future-invest-workflow.svg)

**Figure 1.** Future Invest begins with mission setup and institutional framing, routes through a capability-native research stack, synthesizes outputs through a decision core, resolves through a lean position-construction loop by default, optionally expands into a fuller committee path, and finally writes outcomes back into institutional memory and evaluation logs.

At a high level, the workflow proceeds in six stages:

1. **Mission Setup**  
   The operator specifies the instrument, date, mandate intensity, and model configuration.

2. **Institutional Framing**  
   The orchestrator constructs the initial portfolio mandate, time-horizon split, and institutional memory brief.

3. **Capability Research Stack**  
   Business Truth, Market Expectations, and Timing & Catalysts populate a shared dossier, with the research layer designed to run in parallel inside the hard loop.

4. **Decision Core**  
   Thesis Engine, Challenge Engine, and Investment Director convert research outputs into a coherent world model and investable thesis.

5. **Lean Position Construction / Full Committee Extension**  
   The default lean loop resolves directly into stance, sizing, kill criteria, and monitoring. When deeper review is required, the system expands into execution and allocation engines.

6. **Institutional Learning Loop**  
   Final decisions and realized outcomes are recorded into persistent memory and evaluation logs.

## 6. Research Questions and Hypotheses

The proposal is organized around one primary question:

> Can an AI-native investment institution produce more coherent, more capital-aware, and more evaluable investment decisions than role-based or single-agent baselines?

This question is decomposed into four hypotheses.

### H1. Research Quality

Capability-native decomposition will improve thesis clarity, counterevidence quality, and world-model coherence relative to role-based baselines.

### H2. Temporal Discipline

Explicit separation of long-cycle mispricing, medium-cycle re-rating, and short-cycle execution will improve the distinction between “good company” and “good trade right now.”

### H3. Portfolio Discipline

Front-loaded portfolio constraints will improve portfolio-role clarity, sizing discipline, kill criteria, and trade-to-book fit.

### H4. Institutional Learning

Persistent institutional memory will improve cross-run consistency and reduce repeated analytical failure over time.

## 7. Evaluation Design

The repository already contains a batch evaluation harness in [`evaluation/run_eval.py`](../evaluation/run_eval.py). This makes the proposal empirically testable inside the codebase itself.

Evaluation should proceed on four layers.

### 7.1 Engineering Reliability

- run success rate,
- latency and runtime dispersion,
- structural completeness of canonical sections,
- robustness to case variation and configuration changes.

### 7.2 Research Quality

- thesis clarity,
- counterevidence strength,
- portfolio mandate clarity,
- time-horizon separation,
- dossier completeness.

### 7.3 Institution Quality

- usefulness of execution planning,
- explicitness of kill criteria,
- capital-budget discipline,
- portfolio-fit reasoning,
- consistency across repeated runs.

### 7.4 Outcome Quality

- distribution of final ratings,
- forward return buckets,
- hit rate,
- realized drawdown,
- post-hoc error analysis by module, regime, and decision stage.

The most informative experimental design is a structured comparison across at least three systems:

- the original role-based multi-agent workflow,
- the current Future Invest workflow,
- a simplified single-agent baseline.

## 8. Expected Contribution

This project is expected to contribute in three ways.

### 8.1 Systems Contribution

It offers a concrete architecture for AI-native investing that replaces static role replication with adaptive orchestration, explicit portfolio context, temporal decomposition, and durable memory.

### 8.2 Methodological Contribution

It proposes a way to evaluate investment agents as institutions rather than only as single-run forecasters. This includes engineering metrics, research-quality metrics, institution-quality metrics, and outcome metrics.

### 8.3 Conceptual Contribution

It reframes the role of AI in investing. The core claim is not that one more agent or one better prompt solves the problem, but that the unit of design should be the institution itself.

## 9. Scope and Limitations

This project does not claim to solve the entire problem of real-world asset management. Several limitations remain important:

- outputs remain sensitive to model quality, prompt design, and data vendor coverage;
- the current portfolio layer is still more textual than fully state-driven;
- realized investment performance depends on execution assumptions and market regime;
- system improvement must be demonstrated through repeated evaluation rather than asserted from isolated examples.

These limitations are not peripheral; they define the next frontier of work.

## 10. Why This Matters

If successful, Future Invest provides a blueprint for a new category of investment organization: one that combines the depth of fundamental long/short research, the speed and discipline of modern platform investing, and the compounding advantage of machine memory and workflow optimization.

The broader ambition is therefore not to build a better report generator. It is to prototype the operating system of a future investment institution.
