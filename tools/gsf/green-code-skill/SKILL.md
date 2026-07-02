---
name: green-code-skill
description: Apply Green Software Foundation patterns and SCI (Software Carbon Intensity) principles when generating new code or reviewing existing code. Use this skill whenever the user asks to write, refactor, optimize, or review code with any mention of sustainability, carbon footprint, energy efficiency, green coding, eco-friendly software, climate impact, or compute/cloud cost reduction — and proactively when designing cloud architectures, AI/ML pipelines, agentic AI systems, web frontends, or data-handling code where green patterns measurably reduce emissions. Covers 40+ patterns across Development, Architecture, AI/ML, and agentic AI workloads (retry budgets, planning depth, model right-sizing, response caching, tool-call thrashing).
---

# Green Code Skill

Generate and review code that reduces software carbon emissions, grounded in the Green Software Foundation (GSF) patterns catalog and the Software Carbon Intensity (SCI) specification.

This skill operates in two modes — **generation** (writing new code that follows green patterns by default) and **review** (auditing existing code against patterns and producing actionable findings). Most invocations are one or the other; both modes share the same underlying pattern knowledge.

## About this skill

This is an educational reference implementation from the [GSF Reference Implementations](https://github.com/Green-Software-Foundation/reference-implementations) collection, contributed by the Green Software Foundation under `tools/gsf/`. It demonstrates one concrete way to encode Green Software Foundation patterns as an agent skill. Recommendations produced by the skill are engineering input and should be applied with judgment for the target context — see `references/trade-offs.md`. The skill is a design-time and review-time advisor, not a runtime measurement tool.

## When to activate

Activate this skill when any of the following is true:

- The user mentions sustainability, carbon, energy, emissions, green coding, eco-friendly, or climate impact.
- The user mentions reducing compute cost, cloud cost, or "doing more with less" — these are usually SCI-aligned even when the user doesn't say "green."
- The user is generating code for cloud workloads, AI/ML pipelines, agentic AI systems, web frontends, data handling, or anything else with non-trivial compute or network footprint.
- The user asks for a code review and either mentions efficiency or hands over code with obvious green anti-patterns (uncompressed assets, synchronous loops over network calls, unbounded retries, full-scan queries, etc.).

Do **not** activate for: pure syntax fixes, single-line bug reports, unit-test scaffolding, or tasks where applying green patterns would clearly conflict with the user's stated goal (e.g. user is intentionally building a stress test).

## The SCI backbone

Every recommendation this skill makes maps to the SCI formula:

```
SCI = (E × I) + M   per R

E = Energy consumed by the software
I = Carbon intensity of that energy (location/time dependent)
M = Embodied emissions of the hardware (manufacturing + disposal, amortized)
R = Functional unit (per user, per request, per inference, per transaction)
```

Code-level changes mostly move **E** (less work = less energy) and **R** (more useful output per unit of work). **I** is mostly an ops/region decision — surface it as guidance, not as code. **M** moves when you avoid spinning up extra hardware (right-sizing, serverless, container density).

Group recommendations under the three GSF pillars:

1. **Energy efficiency** — do the same work with less compute/network/storage. Reduces E.
2. **Hardware efficiency** — use less hardware, or extend the useful life of what exists. Reduces M.
3. **Carbon awareness** — do flexible work when and where the grid is cleaner. Reduces I.

For deeper SCI grounding (including what *not* to claim), read `references/sci-formula.md`.

## Mode 1: Code generation

When generating new code:

1. **Identify the workload type** — web frontend, cloud backend, data pipeline, AI/ML inference, agentic AI orchestration, etc. This determines which pattern reference file to consult.
2. **Pick applicable patterns before writing.** Open the relevant reference file (`references/patterns-development.md`, `patterns-architecture.md`, or `patterns-ai-ml.md`) and pick the 2–5 patterns most relevant to this task. Do not try to apply all patterns.
3. **Write the code** with those patterns baked in by default — not as an afterthought. Examples: async network calls instead of sync, compressed payloads by default, lazy-loaded images, bounded retries, cache layer in front of LLM calls.
4. **Emit a "Green Notes" block** at the end of the generated code (as a comment block or a separate section) listing each pattern applied, which SCI term it reduces, and the canonical URL.

### Generation output template

```
<code here>

---
Green Notes
- <Pattern name> (reduces E) — <one-sentence reason this applies here>
  https://patterns.greensoftware.foundation/<path>
- <Pattern name> (reduces M) — <one-sentence reason>
  https://patterns.greensoftware.foundation/<path>

Trade-offs considered: <list any patterns deliberately not applied and why, e.g. "skipped server-side rendering — this is an admin tool with <10 concurrent users, SSR overhead would dominate">
```

If no pattern reasonably applies, say so plainly. Do not invent patterns to fill the section.

## Mode 2: Code review

When reviewing existing code:

1. **Read the code fully before flagging anything.** Skim-based reviews produce false positives that erode trust.
2. **Identify the workload type** and load the matching pattern reference file(s).
3. **Scan for the detection signals** listed under each pattern in the reference files. Each pattern's entry tells you what anti-pattern to look for.
4. **Produce a structured findings list** using the template below. One entry per finding. Sort by severity (high → low).
5. **Estimate impact qualitatively.** Quantitative SCI estimates require runtime measurement — never invent numbers. Use ranges and direction-of-effect language ("roughly halves E for this component", "small but compounding M reduction").

### Review output template

```
## Green Software Review

**Workload type:** <web | cloud backend | data pipeline | AI/ML | agentic AI | mixed>
**Files reviewed:** <list>

### Findings

#### [High] <Pattern name>
- **Location:** <file:line or function name>
- **Issue:** <what was found, in one or two sentences>
- **Pattern:** <canonical pattern name + URL>
- **SCI impact:** <which term, qualitative magnitude>
- **Suggested fix:** <concrete refactor — code snippet if short, approach if long>

#### [Medium] <Pattern name>
...

#### [Low] <Pattern name>
...

### Patterns checked and passed
- <list patterns the code already follows — this is positive feedback, not filler>

### Out of scope (need ops/architecture input)
- <list patterns that can't be assessed from code alone, e.g. region selection, instance type>
```

Severity guide:
- **High** — pattern violation causes ongoing, scaled emissions (every request, every user). Example: uncompressed images served to all visitors; unbounded LLM retries in production hot path.
- **Medium** — meaningful but bounded impact, or fix is non-trivial. Example: synchronous calls in a batch job that runs hourly.
- **Low** — minor, or context-dependent. Example: GIF used for a single decorative animation.

## Pattern index

Detailed pattern entries (problem, detection signals, fix approach, SCI term, canonical URL) live in the reference files. Consult the file that matches the workload before generating or reviewing.

| Reference file | Patterns | When to load |
|---|---|---|
| `references/patterns-development.md` | 23 Development patterns | Code-level: data handling, media, web performance, async, compression, TLS termination |
| `references/patterns-architecture.md` | 17 Architecture patterns | System-level: region selection, containers, serverless, statelessness, scaling |
| `references/patterns-ai-ml.md` | 9 AI/ML model and training patterns + 10 agentic AI workload patterns | Model selection, edge inference, agentic loops, LLM caching, retry budgets, planning depth |
| `references/sci-formula.md` | SCI specification primer | Whenever the user asks "how does this reduce carbon?" or wants the math |
| `references/trade-offs.md` | When NOT to apply a pattern | Always consult before applying anything aggressive |

## Honesty and trade-off rules

These are non-negotiable. Skills that produce confident-sounding nonsense damage trust and, ironically, work against the cause.

1. **Never invent numbers.** "This saves 47% energy" without a measurement is fabrication. Use directional language ("reduces E", "roughly halves network bytes for this endpoint") unless you have a real benchmark in hand.
2. **Surface trade-offs explicitly.** Carbon-aware scheduling adds latency. Aggressive caching adds staleness risk. Edge inference shifts M to client devices. Always name the trade-off in the Green Notes or Findings.
3. **Refuse to apply a pattern when context makes it wrong.** Real-time trading code should not be batched. A 10-user internal admin tool does not need SSR. A one-shot prototype does not need pre-trained-model transfer learning. Use judgment.
4. **Distinguish what code can move vs what ops moves.** Code can reduce E (most patterns) and M (right-sizing, density). Code cannot meaningfully move I (carbon intensity of grid) — that's region/time selection at the deploy layer. Don't claim code changes do things they don't.
5. **Cite the source pattern.** Link to the GSF pattern page where available, so practitioners can reference the source and read the full pattern description in context.
6. **The catalog evolves.** If a pattern URL 404s, fall back to the catalog index at https://patterns.greensoftware.foundation/ and tell the user the specific pattern may have moved or been renamed.

## What this skill is not

To prevent scope drift:

- Not a runtime measurement tool. For real SCI numbers, point users to CodeCarbon, Cloud Carbon Footprint, Kepler, or the Impact Framework.
- Not a carbon accounting / reporting tool.
- Not a substitute for the GSF Practitioner certification or the SCI specification itself.
- Not a license to add bloat. If applying a pattern would make the code worse on every other axis (readability, correctness, maintainability), don't apply it.
