# SCI for AI — Methodology

This document is the technical companion to the project README. It
walks through how this reference implementation measures the carbon and
energy footprint of an LLM inference workload, how it sources each
input (E, I, M, R), and how the per-request, per-call, and per-token
results in the reports are computed.

## 1. The standard this implements

This project implements the [**SCI for AI specification**][sci-ai], the
Green Software Foundation's standard for measuring the carbon footprint
of AI systems. SCI for AI **extends** the base Software Carbon
Intensity specification — [ISO/IEC 21031:2024][iso-21031] — with
AI-specific considerations: functional units suited to ML and
generative workloads, treatment of inference vs training, and
distinction between provider and consumer measurement boundaries.

The base SCI formula is unchanged:

```
SCI = (E × I + M) / R
```

| Symbol | Meaning                                                                | Units              |
| ------ | ---------------------------------------------------------------------- | ------------------ |
| **E**  | Energy consumed by the software                                        | kWh                |
| **I**  | Location-based carbon intensity of the electricity used                | kgCO₂eq / kWh      |
| **M**  | Embodied emissions of the hardware, amortised across the functional unit | kgCO₂eq          |
| **R**  | Functional unit — the unit of useful work the practitioner chooses     | varies             |

The reports include both the SCI value (a per-unit-of-work intensity)
and the absolute totals (energy, emissions, cost) that go into it.

[sci-ai]: https://sci-for-ai.greensoftware.foundation/
[iso-21031]: https://www.iso.org/standard/86612.html

## 2. How each input is computed

### E — Energy in kWh

Two paths, in order of preference:

1. **Measured.** When a provider's SDK is instrumented by
   [EcoLogits][ecologits], the per-call energy and embodied figures
   are read directly from the SDK's response. This is always preferred
   when available. EcoLogits currently supports anthropic,
   google-genai (Gemini), openai, cohere, mistralai, and
   huggingface-hub.
2. **Estimated.** When EcoLogits isn't installed or doesn't recognise
   the model, the tool falls back to a per-model **kWh-per-token
   table** (`src/sci_for_ai/energy.py`) calibrated against measured
   data. Every report labels each call as `measured` or `estimated`
   so the source of each number is transparent.

The estimated per-token figures in this project reflect the
methodology used by current instrumentation tools (such as EcoLogits)
and the published literature on present-day transformer inference.
They typically model output tokens as more energy-intensive than input
tokens because today's autoregressive decoding generates output tokens
sequentially while input tokens are processed in parallel. The exact
ratio and per-token values will evolve as model architectures, serving
infrastructure, and measurement methodologies change — for example,
speculative decoding, parallel decoding, mixture-of-experts variants,
or KV-cache optimizations all affect per-token energy in ways that
aren't reflected in a static lookup table. The profiles in
`src/sci_for_ai/energy.py` are intended as a calibrated starting
point and are designed to be refreshed as better data becomes
available — including by registering a custom profile for a specific
deployment.

To register a custom profile:

```python
from sci_for_ai import ModelEnergyProfile, register_model_energy

register_model_energy(ModelEnergyProfile(
    model_id="my-fine-tuned-model",
    kwh_per_input_token=2.0e-8,
    kwh_per_output_token=1.2e-7,
    source="Measured on-prem, 2026-Q1",
))
```

### I — Carbon intensity in kgCO₂eq/kWh

The tool uses **location-based** intensity — the average grid mix
where the workload physically runs — rather than **market-based**
intensity, which credits renewable purchases. The location-based
figure reflects the emissions associated with the electricity
actually drawn at the meter.

Built-in regions:

| Region          | I       | Source / note                                          |
| --------------- | ------- | ------------------------------------------------------ |
| world-average   | 0.475   | IEA global average — default when region is unknown    |
| us-central1     | 0.413   | Google Cloud Iowa                                      |
| us-west1        | 0.078   | Google Cloud Oregon (hydro-dominant grid)              |
| europe-west1    | 0.167   | Belgium                                                |
| europe-north1   | 0.058   | Finland (nuclear and hydro grid)                       |
| asia-south1     | 0.708   | Mumbai (predominantly thermal generation)              |
| asia-southeast1 | 0.408   | Singapore                                              |

These are sensible defaults but not authoritative. Refresh them
annually from your cloud provider's published sustainability data;
provider-published figures supersede the table.

### M — Embodied emissions in kgCO₂eq

Embodied emissions cover the manufacturing, shipping, and end-of-life
impact of the hardware, amortised across all the work the hardware
performs over its lifetime. Because that amortisation depends on
infrastructure data that providers don't always publish, the embodied
term is the input with the widest range of practical approaches.

Two approaches, in order of preference:

1. **Provider-reported.** When EcoLogits returns an embodied figure
   for a given call, it's used as-is.
2. **Heuristic.** Otherwise the tool estimates M as **12% of
   operational emissions**. Published studies of cloud inference put
   the embodied share at roughly 8–15%; 12% sits in the middle of that
   range.

You can tune the fraction with `estimate_embodied_kg(operational_kg,
fraction=0.10)`. Any change to the assumption should be noted
alongside published results so readers can compare consistently.

### R — Functional unit

The SCI specification leaves R to the practitioner — any well-defined
unit of useful work is valid. Examples in the spec include per API
call, per minute, per user, per device, per ML training job.

This tool reports three R values from each run:

1. **R = 1 request** (the headline metric) — one full pipeline run,
   regardless of how many internal LLM calls that decomposed into.
   This is the unit a user is thinking about: emissions per
   user-facing question.
2. **R = 1 LLM call** — useful for finding which phase of a pipeline
   has the highest per-call footprint.
3. **R = 1 token** (input + output) — the per-token formulation used
   in much of the published LLM-SCI literature, useful for
   infrastructure-level comparisons.

The headline report uses **R = 1 request** because the unit of work
stays consistent when prompts, models, or regions change, which makes
it the most generally interpretable of the three for cross-run
comparisons.

## 3. What the tool records per call

For a three-phase pipeline (Planner → Collector → Writer), each phase
produces a `CallMeasurement` with:

| Field                | Source                                                            |
| -------------------- | ----------------------------------------------------------------- |
| `input_tokens`       | Provider usage metadata                                           |
| `output_tokens`      | Provider usage metadata                                           |
| `energy_kwh`         | EcoLogits if available, otherwise model-card estimate             |
| `carbon_intensity`   | Region table                                                      |
| `embodied_kg`        | Provider-reported, or 12% heuristic                               |
| `cost_usd`           | Per-model pricing table × token counts                            |
| `operational_kg`     | Computed: `energy_kwh × carbon_intensity`                         |
| `total_emissions_kg` | Computed: `operational_kg + embodied_kg`                          |
| `wall_time_s`        | Wall-clock duration (informational; not used in SCI)              |

Aggregation across phases sums each component once across all calls
in the pipeline.

## 4. The baseline-vs-optimized comparison

The `compare` command runs the same query through two prompt sets —
one verbose (representative of a first-draft prompt), one optimized
(compressed structure, explicit conciseness instructions). The
optimized set differs from the baseline in four ways:

1. **Filler instructions are removed.** Phrases like *"make every
   item actionable, provide concrete examples wherever possible"* are
   either cut or replaced with a one-line directive.
2. **Example blocks are compressed.** Worked examples can occupy half
   the prompt; the optimized version keeps the most representative
   example and drops the rest.
3. **Output format is specified as bullets.** *"Output: bullets only,
   no preamble"* tends to reduce output tokens by 20–40% for
   technical reports without loss of detail.
4. **Structural scaffolding becomes section titles.** Long
   descriptions of what each section should contain are replaced with
   the section heading itself.

Typical observed results on real recordings:

* **Input tokens**: -40% to -60%.
* **Output tokens**: -30% to -50%.
* **Energy & emissions**: scale roughly with weighted token totals,
  using the input/output asymmetry.
* **Cost**: tracks emissions closely because both depend mostly on
  output tokens.

## 5. Scope and assumptions

* **Energy values come from one of two paths.** EcoLogits-measured
  values use the provider SDK's instrumented response. When EcoLogits
  isn't available, the fallback is a per-model kWh-per-token
  estimate. Estimated values have an indicative confidence interval
  of roughly ±50% on absolute energy; relative comparisons (baseline
  vs optimized in the same run) are tighter because both sides use
  the same multipliers.
* **Carbon intensity is location-based and time-averaged.** The
  region table uses annual averages. Grid intensity varies through
  the day, so deployments that want carbon-aware scheduling can pass
  a real-time intensity into `sci_score()` instead of using the
  default lookup.
* **Embodied emissions are estimated when the provider doesn't
  report them directly.** The 12% heuristic sits in the published
  range (8–15%) and is the assumption that has the most influence on
  the final number when operational energy is itself measured.
* **The measurement boundary is the inference call.** Data transfer
  between the client and the provider (roughly 0.06 kWh/GB) and
  client-device energy are out of scope for this tool; teams looking
  at an end-to-end footprint can add these as separate terms.
* **Caching is not modelled.** Prompt caching — whether applied
  implicitly by the provider, explicitly through provider APIs, or
  via a third-party caching layer — would reduce the per-request
  footprint of repeated work. This tool reports each call at full
  energy and cost unless the provider's response indicates otherwise,
  so the numbers represent an uncached upper bound.

These are areas where contributions are welcome — the SCI calculation
itself lives in a single file (`src/sci_for_ai/sci.py`) that's
intended to be straightforward to read, adapt, and improve. If you're
working on any of these aspects in your own context, sharing findings
back through the GSF community helps the specification and its
reference implementations mature for everyone.

## 6. References

* Green Software Foundation. *SCI for AI Specification.*
  https://sci-for-ai.greensoftware.foundation/
* Green Software Foundation. *Software Carbon Intensity (SCI)
  Specification.* https://sci.greensoftware.foundation/
* International Organization for Standardization. *ISO/IEC 21031:2024 —
  Information technology — Software carbon intensity.*
* EcoLogits documentation. https://ecologits.ai/

[ecologits]: https://ecologits.ai/
