# Green Code Skill — Usage Guide

Shared reference for using the Green Software skill in any coding tool where you have installed it. Covers what the skill does, working examples for all three modes (write, review, measure), prompts to try across common workloads, and troubleshooting.

> This skill is an educational reference implementation from the [GSF Reference Implementations](https://github.com/Green-Software-Foundation/reference-implementations) collection under `tools/gsf/`. Recommendations produced by the skill should be applied with engineering judgment for the target context, and quantitative impact claims should be treated as directional unless backed by runtime measurement. See the [README](./README.md) for the full scope, design choices, and educational context.

If you have not yet installed the skill, see the tool-specific quickstart in [`getting-started/`](./getting-started/).

## What the skill does

The skill activates when your prompt matches its description — anything mentioning sustainability, carbon, energy, green coding, efficiency, cost reduction, measuring energy impact, or the design of cloud, AI/ML, or agentic AI workloads. It operates in three modes:

- **Write mode** — writing new code that follows Green Software Foundation patterns by default, with a Green Notes block explaining which patterns were applied and why.
- **Review mode** — analyzing existing code against green software patterns and producing a structured findings list with severity, canonical pattern references, and concrete fixes.
- **Measure mode** — running a baseline and one or more variants under CodeCarbon and reporting energy and operational carbon per functional unit, labelled *measured* or *estimated*.

You do not need to name the skill explicitly in every prompt. Naming it on the first turn is a helpful way to guarantee activation while you get familiar with it.

## Verifying the skill is active

After installing the skill in your tool of choice (see the [tool-specific quickstarts](./getting-started/)), open a new conversation and send:

> Using the green-code-skill, generate a Node.js Express endpoint that returns a paginated list of products from a PostgreSQL database.

If the response includes code followed by a **Green Notes** block listing patterns applied, the skill is active and working.

## Example 1 — Writing code

Use write mode when you want Claude to write new code that follows green software patterns from the start.

**Prompt:**

> Write a Node.js Express endpoint that returns a paginated list of products from a PostgreSQL database. Follow green software patterns.

**What happens under the hood:**

1. Claude identifies the workload as a cloud backend service.
2. It consults `references/patterns-development.md` and `references/patterns-architecture.md`.
3. It selects the patterns most relevant to this specific task — typically pagination, asynchronous I/O, and caching headers for a listing endpoint.
4. It writes the code with those patterns applied by default.
5. It appends a Green Notes block explaining which patterns were applied and why.

**Sample output:**

```javascript
router.get('/products', async (req, res) => {
  const page = Number(req.query.page) || 1;
  const limit = Math.min(Number(req.query.limit) || 50, 200);
  const offset = (page - 1) * limit;

  const result = await db.query(
    'SELECT id, name, price, stock FROM products ORDER BY id LIMIT $1 OFFSET $2',
    [limit, offset]
  );

  res.set('Cache-Control', 'public, max-age=60');
  res.json({ page, limit, results: result.rows });
});
```

```
---
Green Notes
- Reduce transmitted data (reduces E) — Pagination with a bounded limit prevents returning
  the entire products table on every request; the projection returns only the columns the
  client needs.
  https://patterns.greensoftware.foundation/development/data-handling/reduce-transmitted-data
- Use asynchronous network calls instead of synchronous (reduces E) — The handler uses async
  DB access so the event loop can serve other requests while waiting on I/O.
  https://patterns.greensoftware.foundation/development/use-async-instead-of-sync
- Cache static data (reduces E) — Cache-Control enables browser and CDN caching for repeat
  product-list requests, avoiding redundant DB reads.
  https://patterns.greensoftware.foundation/development/data-handling/cache-static-data

Trade-offs considered: gzip/Brotli text compression is best enabled at the reverse proxy or
API gateway layer rather than inside Express, so it is not shown in the endpoint code.
```

## Example 2 — Reviewing existing code

Use review mode when you want to analyze existing code against green software patterns.

**Prompt:**

> Review this Python script against green software patterns.
>
> ```python
> import requests, json
>
> def fetch_all_users():
>     users = []
>     for i in range(1, 10000):
>         r = requests.get(f"https://api.example.com/users/{i}")
>         users.append(r.json())
>
>     with open("users.json", "w") as f:
>         json.dump(users, f)
> ```

**What happens under the hood:**

1. Claude identifies the workload as a data pipeline.
2. It reads the script and consults the development and architecture pattern references.
3. It scans for anti-patterns tied to each canonical pattern.
4. It produces a structured findings list sorted by severity.

**Sample output:**

```
## Green Software Review

**Workload type:** data pipeline
**Files reviewed:** the provided script

### Findings

#### [High] Use asynchronous network calls instead of synchronous
- **Location:** fetch_all_users, the for-loop
- **Issue:** 10,000 sequential blocking HTTP requests keep the CPU idle for most of the
  run — one full request round-trip per user.
- **Pattern:** https://patterns.greensoftware.foundation/development/use-async-instead-of-sync
- **SCI impact:** Reduces E significantly — concurrent async requests complete the same
  work in a fraction of the wall-clock time, so the process holds server resources for
  far less time.
- **Suggested fix:** Use httpx.AsyncClient with asyncio.gather in batches of ~50–100
  concurrent requests, with retry and rate-limit handling.

#### [High] Reduce transmitted data
- **Location:** fetch_all_users, the per-user API call
- **Issue:** The code fetches one user record per request. If the API exposes a batch
  endpoint, a single request could return many users with far less per-record overhead
  (headers, TLS negotiation, round-trip latency).
- **Pattern:** https://patterns.greensoftware.foundation/development/data-handling/reduce-transmitted-data
- **SCI impact:** Reduces E — fewer HTTP round-trips, less header overhead, fewer TLS
  negotiations.
- **Suggested fix:** Check the API for a batch endpoint (for example, GET /users?page=1&
  limit=100 or GET /users?ids=1,2,3,...). Fall back to concurrent single-user fetches
  only if no batch API exists.

#### [Medium] Compress stored data
- **Location:** the json.dump write
- **Issue:** The output file is written as uncompressed JSON. For a 10,000-record file,
  this is substantially larger than needed on both write and subsequent read.
- **Pattern:** https://patterns.greensoftware.foundation/development/data-handling/compress-stored-data
- **SCI impact:** Reduces M (less storage footprint) and E (less I/O on subsequent reads).
- **Suggested fix:** Write to a gzipped stream (gzip.open("users.json.gz", "wt")). If the
  data will be read analytically, a columnar format like Parquet delivers further
  compression and much faster analytical reads.

### Patterns checked and passed
- Not applicable at this scale — the script is small enough that most patterns are
  opportunities to add rather than passes to note.

### Out of scope (need ops/architecture input)
- Region selection for where this script runs (affects I in the SCI formula)
- Whether this batch job could be scheduled during a low-carbon-intensity window
```

## Example 3 — Measuring a change

Use measure mode when you want numbers: the energy and operational carbon of real runs, usually before and after a change. The skill drives [CodeCarbon](https://github.com/mlco2/codecarbon) through the bundled harness `scripts/measure.py`, so it needs a tool that can run commands on your machine (Claude Code, Codex CLI, Cursor, Aider). With `uv` installed, CodeCarbon is installed ephemerally on first run. If you installed only `AGENTS.md`, also copy `scripts/measure.py` into your project.

**Prompt:**

> Measure the energy difference between the loop and builtin implementations in driver.py.

**What happens under the hood:**

1. The agent agrees the functional unit (R) with you, here one million records aggregated, and makes each variant a single command doing identical work. It sizes the work so each run lasts at least ~10 seconds.
2. It runs the harness. The harness interleaves the variants, discards a warm-up run, measures each run as a CodeCarbon task, and measures an idle floor.
3. It reads the Method line first. *Measured* means hardware energy counters (RAPL, NVML, and so on). *Estimated* means CodeCarbon's power models. Every number carries that label.
4. It calls a difference real only when the min–max ranges are separated, and it states what the measurement does not cover.

**Sample output** (a real run on an Apple M4 Pro laptop):

```
## Green Measurement

**Workload:** driver.py sum-of-squares aggregation · **R:** million records, 300 per run
**Variants:** loop: explicit for-loop (baseline) · builtin: sum() over a generator

**Method:** CodeCarbon 3.3.1, **estimated** (CPU: cpu_load, GPU: Unspecified, RAM: RAM power estimation model); 5 interleaved runs per variant after 1 warm-up
**Machine:** Apple M4 Pro · macOS-26.7.1-arm64-arm-64bit-Mach-O
**Grid:** United States, ~369 gCO₂eq/kWh (CodeCarbon)

| Variant | Energy per run (median, min–max) | Duration (median) | Energy per million records | CO₂eq per million records |
|---|---|---|---|---|
| loop | 54.79 mWh (52.82 mWh–57.63 mWh) | 12.65 s | 182.6 µWh | 67.48 µg |
| builtin | 39.26 mWh (37.64 mWh–40.14 mWh) | 9.22 s | 130.9 µWh | 48.35 µg |

- **builtin vs loop:** -28.3% median energy per run (separated: ranges do not overlap)
- **Idle floor:** 15.4 W average over 12.7 s (compare variant average power: loop 15.6 W, builtin 15.3 W)
- ⚠ No CPU tracking mode found. Falling back on CPU load mode.

**Result:** builtin uses 28% less energy per million records than loop (estimated, ranges separated).
Both variants draw roughly idle-floor power on a single core, so the estimate tracks runtime:
builtin finishes sooner. A measured run (Linux with readable RAPL) would also capture
efficiency differences at equal load.
**Scope:** operational carbon only (E × I) on this machine and grid. Embodied hardware
emissions (M) are not measured. Production hardware, load, and grid will differ.
```

## Prompts to try across workload types

Once you have run one generation and one review, these prompts exercise the breadth of the skill:

**Web frontend**
> Create a React product listing page for a high-traffic e-commerce site. Apply green software patterns for web performance and media efficiency.

**Cloud backend architecture**
> Design the architecture for a webhook processing service that handles bursty traffic — 100k events/hour peak, ~5k events/hour average. Use green software patterns.

**Data pipeline**
> Write a Python script that ingests a 10 GB CSV of customer transactions, cleans them, and writes to object storage. Follow green software patterns.

**AI/ML inference service**
> Set up a text classification service using a pre-trained model. Follow green software patterns for AI/ML workloads.

**Agentic AI system**
> Design a customer-support agent that uses tool calls to look up orders, check policies, and draft replies. Apply the agentic AI patterns from the green-code-skill.

**Code review — Dockerfile**
> Review this Dockerfile against green software patterns:
>
> [paste your Dockerfile]

**Measuring a review fix**
> Measure the energy of this batch job before and after the async refactor you suggested, per 1,000 records.

**Architecture review**
> Review this system design against green software patterns:
>
> [paste your architecture description or diagram summary]

## Getting the best results

A few practices produce better output from the skill:

**Name the workload.** Mentioning "cloud backend," "React frontend," "data pipeline," "AI inference," or "agentic AI" helps Claude select the right pattern reference file quickly and choose relevant patterns.

**Share real context.** Real code, real data shapes, and real constraints (target latency, expected scale, tenancy model, compliance requirements) produce far better recommendations than abstract prompts. If you are working on a specific system, describe it.

**Ask for the trade-off analysis.** If a recommendation does not fit your context, ask "why not X instead?" or "does this apply to a low-traffic internal tool?" The skill is designed to reason through pattern trade-offs collaboratively.

**Iterate.** After an initial review, drill into a specific finding: "elaborate on the async fix — show me the full refactor with error handling and rate limiting." Or ask for prioritization: "which of these findings is highest-impact for my system?"

**Ask for the SCI mapping.** If you want to understand the reasoning, ask "which SCI term does this reduce, and why?" The skill is grounded in the SCI formula and can walk through the causal chain.

## Troubleshooting

**The skill did not trigger.** First check that the skill is installed correctly for your tool — see the tool-specific quickstart in [`getting-started/`](./getting-started/) for install verification steps. Then try invoking the skill by name in your first message ("use the green-code-skill to..."). If it still does not trigger, add one of the description keywords (green, sustainability, carbon, energy efficiency, cost reduction) to your prompt and try again.

**Claude produced code but no Green Notes block.** The skill may have activated partially. Add "with a Green Notes block explaining the green software patterns applied" to your prompt, or ask as a follow-up: "list the green software patterns you applied and cite the canonical pattern URL for each."

**A pattern URL returns 404.** The GSF catalog evolves; a pattern may have been renamed or moved. Ask Claude to verify against the current catalog at https://patterns.greensoftware.foundation/ — the skill is designed to fall back to the index and note when specific URLs have moved.

**Measure results are labelled *estimated*.** CodeCarbon found no hardware energy counters, so it modelled power from CPU utilization. Estimates are useful for comparing variants by runtime and load. For measured numbers, run on Linux with readable RAPL files (`/sys/class/powercap/intel-rapl`), Windows 11 on bare metal, or an NVIDIA/AMD GPU for GPU work.

**Measure mode reports no measurable difference.** The variants' min–max ranges overlapped. Ask for more runs (`--runs 10`) or more work per run. If they still overlap, the change does not move energy enough to show on this machine.

**The recommendations do not fit your context.** Push back on any recommendation that does not match your reality. Example: "this is a low-traffic internal tool used by fewer than 10 people — is server-side rendering actually worthwhile here?" The skill is designed to re-evaluate recommendations against context, surface trade-offs honestly, and refine its guidance.

## Reading further

- Full GSF pattern catalog: https://patterns.greensoftware.foundation/
- SCI specification: https://sci.greensoftware.foundation/
- Green Software Foundation: https://greensoftware.foundation/
- Practitioner course: https://learn.greensoftware.foundation/

Inside this skill package:

- `SKILL.md` — agent-facing router: mode selection, SCI backbone, honesty rules, pattern index
- `modes/write.md`, `modes/review.md`, `modes/measure.md` — per-mode steps and output templates
- `scripts/measure.py` — CodeCarbon measurement harness used by measure mode
- `references/sci-formula.md` — SCI grounding and what each SCI term represents
- `references/patterns-development.md` — 23 Development patterns with detection signals and fixes
- `references/patterns-architecture.md` — 17 Architecture patterns
- `references/patterns-ai-ml.md` — 9 AI/ML model and training patterns + 10 agentic AI workload patterns
- `references/trade-offs.md` — contextual considerations for applying patterns well
