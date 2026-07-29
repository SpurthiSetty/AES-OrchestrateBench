# Measuring How Multi-Agent AI Pipelines Fail — Not Just Whether They Succeed

*Blog post for the Anote research hub. Authors: Yidian Chen, Yingzi Gu, Natan Vidra, Spurthi Setty, and Sharon Zheng. Based on the OrchestraBench paper (AAAI 2027 submission). Non-anonymized — this is the public-facing version, safe to brand.*

---

## The problem: production multi-agent systems fail *silently*

Multi-agent orchestration frameworks — AutoGen, LangGraph, CrewAI, the Anthropic Agents SDK — are moving from demos into production. A single "task" now runs through a chain of specialized agents: a router, a retriever, a tool-caller, a planner. When one of those steps goes wrong, the failure is usually **silent**: a misrouted task still returns a confident, plausible-looking answer. Nobody sees the error until it's downstream in a finished product.

Here's the gap that bothered us. Every agent benchmark we could find (AgentBench, OdysseyBench, SWE-Bench) answers exactly one question: *did the task succeed?* None of them can tell a team:

- **Which** orchestration decision actually failed,
- **How far** that error propagated before anyone noticed, or
- **Whether** the "intelligent" routing layer was even worth its added cost.

You can't harden a system on *reliability* if the only number you have is a pass/fail rate. So we built a benchmark for the questions that pass/fail can't answer.

## OrchestraBench: failure handling as a first-class metric

**OrchestraBench** treats *how a pipeline fails, recovers, and decomposes* as the unit of evaluation — not just whether it finished. It injects controlled, seeded failures into templated enterprise workflows and measures three things existing benchmarks leave out: per-failure-mode recovery, **cascade radius** (how many downstream stages a single error corrupts), and routing-policy mechanism. Every number regenerates from committed data with bootstrap confidence intervals and exact paired tests — offline, no API key needed.

We ran it on real Claude agents. Three findings stood out.

### 1. Failure handling splits into three sharp tiers

When we injected the five most common multi-agent failure modes (from the MAST taxonomy) into a verifiable task chain, recovery didn't degrade smoothly — it split into **three distinct tiers**:

- **Tool faults fully recover (1.0).** When a tool call fails, the agent just recomputes the value by hand. No lasting damage.
- **Ambiguous delegation partially recovers (~0.30).** About a third of the time the agent infers the intended operation and saves itself. Genuinely stochastic — real model behavior, not a fixed outcome.
- **Context pollution, conflicting outputs, and premature action never recover (0.0).** These corrupt the run and cascade all the way downstream.

And crucially: **retry does not repair the latent failures.** Retrying a corrupted-state task just reproduces the same wrong answer and lengthens the time before anyone notices. What you need is *detection and attribution*, not a blind retry loop.

### 2. Errors cascade further as pipelines get deeper

We injected a single error at the first stage of pipelines of increasing depth and measured how far it spread. The cascade grows almost linearly with depth — mean cascade radius climbs **0.93 → 1.85 → 2.80 → 3.63 → 4.67** across depths 3 to 7. The deeper your pipeline, the more expensive a single upstream mistake becomes. Tool faults, by contrast, stay contained at zero downstream corruption at every depth.

### 3. The routing *mechanism* — not the task — decides reliability

On a focused routing diagnostic, a keyword/flag heuristic (the kind of rule-based router that ships in a lot of production systems) scored **0% on adversarial cases** — inputs where the surface flags are missing or misleading but the intent is clear. A model-driven router that reasons over intent scored **100%** on the exact same cases. Same tasks, opposite outcomes: the blind spot is a property of the *routing mechanism*, not the difficulty of the work.

## What this is — and isn't

We're deliberate about scope. These are **controlled mechanism probes** on a verifiable task chain, not a domain-workload leaderboard. The failure-mode ordering holds when we reframe the same computation as a business (loan-approval) workflow, which tells us we're measuring real model behavior rather than an artifact — but the next steps are broader workflow suites, a cross-model sweep, and a fully multi-agent harness. The point of OrchestraBench isn't a single score; it's giving teams a way to ask *where* and *how* their orchestration breaks before it ships.

## Read more

The full paper (methods, statistics, and reproducibility) is available [here](https://github.com/anote-ai/Research-OrchestrateBench/blob/main/paper/main.pdf), and the benchmark harness — seed-controlled workflows, the failure injector, and the analysis scripts — is open source [here](https://github.com/anote-ai/Research-OrchestrateBench).
