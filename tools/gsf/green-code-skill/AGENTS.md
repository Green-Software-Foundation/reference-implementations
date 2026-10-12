# AGENTS.md — Green Code Skill (Portable Edition)

> Single-file edition for agentic coding tools that read one instruction file (Codex, Antigravity, Cursor, Aider, Continue, Cline). Tools with multi-file skills should use `SKILL.md` + `modes/` + `references/` from the same package. An educational reference implementation from [GSF Reference Implementations](https://github.com/Green-Software-Foundation/reference-implementations) (`tools/gsf/`).

Green Software Foundation (GSF) patterns and the Software Carbon Intensity (SCI) specification, applied in three modes: **write**, **review**, and **measure**.

## When to activate

- The user mentions carbon, energy, or sustainability.
- The user asks to cut compute or cloud cost (usually SCI-aligned even without "green" framing).
- The user wants to measure or verify the energy impact of code or a change.
- The user is building cloud backends, web frontends, data pipelines, AI/ML, or agentic AI systems.
- A code review turns up obvious green anti-patterns (uncompressed assets, unbounded retries, full-scan queries, sync I/O loops).

Stand down for single-line fixes, test scaffolding, and work where green patterns would defeat the goal (an intentional stress test).

## Pick one mode

| The user wants | Mode |
|---|---|
| New code, a refactor, or a design | **Write** |
| Existing code audited | **Review** |
| Numbers: energy or emissions of real runs, before/after a change | **Measure** |

Follow only that mode's section and finish its output before starting another mode. Modes hand off. A review finding or a written change becomes a measure baseline when the user wants evidence. A measurement with no measurable difference goes back to review for a better candidate.

## SCI backbone

```
SCI = (E × I) + M   per R
```

- **E**: energy the software consumes. Most patterns target E: compress, cache, async, smaller models, fewer calls.
- **I**: carbon intensity of that energy (where and when it runs). The deploy layer moves I. Code only *enables* I-aware execution by making work deferrable.
- **M**: embodied hardware emissions, amortized. Moves with right-sizing, serverless, and container density. Edge inference shifts M onto client devices.
- **R**: the functional unit (per request, per user, per inference). It is the denominator: SSR (one render serves many), batching, and pre-trained models improve R.

Organize recommendations under the three GSF pillars: **energy efficiency** (E), **hardware efficiency** (M), **carbon awareness** (I).

## Honesty rules (every mode)

1. **Numbers come from measurement.** Quote a figure only from a Measure-mode run or data the user supplied, and name its method alongside it. Everywhere else, use *directional* language: "reduces E for every request", "roughly halves network bytes", "removes a render per visit".
2. **Name the trade-off** beside each recommendation: latency from carbon-aware scheduling, staleness from caching, M shifted to clients by edge inference.
3. **Context beats the pattern.** Real-time paths stay unbatched, a 10-user admin tool stays client-rendered, a prototype trains nothing. Check the trade-offs section before applying anything aggressive.
4. **Code moves E, M, and R.** For I, say the code *enables* cleaner scheduling or regions.
5. **Cite the pattern** with its URL under https://patterns.greensoftware.foundation/. If a URL 404s, link the catalog root and say the pattern may have moved.

## Mode: Write

New code, refactors, and designs with green patterns built into the first draft.

1. **Name the workload**: web frontend, cloud backend, data pipeline, AI/ML, agentic AI, or a mix. Note the scale signals the user gave (traffic, data volume, call rate), because they decide which patterns pay off.
2. **Shortlist 2–5 patterns** from the catalog below. Keep a pattern only if it passes the four-part test in the trade-offs section. Done when every shortlisted pattern passes and every rejected candidate has a one-line reason.
3. **Write the code with the shortlist as defaults**, so the patterns are visible in the code itself: bounded retries, async I/O, paginated and projected queries, compressed payloads, a cache in front of LLM calls.
4. **Append Green Notes.** Done when every applied pattern has an entry with its SCI term and URL, and every rejected candidate appears under *Trade-offs considered*.

```
<code>

---
Green Notes
- <Pattern name> (reduces E) — <one sentence on why it pays off here>
  https://patterns.greensoftware.foundation/<path>

Trade-offs considered: <rejected patterns and why, e.g. "skipped SSR: internal admin tool, <10 concurrent users">
```

When no pattern fits, write `Green Notes: no pattern applies — <reason>` in place of the block.

## Mode: Review

Existing code audited against green patterns, reported as severity-ranked findings.

1. **Read every file in scope end to end** before flagging anything. Done when you can list the files reviewed.
2. **Name the workload(s)** and take the matching catalog sections below.
3. **Sweep the detection signals.** Check each pattern in those sections against the code and sort it into one bucket: *finding*, *pass*, *out of scope* (needs ops input: region, instance type, grid), or *not applicable* (no such code). Done when every pattern in those sections sits in exactly one bucket.
4. **Test each finding against context** using the trade-offs section. Drop or downgrade findings the context makes wrong.
5. **Rate severity and write the report**, sorted High → Low. Leave *not applicable* out.

Severity:
- **High**: scaled, ongoing emissions on every request or every user. Examples: uncompressed images served to all visitors; unbounded LLM retries on a production hot path.
- **Medium**: meaningful but bounded, or the fix is non-trivial. Example: sync I/O in an hourly batch job.
- **Low**: minor or context-dependent. Example: one decorative GIF.

SCI impact stays *directional*. When the user disputes a High finding's impact or wants numbers, offer Measure mode with the current code as baseline and the fix as variant.

```
## Green Software Review

**Workload type:** <web | cloud backend | data pipeline | AI/ML | agentic AI | mixed>
**Files reviewed:** <list>

### Findings

#### [High] <Pattern name>
- **Location:** <file:line or function>
- **Issue:** <one or two sentences>
- **Pattern:** <name + URL>
- **SCI impact:** <which term, directional magnitude>
- **Suggested fix:** <concrete refactor>

#### [Medium] ...
#### [Low] ...

### Patterns checked and passed
- <patterns the code already follows>

### Out of scope (need ops/architecture input)
- <patterns code alone can't settle: region, instance type, grid intensity>
```

## Mode: Measure

Energy and operational carbon of real runs, measured with [CodeCarbon](https://github.com/mlco2/codecarbon). Usually a before/after comparison: a **baseline** and one or more **variants** doing the same work. CodeCarbon sees **this machine only**: LLM API inference, remote databases, and other services do not appear in its numbers. For API-bound code, use call and token counts as the proxy for the remote side and say so.

1. **Fix R and the variants.** Agree with the user on the code path, the functional unit R, and how many units one run performs. Done when each variant is one shell command that performs the same R units of work, exits 0, and is safe to repeat. Wrap a Python function in a driver script that loops over it. Use the same fixed inputs everywhere and no network. Size each run to last **10 s or more**. Before measuring commands that write external state or call paid APIs, confirm with the user.
2. **Run the harness**: `measure.py` from the green-code-skill package's `scripts/` folder ([source](https://github.com/Green-Software-Foundation/reference-implementations/tree/main/tools/gsf/green-code-skill/scripts)); look for a copy in the project first.
   ```bash
   uv run <path>/measure.py --variant baseline="python driver.py --impl current" \
     --variant batched="python driver.py --impl batched" --units 1000 --unit-label record --country DEU
   ```
   Without uv, install `codecarbon>=3,<4` into a scratch venv and leave the project's dependency files untouched. Pass `--country` (ISO alpha-3) for the grid where the code runs, because IP geolocation follows VPNs. Without the harness, build the equivalent: one CodeCarbon task per run (`start_task`/`stop_task`, `tracking_mode="machine"`), variants interleaved after a warm-up, median and min–max energy per variant, and the CPU tracking method read from CodeCarbon's log. Done when the harness exits 0 and prints its summary.
3. **Read the Method line before the numbers.** The run is **measured** (hardware counters: RAPL, Windows EMI, PowerMetrics, NVML, AMDSMI) or **estimated** (CodeCarbon's CPU-load or TDP models). Carry that label onto every number. Estimated energy tracks runtime and CPU load and misses efficiency gains at equal load. When the run is estimated, tell the user that Linux with readable RAPL, Windows 11 on bare metal, or NVIDIA/AMD GPUs give measured readings.
4. **Judge the difference.** Compare energy, not emissions: every variant ran under the same I. A difference counts only when the min–max ranges are **separated**; overlapping ranges mean "no measurable difference at this run count". When a variant's average power sits close to the idle floor, the measured difference is mostly runtime. Done when every harness warning is resolved by a re-run or carried into the report.
5. **Report:**
   ```
   ## Green Measurement

   **Workload:** <code path> · **R:** <functional unit>, <N> per run
   **Variants:** <name: what changed>, baseline first

   <harness summary, pasted unchanged>

   **Result:** <variant> uses <X>% less energy per <unit> than <baseline> (<measured|estimated>, ranges separated) | no measurable difference at <runs> runs.
   **Scope:** operational carbon only (E × I) on this machine and grid. M not measured. Production hardware, load, and grid will differ. <Remote work not captured, if any.>
   ```

## Pattern catalog — one-line summaries

For full detail on any pattern, the agent can fetch the URL.

### Development (23 patterns)

**Data handling**
- Avoid tracking unnecessary data — remove duplicate/unused trackers, sample, aggregate. → /development/data-handling/avoid-tracking-unnecessary-data
- Cache static data — HTTP cache headers, CDN, in-memory cache for repeat reads. → /development/data-handling/cache-static-data
- Compress stored data — DB column compression, gzip/zstd objects, Parquet/Avro. → /development/data-handling/compress-stored-data
- Compress transmitted data — gzip/Brotli on responses and large request bodies. → /development/data-handling/compress-transmitted-data
- Reduce transmitted data — field selection, pagination, sparse fieldsets. → /development/data-handling/reduce-transmitted-data

**Media & code efficiency**
- Defer offscreen images — `loading="lazy"`, Intersection Observer. → /development/media-and-code-efficiency/defer-offscreen-images
- Deprecate GIFs — MP4/WebM with `<video autoplay muted loop playsinline>`. → /development/media-and-code-efficiency/deprecate-gifs
- Optimize image size — `srcset` + `sizes`, image CDN, match output to display. → /development/media-and-code-efficiency/properly-sized-images
- Remove unused CSS — PurgeCSS, Tailwind JIT, dead-code elimination. → /development/media-and-code-efficiency/remove-unused-css
- Serve images in modern formats — `<picture>` with AVIF → WebP → JPEG. → /development/media-and-code-efficiency/serve-images-in-modern-formats
- Use compiled languages — for CPU-bound hot paths only (Go, Rust, .NET AOT). → /development/media-and-code-efficiency/use-compiled-languages

**Web performance**
- Avoid excessive DOM size — virtualize lists, paginate, fewer wrapper divs. → /development/web-performance/avoid-excessive-dom-size
- Avoid chaining critical requests — `rel="preload"`, inline critical CSS. → /development/web-performance/avoid-chaining-critical-requests
- Enable text compression — gzip or Brotli at server/CDN. → /development/web-performance/enable-text-compression
- Keep request counts low — bundling, HTTP/2 multiplexing, SVG sprites. → /development/web-performance/keep-request-counts-low
- Minify web assets — esbuild/terser/swc; don't ship source maps. → /development/web-performance/minify-web-assets
- Minimize main thread work — Web Workers, `requestIdleCallback`, push work server-side. → /development/web-performance/minimize-main-thread-work
- Use server-side rendering for high-traffic pages — SSR/SSG for marketing/landing. → /development/web-performance/use-server-side-rendering

**Cloud & deployment**
- Minimize deployed environments — ephemeral PR envs, scale staging down, shut down non-prod nightly. → /development/minimizing-deployed-environments
- Terminate TLS at border gateway — only if threat model permits. → /development/evaluate-whether-to-use-TLS-termination
- Use async network calls — `httpx`/`aiohttp`/`WebClient`, `Promise.all`. → /development/use-async-instead-of-sync

**AI/ML (Dev category)**
- Leverage pre-trained models & transfer learning — start from foundation model, LoRA. → /development/pre-trained-transfer-learning
- Use sustainable regions for AI/ML training — pick low-carbon-intensity regions/windows. → /development/leverage-sustainable-regions

### Architecture (17 patterns)

**System topology**
- Adopt serverless for AI/ML — scale-to-zero inference (SageMaker Serverless, Vertex, Modal). → /architecture/system-topology/serverless-model-development
- Choose region closest to users — multi-region or global CDN edge. → /architecture/system-topology/choose-region-closest-to-users
- Containerize workloads — pack on shared orchestrator, right-size requests/limits. → /architecture/system-topology/containerize-your-workload-where-applicable
- Implement stateless design — externalize state, sticky-session-free. → /architecture/system-topology/implement-stateless-design
- Queue non-urgent processing requests — accept-then-queue, steady worker consumption. → /architecture/system-topology/queue-non-urgent-requests
- Reduce network traversal between VMs — co-locate tightly coupled services, less chatter. → /architecture/system-topology/reduce-network-traversal-between-VMs
- Run AI models at the edge — CoreML, TFLite, ONNX Runtime Mobile, TensorRT edge. → /architecture/system-topology/energy-efficent-ai-edge
- Scale logical components independently — decompose where load profiles differ. → /architecture/system-topology/scale-logical-components-independently
- Use a service mesh only if needed — selective application, not mesh-wide. → /architecture/system-topology/evaluate-using-a-service-mesh

**Technology selection**
- Evaluate other CPU architectures — benchmark on ARM (Graviton, Cobalt, Axion). → /architecture/technology-selection/evaluate-other-cpu-architectures
- Optimize AI/ML model size — quantize (INT8/INT4/FP8), prune, distill, LoRA. → /architecture/compress-ml-models-for-inference
- Select energy-efficient AI/ML framework — ONNX Runtime, TensorRT, vLLM, TGI, llama.cpp. → /architecture/technology-selection/energy-efficent-framework
- Right hardware for AI/ML training — profile GPU utilization, consider MIG. → /architecture/technology-selection/right-hardware-type
- Use cloud-native processor VMs — ARM-based for scale-out workloads. → /architecture/technology-selection/use-energy-efficient-hardware
- Use efficient file formats for AI/ML — Parquet, Arrow, TFRecord, WebDataset, safetensors. → /architecture/technology-selection/efficent-format-for-model-training
- Use energy-efficient AI/ML models — match model size to task, routing pattern. → /architecture/technology-selection/energy-efficent-models
- Use serverless cloud services — FaaS, serverless containers, serverless databases. → /architecture/technology-selection/use-serverless

### Agentic AI patterns

Applied to LLM-driven orchestration, agentic loops, and tool-calling workflows. These patterns target the energy and emissions profile of agentic AI systems, where each loop iteration is a model call and call counts can compound rapidly across planning, retries, and tool invocations.

- **Right-size the model per subtask (model routing)** — small models for classification/extraction/routing; large for synthesis. Reduces E on every routed step.
- **Cap the retry budget** — max attempts 3–5, exponential backoff with hard ceiling, retry only transient errors. Prevents runaway loops.
- **Bound planning and reasoning depth** — `max_iterations` on agent loops (typically 5–10), break on repeated states.
- **Cache LLM responses** — exact-match cache (hash of prompt+params); semantic cache (embedding similarity) for near-duplicates.
- **Use provider prompt caching** — for stable system prompts, RAG context, tool schemas.
- **Batch tool calls / parallelize independent steps** — dispatch independent tools in parallel where the framework supports it.
- **Pre-filter retrieval before reranking** — two-stage: cheap recall → expensive precision rerank on top-N.
- **Stop generation when sufficient** — set `max_tokens`, use stop sequences, prompt for concise answers.
- **Prefer structured output over multi-turn negotiation** — structured-output APIs with schema validation; one call, one validation pass.
- **Detect and break tool-call loops** — hash (tool_name, args) per iteration; break on repeats or oscillation.

## Trade-offs — when NOT to apply a pattern

Apply a pattern only when all four hold:
1. It actually reduces SCI for *this* workload.
2. It doesn't make the code worse on correctness, security, readability, or maintainability.
3. The savings compound (per-request, per-user, per-inference).
4. The context tolerates the trade-off.

Common mistakes to avoid:

- **Green-washing low-traffic code** — SSR, advanced bundling, edge caching only pay off at scale.
- **Mandating compiled languages for cold paths** — applies to CPU-bound hot paths only.
- **Aggressive caching where freshness matters** — pricing, balances, live scores must not be cached without invalidation.
- **Edge inference at any cost** — it shifts M to client devices; surface that trade-off.
- **TLS termination changes without threat-model check** — defense-in-depth and compliance can trump CPU savings.
- **Premature serverless adoption** — steady-state high-throughput may do worse on serverless.
- **Quantization without evaluation** — accuracy drop can trigger retries that wipe out savings.
- **Batching real-time workloads** — never apply to chat, trading, search-as-you-type.
- **Removing analytics the business needs** — sample/aggregate, don't blindly delete.
- **Eliminating dev environments** — pattern says *minimize*, not *eliminate*; prod incidents have emissions cost too.

## Reading further

- Pattern catalog: https://patterns.greensoftware.foundation/
- SCI specification: https://sci.greensoftware.foundation/
- Practitioner course: https://learn.greensoftware.foundation/
