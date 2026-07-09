# Green AI Calculator — Agentic LLM Cost & Carbon Explorer

An interactive, single-file educational tool that makes the cost, energy, carbon, and water *shape* of agentic LLM workloads visible — for both single-agent and multi-agent (per-role) architectures — and shows, lever by lever, how green software practices reduce it.

> **These reference implementations are intended for educational purposes — demonstrating how to apply green software concepts in practice. They are not production-ready applications, and practitioners adopting them should evaluate each against their own tooling, measurement, and methodology requirements.**

Part of the [GSF Reference Implementations](https://github.com/Green-Software-Foundation/reference-implementations) collection, under `tools/gsf/`. It complements the [sci-for-ai](https://github.com/Green-Software-Foundation/reference-implementations/tree/main/specifications/sci-for-ai/gsf/llm-inference) reference implementation: where that project shows how to *measure* an LLM pipeline against the [SCI for AI specification](https://sci-for-ai.greensoftware.foundation/), this tool teaches practitioners to *reason about the shape* of agentic workloads before and alongside measurement — why costs compound, where the footprint hides, and which design decisions move it.

---

## What it is

An agent is not one model call — and a production system is rarely one agent. A single user request fans out across a team of roles (a router, a worker loop with tool use and retries, a guardrail), and every turn re-processes an ever-growing transcript. The resulting cost compounds in a way no per-token price sheet reveals, and the energy, carbon, and water behind it never appear on any invoice. What can't be seen can't be reduced.

This tool is a browser-based simulator that makes that shape visible. The practitioner describes a workload (turns, standing prompt, tool returns, retries, scale), reads an itemized "utility bill" for it — cost, energy, operational and embodied carbon, and water, per run and at operational scale — and then flips reduction levers to see what each practice contributes, in the order a team would actually apply them.

It is one possible approach to teaching this material, contributed for the community to build on. Other valid approaches exist, and alternative implementations are welcome.

## What it demonstrates

- **The compounding context loop.** The core mechanic of agentic cost: each turn re-processes the standing prompt plus the accumulated transcript. The tool visualizes this growth per turn and derives every figure from it.
- **Single-agent and multi-agent architectures, priced side by side.** In default mode, one model and one token profile describe the whole run. In *stages mode*, each role (router, worker loop, guardrail, and so on) gets its own model tier, turn count, and token profile, with the transcript flowing through all of them — making explicit the routing that single-agent mode can only approximate.
- **A worked example, twice.** One realistic support-ticket workload is walked end-to-end as a single agent and again as a multi-agent system, with every intermediate figure computed live by the same engine — including a stage-by-stage pricing breakdown and a turn-level walkthrough — so the reader can trace each headline number back to its arithmetic.
- **Reduction levers mapped to green software practices.** Right-sizing models, trimming reasoning budgets, summarise-and-retrieve memory layers, prefix caching, bounding loops, hardening against retries, batching non-urgent work, and carbon-aware placement — each applied cumulatively, with a waterfall attributing the saving to the lever that earned it.
- **An SCI-aligned framing.** Impacts are reported per functional unit (one run) and split into operational and embodied components, mirroring the structure of the [Software Carbon Intensity](https://sci.greensoftware.foundation/) specification (ISO/IEC 21031) and its [SCI for AI](https://sci-for-ai.greensoftware.foundation/) extension. This tool illustrates the framing; it does not perform or replace an SCI measurement.
- **Framework grounding.** Every concept in the tool maps to a documented primitive in mainstream agent frameworks (LangGraph/LangChain, Google ADK, OpenAI Agents SDK, CrewAI), shown with per-framework guidance for both architectures and for each reduction lever — so the concepts are implementable, not just theoretical.

## What it is *not*

- **Not a measurement tool.** It is a simulator built on illustrative, documented assumptions. It reads no telemetry and produces estimates, not measurements. For measured pipelines, see the sci-for-ai reference implementation and the measurement guidance in the SCI for AI specification.
- **Not a rate card, benchmark, or endorsement of any figure.** All constants in the tool — pricing tiers, energy-per-token bands, grid intensities, facility and water factors, embodied amortization — are *illustrative values chosen for teaching*, drawn from cited public sources with their vintage stated, and editable in the tool itself. They are the contributor's choices, not figures published or endorsed by the Green Software Foundation, and they will drift as the field evolves. **Do not quote numbers from this tool as authoritative; calibrate with your own traces and measured data.**
- **Not production software.** No warranty of fitness for procurement, reporting, or compliance use. Published estimation approaches in this space are themselves subject to significant, documented uncertainty, which the tool's methodology section discusses.
- **Not a complete footprint.** The scope covers inference-time operational impacts plus an amortized embodied component. Training, networking, end-user devices, and framework scaffolding overhead are out of scope, as stated in the tool's methodology.

## How to use it

No build step, no dependencies, no API keys, no network calls for computation:

1. Open `index.html` in any modern browser.
2. **Calculator** — pick a preset or describe your own workload, choose a model tier and grid, and read the bill. Toggle *per-role stages* to model a multi-agent system with a model per role.
3. **Worked example** — follow one workload end-to-end, as a single agent and as a multi-agent system, and load either configuration into the calculator with one click.
4. **In practice** — see how each architecture and each reduction lever is implemented in LangGraph, Google ADK, the OpenAI Agents SDK, and CrewAI, and how to calibrate the tool from real traces.
5. **Extend it** — edit the data block to add your own model tiers, grids, presets, or levers; scenarios are shareable via URL.
6. **Methodology & sources** — every formula, assumption, scope boundary, known limitation, and source (with vintage) used by the tool.

## Calibrating to your own workload

The defaults are teaching values. To make the estimate reflect *your* system: run your framework with tracing enabled, read turns per run, input/output tokens per role, and retry rates from the traces, and enter them into the tool (stage rows for multi-agent systems, sliders for single-agent). The billed token counts in your traces are the ground truth this simulator approximates. The tool's methodology tab documents each assumption you may want to replace.

## Relationship to GSF work

- **[SCI](https://sci.greensoftware.foundation/) / [SCI for AI](https://sci-for-ai.greensoftware.foundation/):** the tool's per-functional-unit reporting and operational-plus-embodied split follow the specification's structure, as an educational illustration.
- **[Green Software Patterns](https://patterns.greensoftware.foundation/):** the reduction levers correspond to documented pattern families (right-sizing, caching, demand shaping, carbon-aware scheduling, and related practices).
- **[sci-for-ai reference implementation](https://github.com/Green-Software-Foundation/reference-implementations/tree/main/specifications/sci-for-ai/gsf/llm-inference):** the measurement-oriented counterpart to this reasoning-oriented tool.
- **[green-code-skill reference implementation](https://github.com/Green-Software-Foundation/reference-implementations/tree/main/tools/gsf/green-code-skill):** a sibling tool under `tools/gsf/`, applying green software patterns at code generation and review time in agentic coding tools.

## Files

| File | Purpose |
|---|---|
| `index.html` | The complete tool — UI, engine, worked examples, framework mapping, methodology, and sources in one self-contained file |
| `README.md` | This document |
| `LICENSE` | MIT license |

## Feedback and contributions

Questions about scope, methodology, or alternative approaches are welcome on the repository's issue tracker. Different teams will reasonably make different choices about assumptions, tooling, and pedagogy; alternative implementations of the same idea make the collection more useful, and are encouraged per the repository's contribution process.

## License

MIT License. See [LICENSE](./LICENSE).

---

*Reference implementations in this repository are educational, illustrative examples of how GSF specifications and green software tools can be applied. Each project documents the choices it made so readers can evaluate them against their own requirements.*
