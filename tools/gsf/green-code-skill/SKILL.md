---
name: green-code-skill
description: Green Software Foundation patterns and SCI (Software Carbon Intensity) in three modes. Write new code with green patterns built in, review existing code for green anti-patterns, or measure energy and emissions with CodeCarbon. Use when the user mentions carbon, energy, or sustainability, asks to cut compute or cloud cost, wants to measure or verify the energy impact of a change, or is building cloud backends, web frontends, data pipelines, AI/ML, or agentic AI systems.
---

# Green Code Skill

Grounded in the Green Software Foundation (GSF) pattern catalog and the SCI specification. Stand down for single-line fixes, test scaffolding, and work where green patterns would defeat the goal (an intentional stress test).

## Pick one mode

| The user wants | Mode | Read |
|---|---|---|
| New code, a refactor, or a design | **Write** | [`modes/write.md`](modes/write.md) |
| Existing code audited | **Review** | [`modes/review.md`](modes/review.md) |
| Numbers: energy or emissions of real runs, before/after a change | **Measure** | [`modes/measure.md`](modes/measure.md) |

Read only that mode's file and finish its output before starting another mode. Modes hand off. A review finding or a written change becomes a measure baseline when the user wants evidence. A measurement with no measurable difference goes back to review for a better candidate.

## SCI backbone

```
SCI = (E × I) + M   per R
```

- **E**: energy the software consumes. Most patterns target E: compress, cache, async, smaller models, fewer calls.
- **I**: carbon intensity of that energy (where and when it runs). The deploy layer moves I. Code only *enables* I-aware execution by making work deferrable.
- **M**: embodied hardware emissions, amortized. Moves with right-sizing, serverless, and container density. Edge inference shifts M onto client devices.
- **R**: the functional unit (per request, per user, per inference). It is the denominator: SSR (one render serves many), batching, and pre-trained models improve R.

Organize recommendations under the three GSF pillars: **energy efficiency** (E), **hardware efficiency** (M), **carbon awareness** (I). For the full grounding and phrasing examples, read [`references/sci-formula.md`](references/sci-formula.md).

## Honesty rules (every mode)

1. **Numbers come from measurement.** Quote a figure only from a Measure-mode run or data the user supplied, and name its method alongside it. Everywhere else, use *directional* language: "reduces E for every request", "roughly halves network bytes", "removes a render per visit".
2. **Name the trade-off** beside each recommendation: latency from carbon-aware scheduling, staleness from caching, M shifted to clients by edge inference.
3. **Context beats the pattern.** Real-time paths stay unbatched, a 10-user admin tool stays client-rendered, a prototype trains nothing. Before applying anything aggressive, check [`references/trade-offs.md`](references/trade-offs.md).
4. **Code moves E, M, and R.** For I, say the code *enables* cleaner scheduling or regions.
5. **Cite the pattern** with its URL under https://patterns.greensoftware.foundation/. If a URL 404s, link the catalog root and say the pattern may have moved.

## Pattern index

Each entry gives the problem, detection signals, fix, SCI term, and canonical URL. Open the file matching the workload.

| File | Covers |
|---|---|
| [`references/patterns-development.md`](references/patterns-development.md) | 23 Development patterns: data handling, media, web performance, async I/O, compression, TLS termination |
| [`references/patterns-architecture.md`](references/patterns-architecture.md) | 17 Architecture patterns: region, containers, serverless, statelessness, scaling, CPU architecture |
| [`references/patterns-ai-ml.md`](references/patterns-ai-ml.md) | 9 AI/ML model and training patterns and 10 agentic AI patterns: model routing, retry budgets, planning depth, LLM caching, loop detection |
