# SCI for AI

A reference implementation of the [Green Software Foundation **SCI for AI
specification**][sci-ai] — demonstrating one way to measure the carbon
and energy footprint of an **LLM inference workload** end-to-end, with
API cost reported alongside as a complementary cost lens.

This is one entry in the GSF
[reference-implementations](https://github.com/Green-Software-Foundation/reference-implementations)
collection, which holds educational, working examples of how GSF
specifications, patterns, and best practices can be applied.

[sci-ai]: https://sci-for-ai.greensoftware.foundation/

## What this is

SCI for AI extends the ISO-adopted base Software Carbon Intensity
specification ([ISO/IEC 21031:2024][iso-21031]) with AI-specific
considerations: functional units suited to ML and generative workloads,
treatment of inference vs training, and distinction between provider
and consumer measurement boundaries. **This project is one runnable
reference implementation of that specification, applied to LLM
inference workloads.** It is one valid approach, not the only
approach — alternative implementations and implementations covering
other AI workload classes (training, computer vision, recommender
systems, etc.) are welcome in the broader collection.

It demonstrates, with real provider data, how to:

- Attribute carbon and energy to a clear **functional unit** of
  useful work, as the SCI for AI specification defines.
- Use **measured** energy via instrumentation tools like
  [EcoLogits][ecologits] when the provider SDK supports it, and a
  calibrated **estimated** fallback otherwise — with each number
  labelled so it's always clear which is which. Alternative
  measurement providers could be substituted by adapting the
  provider layer.
- Apply **location-based** carbon intensity for the actual deployment
  region, not a global average.
- Project per-request impact to **operational scale** so the values
  can be expressed in the units (per day, per month, per year) used
  in sustainability reporting frameworks.
- Ship **recorded fixtures** so the example can be tried locally
  without an API key.

In addition to the SCI for AI measurements, this reference
implementation also tracks **API cost in USD per request** as a
complementary factor. Cost is not part of the SCI for AI
specification — it's a separate lens — but in practice carbon, energy,
and cost are all consequences of the same underlying choices (model,
region, prompt design, caching, batching, etc.), so reporting them
side by side makes the same engineering decision evaluable against
both sustainability and finance criteria.

The source is compact and the SCI formula lives in a single file, so
the methodology can be inspected end-to-end. Every number in this
README comes from a committed fixture you can replay locally.

> **Status: Reference implementation.** This is an educational,
> working end-to-end example of how the SCI for AI specification can
> be applied to LLM inference. Different workloads and teams will
> reasonably make different choices about measurement provider,
> functional unit, and pipeline structure; the methodology document
> records the choices made here so readers can evaluate them against
> their own context.

[iso-21031]: https://www.iso.org/standard/86612.html
[ecologits]: https://ecologits.ai/

## Why this matters

Every team running production LLM workloads is making decisions whose
sustainability and financial consequences are usually treated
separately but are physically the same decision:

- **Carbon** — what the inference emitted, given when and where it ran
- **Energy** — how much electricity it actually consumed
- **Cost** — what the provider charged

Most observability stacks track the third in detail. Carbon and
energy are commonly tracked at a coarser granularity, often using
provider-level summaries or estimates that don't tie back to a
specific engineering change. Existing tooling tends to focus on one
dimension at a time: finOps tools surface dollars, sustainability
tools surface CO₂, but connecting a specific design choice — a model
swap, a prompt revision, a region shift — to its impact across all
three dimensions still requires bringing them into a common frame.

SCI for AI gives the carbon and energy dimensions a shared
measurement frame. This reference implementation implements that frame
and reports cost alongside it, so engineering teams can evaluate a
single change — a model swap, a region shift, a prompt revision, a
caching strategy — against carbon, energy, and cost together in one
report.

## Scope: what SCI for AI applies to

SCI for AI is a measurement specification, not a single recipe. It
applies to every design and operational lever an AI team has:

| Lever                       | Example question SCI for AI answers                                       |
| --------------------------- | ------------------------------------------------------------------------- |
| Model selection             | What is the per-request emissions difference between gpt-5.4 and gpt-4o-mini for this workload? |
| Region selection            | Does shifting from us-central1 (~0.41) to europe-north1 (~0.06) help?     |
| Prompt design               | Does a shorter prompt reduce per-request emissions?                       |
| Pipeline architecture       | Single big call vs multiple smaller calls — which has the lower footprint? |
| Caching & routing           | How much do cache hits and small-model routing reduce intensity?          |
| Batching                    | Does batched / asynchronous processing change the per-request footprint?  |
| Fine-tuning vs prompting    | Is a fine-tuned smaller model lower-footprint than prompting a big one?   |
| Hardware                    | Is ARM, smaller GPUs, or quantised inference better for this workload?    |
| Carbon-aware scheduling     | Can deferrable work be shifted to lower-carbon hours?                     |

**This reference implementation ships with a prompt-optimization demo.**
Prompt optimization is one example of how SCI for AI can be applied to
a real workload — chosen because the before/after change is
self-contained and easy to reproduce. The underlying measurement
library is provider-, model-, region-, and lever-agnostic; the same
`CallMeasurement` / `aggregate` / `compare` primitives can be used
to evaluate any of the levers above.

## The bundled demo: prompt-optimization comparison

For any sustainability-related query, the bundled `compare` command
runs a three-phase **Planner → Collector → Writer** pipeline twice —
once with verbose baseline prompts and once with optimized prompts —
and reports the delta in carbon, cost, and energy per request, then
projects the impact to operational scale (default: 10,000 requests/day).

Example output (real recording from a `gpt-4o-mini` run with EcoLogits,
committed at `docs/fixtures/openai-gpt-4o-mini.json`):

```
================================================================
                  SCI for AI — Comparison Report
================================================================
Query: How can I reduce the energy consumption and carbon footprint of a
Python web service that processes user-uploaded images for resizing and
format conversion?
Energy source: measured (baseline) / measured (optimized) — measured via EcoLogits
Model: gpt-4o-mini  Region: us-central1  LLM calls per pipeline run: 3 / 3

PRIMARY METRIC — SCI per request
In this tool, one "request" = one full report generation = one user query.
The pipeline makes 3 LLM calls (Planner → Collector → Writer) internally,
but the user-facing unit of work is the generated report. R = 1.
This unit stays consistent across prompt, region, and model changes.

Metric                          Baseline        Optimized        Delta
-----------------------------------------------------------------------
SCI per request                102.526 mg        54.620 mg       -46.7%
Cost per request                $0.002401         $0.001203       -49.9%
Total emissions                102.526 mg        54.620 mg       -46.7%

================================================================
      SCALE PROJECTION  —  10,000 requests / day
================================================================
                       Baseline      Optimized        Savings
-----------------------------------------------------------------------
Per day — emissions    1.025 kg      546.201 g       479.060 g
Per day — cost           $24.01         $12.03           $11.97
Per month — emissions 30.758 kg      16.386 kg        14.372 kg
Per month — cost        $720.23        $361.03          $359.19
Per year — emissions 374.220 kg     199.363 kg       174.857 kg
Per year — cost         $8,763         $4,393           $4,370

Annual savings translate to:
  • 1,023 km of car driving avoided
  • 16 days of average household electricity
  • 8 trees' worth of annual CO₂ sequestration
```

Three things the output makes explicit:

1. **Per request, not per token.** "One request" = one report
   generated = one user query. The internal LLM calls are an
   implementation detail. The per-request metric stays consistent
   across prompt, region, and model changes.
2. **Cost reported alongside carbon.** USD per request and projected
   annual spend appear next to the carbon figures so a single change
   can be evaluated against both lenses.
3. **Operational scale.** Per-request numbers in milligrams and
   fractions of a cent are abstract; the same numbers at 10,000
   requests/day in kilograms and thousands of dollars are easier to
   reason about for both sustainability and finance contexts.

## What the real data shows

The same query, same prompts, recorded across three OpenAI models with
real EcoLogits-measured energy. Fixtures live in `docs/fixtures/` and
the tables below are generated from them by
`scripts/build_cross_model_table.py`.

### Per-request results (one report generation)

| Model | Type | Baseline emissions | Optimized | Reduction | Baseline cost | Optimized cost | Cost reduction |
|---|---|---|---|---|---|---|---|
| `gpt-4o-mini` | non-reasoning | 102.5 mg | 54.6 mg | **-46.7%** | $0.0024 | $0.0012 | **-49.9%** |
| `gpt-4o` | non-reasoning | 2.2 g | 1.3 g | **-41.6%** | $0.0364 | $0.0207 | **-43.1%** |
| `gpt-5.4` | reasoning | 11.0 g | 7.1 g | **-35.2%** | $0.2166 | $0.1378 | **-36.4%** |

### At 10,000 requests / day — annualized

| Model | Annual emissions (baseline) | Annual cost (baseline) | Annual CO₂ savings | Annual $ savings | Car-km avoided |
|---|---|---|---|---|---|
| `gpt-4o-mini` | 374 kg | $8,763 | **175 kg** | **$4,370** | **1,023 km** |
| `gpt-4o` | 7,849 kg | $132,833 | **3,266 kg** | **$57,232** | **19,100 km** |
| `gpt-5.4` | 40,054 kg | $790,672 | **14,098 kg** | **$287,666** | **82,444 km** |

> **Note on caching.** These projections assume every request is
> processed from scratch. In practice, prompt caching — whether
> applied implicitly by the provider, explicitly through provider
> APIs, or via a third-party caching layer — would reduce both the
> baseline and the optimized numbers further, since repeated prefixes
> would no longer be re-computed. This reference implementation does not
> model caching, so the figures here represent an uncached upper
> bound. Caching is one of the levers listed in the scope table above
> and could be measured separately using the same primitives.

**Absolute savings scale with the baseline footprint.** A given
percentage reduction translates to larger absolute changes in
carbon, energy, and cost for models with a higher per-request
baseline. The chosen lever and the expected magnitude of change will
depend on the specific workload.

A few observations from this data:

- **The prompt change reduced metrics on the reasoning model
  (`gpt-5.4`) as well.** The reduction was smaller in percentage
  terms (~35% vs ~47% on `gpt-4o-mini`), but larger in absolute
  terms because the baseline numbers are larger. Note that for
  reasoning models, output tokens billed at the output rate include
  internal reasoning tokens, so the per-request effect of any prompt
  change depends on how the reasoning budget responds.
- **`gpt-5.4` measures roughly 100× the per-request emissions of
  `gpt-4o-mini`.** This is driven by a combination of model size,
  reasoning tokens, and how EcoLogits models per-token energy for
  larger architectures. The ratio is in the same order of magnitude as
  the cost ratio (~90×).
- **All three runs report `measured` energy via EcoLogits.** The
  measurement path is the same for each row, so within this table
  the comparison is consistent across models.

To regenerate the tables after re-recording fixtures or adding a new
model, run:

```bash
python scripts/build_cross_model_table.py
```

## Quick start

The core measurement library and the mock provider have **zero
required dependencies**. You can try the CLI immediately:

```bash
git clone https://github.com/Green-Software-Foundation/reference-implementations
cd reference-implementations/specifications/sci-for-ai/gsf/llm-inference
pip install -e .
sci-for-ai compare --query "How do I reduce energy use in image processing?"
```

> The default `--provider mock` runs a *synthetic* model — useful for
> trying the CLI, but the numbers are not measured. For real numbers,
> use a recorded fixture (next) or your own API key (further below).

### Run against a recorded fixture (no API key)

To see real numbers from an actual OpenAI run measured by EcoLogits,
replay one of the committed fixtures:

```bash
sci-for-ai compare \
    --provider recorded \
    --fixture docs/fixtures/openai-gpt-4o-mini.json \
    --query "How do I reduce energy use in image processing?"
```

The report header will read `Energy source: measured — measured via
EcoLogits`. Three fixtures are committed (`gpt-4o-mini`, `gpt-4o`,
`gpt-5.4`); replay any of them to verify the numbers in the tables
above.

### Run against a live provider

```bash
# Anthropic
pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY=...
sci-for-ai compare --provider anthropic --query "your question"

# Google Gemini
pip install -e ".[gemini]"
export GEMINI_API_KEY=...
sci-for-ai compare --provider gemini --query "your question"

# OpenAI — and record the result for replay
pip install -e ".[openai]"
export OPENAI_API_KEY=...
sci-for-ai compare --provider openai --model gpt-4o-mini \
    --query "your question" --record-to my-run.json
```

See [docs/RECORDING_REAL_DATA.md](docs/RECORDING_REAL_DATA.md) for the
full recording walkthrough.

## Programmatic use

The bundled `compare` command is one way to use the library. For your
own analysis — region comparison, model comparison, caching study,
etc. — wire up the primitives directly:

```python
from sci_for_ai import build_provider, CallMeasurement, aggregate, compare

# Construct a provider for the workload's deployment region
provider = build_provider("anthropic", region="europe-north1")  # lower-intensity region

# Run your own workload (e.g. a single call or a multi-call pipeline),
# collecting a CallMeasurement per LLM call. The `compare_prompt_sets`
# helper below shows one example of doing this for a baseline-vs-optimized
# pair; for other levers (model, region, caching, etc.) build the
# measurement list yourself.

# Aggregate and compare arbitrary measurement sets
baseline_totals = aggregate(baseline_measurements)
optimized_totals = aggregate(optimized_measurements)
delta = compare(baseline_totals, optimized_totals)

print(f"Emissions change: {delta['total_emissions_kg']['reduction_pct']:.1f}%")
print(f"Cost change:      {delta['cost_usd']['reduction_pct']:.1f}%")
```

The bundled prompt-comparison helper does this for the specific case
of baseline-vs-optimized prompts:

```python
from sci_for_ai import build_provider, BASELINE, OPTIMIZED, compare_prompt_sets

provider = build_provider("anthropic", region="europe-north1")
result = compare_prompt_sets(provider, BASELINE, OPTIMIZED, "your query")
```

## The SCI formula

```
SCI = (E × I + M) / R
```

- **E** — energy (kWh) measured (EcoLogits) or estimated (model-card)
- **I** — grid carbon intensity (kgCO₂eq/kWh) for the deployment region
- **M** — embodied emissions (kgCO₂eq) from provider data or a 12% heuristic
- **R** — functional unit (practitioner's choice per the spec)

This tool reports SCI at three R values: **per request** (the
headline, one full pipeline run), per individual LLM call, and per
token. The headline uses per-request because it stays constant when
prompts, models, or regions change.

See [docs/SCI_METHODOLOGY.md](docs/SCI_METHODOLOGY.md) for the full
sources, scope, and assumptions behind each input.

## Measured vs estimated energy

By default, energy comes from a per-model **kWh-per-token table**
(`src/sci_for_ai/energy.py`) — a useful starting point, but a coarse
estimate calibrated against real EcoLogits measurements.

For **measured** energy, install [EcoLogits][ecologits] (included in
every provider extra). It instruments the provider SDK and attaches
real per-call energy and embodied figures to every response. The tool
detects EcoLogits automatically, uses it when available, and labels
each run as `measured` or `estimated` in the report so the source of
each number is transparent.

```bash
pip install ecologits   # already included with [anthropic], [gemini], [openai]
```

EcoLogits supports anthropic, google-genai (Gemini), openai, cohere,
mistralai, and huggingface-hub.

## Architecture

```
src/sci_for_ai/
├── sci.py        # Pure SCI math: (E*I + M)/R. No I/O. Self-contained and testable.
├── energy.py     # Per-model kWh/token profiles with citations.
├── pricing.py    # Per-model USD/token table, citations included.
├── scale.py      # Per-request → per-day/month/year projection.
├── providers.py  # Lazy-imported adapters for Anthropic / Gemini / OpenAI / Mock / Recorded.
├── prompts.py    # Baseline + optimized prompt sets for the bundled demo.
├── pipeline.py   # Orchestration; short-circuits on empty outputs.
├── report.py     # ANSI-coloured terminal report formatter.
└── __main__.py   # CLI entrypoint.
```

Each module has a single responsibility. The SCI calculation itself is
in one file, kept short so the methodology can be read alongside the
specification.

## Design principles

The implementation follows the principles the tool measures:

| Principle | How it's applied |
|---|---|
| **Minimal dependencies** | Core has **zero** required deps. Provider SDKs are optional extras. |
| **Lazy imports** | Provider SDKs load only when their adapter class is instantiated. |
| **Single-pass aggregation** | One loop over measurements, not five. |
| **Deterministic tests** | 84 tests in <0.2 s; no network calls; `MockProvider` for offline CI. |
| **Slim Docker image** | Multi-stage build, no build tooling in runtime, non-root user. |
| **Pluggable carbon data** | Region table is data, not code. Update annually from provider sustainability reports. |
| **Reproducible results** | Every number in this README comes from a committed fixture anyone can replay. |

## Reproducibility

Run with Docker:

```bash
docker build -t sci-for-ai .
docker run --rm sci-for-ai compare --query "your question" --provider mock
```

Run the full test suite:

```bash
pip install -e ".[dev]"
pytest
```

84 tests, <0.2 second runtime, no network required.

## Contributing

Issues and pull requests welcome. When proposing changes to the energy
or carbon-intensity tables, please include the citation so reviewers
can verify the source.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

Methodology follows the Green Software Foundation [SCI for AI
specification][sci-ai], which extends the base
[Software Carbon Intensity (SCI) specification][gsf-sci]
([ISO/IEC 21031:2024][iso-21031]) with AI-specific considerations.
The optional measured-energy path uses [EcoLogits][ecologits].

[gsf-sci]: https://sci.greensoftware.foundation/
