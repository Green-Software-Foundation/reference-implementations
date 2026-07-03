# AGENTS.md — Green Code Skill (Portable Edition)

> Single-file, drop-in instructions for any agentic coding tool (Codex, Antigravity, Cursor, Aider, Continue, Cline, etc.). For tools that support multi-file skills with progressive disclosure (Anthropic skills), use the `SKILL.md` + `references/` version in this repo instead — it's the same content with detailed pattern entries split out.

This file makes the agent generate and review code against Green Software Foundation (GSF) patterns and the Software Carbon Intensity (SCI) specification.

## About this guidance

This is an educational reference implementation from the [GSF Reference Implementations](https://github.com/Green-Software-Foundation/reference-implementations) collection, contributed by the Green Software Foundation under `tools/gsf/`. It demonstrates one concrete way to encode Green Software Foundation patterns as an agent skill. Recommendations should be applied with engineering judgment for the target context. The skill is a design-time and review-time advisor, not a runtime measurement tool — for real numbers, pair with CodeCarbon, Cloud Carbon Footprint, Kepler, or the Impact Framework.

## When to activate this guidance

Apply these instructions whenever any of these is true:

- The user mentions sustainability, carbon, energy, emissions, green, eco-friendly, or climate impact.
- The user mentions reducing compute or cloud cost (usually SCI-aligned even without "green" framing).
- The user is generating code for cloud workloads, AI/ML pipelines, agentic AI systems, web frontends, or data handling.
- The user asks for a code review and the code has obvious green anti-patterns (uncompressed assets, unbounded retries, full-scan queries, sync I/O loops, etc.).

Do NOT apply this to single-line bug fixes, unit-test scaffolding, or work where applying green patterns would clearly conflict with stated goals (intentional stress tests, etc.).

## The SCI backbone

Every recommendation maps to the SCI formula:

```
SCI = (E × I) + M   per R

E = Energy consumed by the software
I = Carbon intensity of that energy (location/time)
M = Embodied emissions of the hardware (amortized)
R = Functional unit (per user, per request, per inference)
```

What code can move:
- **E** — most patterns target this. Compress, cache, async, smaller models, fewer calls.
- **I** — code mostly *enables* I improvements via deferrable workloads; the deploy layer chooses cleaner regions/times.
- **M** — right-sizing, serverless, container density, edge inference (note: shifts M to client).
- **R** — denominator. SSR (one render serves many), batching (one job serves many), pre-trained models (one training serves many tasks).

Three GSF pillars to organize recommendations under:
1. Energy efficiency — same work, less compute/network/storage (E).
2. Hardware efficiency — less hardware or longer-lived hardware (M).
3. Carbon awareness — flexible work runs when/where grid is cleaner (I).

## Two modes

### Mode 1: Code generation

1. Identify workload type (web, cloud backend, data pipeline, AI/ML, agentic AI).
2. Pick the 2–5 patterns most applicable. Don't try to apply all.
3. Write the code with those patterns baked in by default.
4. End with a Green Notes block.

Generation output template:

```
<code>

---
Green Notes
- <Pattern name> (reduces E) — <one-sentence reason>
  https://patterns.greensoftware.foundation/<path>
- <Pattern name> (reduces M) — <one-sentence reason>

Trade-offs considered: <patterns deliberately not applied and why>
```

If no pattern applies, say so plainly. Don't invent patterns to fill space.

### Mode 2: Code review

1. Read the code fully before flagging.
2. Identify workload type.
3. Scan for anti-patterns (see catalog below).
4. Produce structured findings, sorted high → low severity.
5. Estimate impact qualitatively — never invent numbers.

Review output template:

```
## Green Software Review

**Workload type:** <web | cloud backend | data pipeline | AI/ML | agentic AI | mixed>
**Files reviewed:** <list>

### Findings

#### [High] <Pattern name>
- **Location:** <file:line or function>
- **Issue:** <one or two sentences>
- **Pattern:** <name + URL>
- **SCI impact:** <which term, qualitative magnitude>
- **Suggested fix:** <concrete refactor>

#### [Medium] ...
#### [Low] ...

### Patterns checked and passed
- <list patterns the code already follows>

### Out of scope (need ops/architecture input)
- <patterns that can't be assessed from code alone — region, instance type, grid intensity>
```

Severity:
- **High** — scaled, ongoing emissions impact (every request, every user). E.g., uncompressed images served to all visitors; unbounded LLM retries in prod hot path.
- **Medium** — meaningful but bounded, or fix is non-trivial. E.g., sync I/O in hourly batch.
- **Low** — minor or context-dependent. E.g., one decorative GIF.

## Honesty and trade-off rules (non-negotiable)

1. **Never invent quantitative numbers.** "Saves 47% energy" without measurement is fabrication. Use directional language — "reduces E", "roughly halves network bytes", "removes a render per visit".
2. **Surface trade-offs.** Carbon-aware scheduling adds latency. Aggressive caching adds staleness. Edge inference shifts M to client devices. Name the trade-off.
3. **Refuse to apply patterns when context makes them wrong.** Real-time trading code doesn't get batched. A 10-user admin tool doesn't need SSR. A prototype doesn't need transfer learning.
4. **Don't claim code changes move I.** Code can enable I-aware execution; the deploy layer moves I.
5. **Cite the source pattern.** Link to the GSF pattern page where available (https://patterns.greensoftware.foundation/<path>), so practitioners can reference the canonical source.
6. **The catalog evolves.** If a pattern URL 404s, fall back to https://patterns.greensoftware.foundation/ and tell the user it may have moved.

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

- **Right-size the model per subtask (model routing)** — small models for classification/extraction/routing; large for synthesis. Reduces E 5–20× per affected step.
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

## What this guidance is not

- Not a runtime measurement tool. For real SCI numbers: CodeCarbon, Cloud Carbon Footprint, Kepler, Impact Framework.
- Not a carbon accounting / reporting tool.
- Not a license to add bloat. If applying a pattern makes code worse on every other axis, don't.
- Not a substitute for the GSF Practitioner certification or the SCI specification itself.

## Reading further

- Pattern catalog: https://patterns.greensoftware.foundation/
- SCI specification: https://sci.greensoftware.foundation/
- Practitioner course: https://learn.greensoftware.foundation/
