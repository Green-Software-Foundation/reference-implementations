# SCI (Software Carbon Intensity) — Grounding for Code-Level Decisions

The Software Carbon Intensity specification is the GSF's measurement standard. This file gives just enough grounding for the skill to reason honestly about which code changes affect which SCI term, and which don't.

## The formula

```
SCI = (E × I) + M   per R
```

| Term | Meaning | Unit (typical) |
|---|---|---|
| **E** | Energy consumed by the software, end to end | kWh |
| **I** | Carbon intensity of that energy at the time and place it was consumed | gCO₂eq / kWh |
| **M** | Embodied emissions of the hardware used, amortized over its useful life and the share this workload consumed | gCO₂eq |
| **R** | Functional unit — what one "unit of useful work" looks like for this software | per request / per user / per inference / per transaction |

SCI is a **rate**, not a total. You always express it as carbon-per-something. Halving R (doing twice as much useful work for the same energy and hardware) reduces SCI just as much as halving E.

## What code-level changes can actually move

| SCI term | Can code move it? | Examples |
|---|---|---|
| **E** | **Yes, directly.** Most patterns target E. | Compressing payloads, caching, async I/O, fewer LLM calls, smaller models, lazy loading, efficient algorithms |
| **I** | **Mostly no — this is an ops/deploy decision.** Code can *prepare* for carbon-aware execution but cannot itself change the grid mix. | Code that can defer non-urgent work (queues, batch jobs) makes carbon-aware scheduling *possible*. Region selection happens at deploy time. |
| **M** | **Indirectly, yes.** Code that uses less hardware lowers the embodied share. | Right-sizing instances, container density via stateless design, serverless, edge inference (shifts M to user devices — name this trade-off) |
| **R** | **Yes — this is the most underused lever.** | Server-side rendering for high-traffic pages (one render serves many), batch processing (one job serves many records), pre-trained model reuse (one training serves many tasks) |

The most common mistake is claiming a code change moves I. It almost never does directly. What it *can* do is make I-aware scheduling viable — that's a real benefit, but say it accurately.

## The three pillars (how GSF organizes interventions)

GSF teaches three operating principles. Every pattern maps to one or more.

1. **Energy efficiency** — do the same work with less compute, network, or storage. Targets E.
2. **Hardware efficiency** — use less hardware, or extend the life of what exists. Targets M.
3. **Carbon awareness** — do flexible work when and where the grid is cleaner. Targets I (mostly via deploy/ops; code enables it via deferrable workloads).

Use the pillar language when explaining recommendations to users — it's the vocabulary they'll see in GSF training and case studies.

## What this skill should never do

- **Invent quantitative SCI numbers.** Real SCI scores come from measurement tools (CodeCarbon, Cloud Carbon Footprint, Kepler, Impact Framework, cloud-provider carbon dashboards). Without instrumentation, use directional language only ("reduces E", "halves network bytes for this endpoint", "removes a full re-render per visit").
- **Claim a code change improves I.** Code can enable carbon-aware behavior; the I term itself only moves when the workload actually runs on cleaner electricity. That's a runtime/deploy outcome.
- **Treat SCI as a single number to optimize.** It's a rate. Compare SCI before and after the same R. Don't compare "SCI of system A" to "SCI of system B" without confirming R is defined the same way.

## How to phrase impact in outputs

Good ("directional, honest"):

- "Compressing this payload reduces E for every request on this endpoint."
- "Caching this LLM response collapses N retries into one cached lookup for repeat queries — E drops roughly in proportion to cache hit rate."
- "Using serverless here reduces M because idle capacity is shared across tenants instead of provisioned per-app."

Bad ("invented or misleading"):

- "This saves 23% carbon." (no measurement)
- "Switching to ARM reduces I." (it reduces E per unit work, not I)
- "This is now a green system." (SCI is a rate; you reduced it, you didn't eliminate it)

## Reading further

- SCI specification: https://sci.greensoftware.foundation/
- Pattern catalog: https://patterns.greensoftware.foundation/
- Practitioner course: https://learn.greensoftware.foundation/
- Measurement tools: CodeCarbon, Cloud Carbon Footprint, Kepler, Impact Framework
