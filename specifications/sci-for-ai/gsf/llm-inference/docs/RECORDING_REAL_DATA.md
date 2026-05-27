# Recording a real run with EcoLogits

This guide walks through producing the fixtures committed in
`docs/fixtures/` — real comparison runs against an LLM provider with
energy figures measured by [EcoLogits](https://ecologits.ai/), saved
as JSON files that anyone can replay without an API key.

The same workflow applies to OpenAI, Anthropic, and Google Gemini. The
examples below use OpenAI; substitute `anthropic` or `gemini` for the
`--provider` value and the matching model id to record against another
provider.

## Prerequisites

* Python 3.10 or later
* An API key for the provider you choose
* A small amount of API credit. Costs scale with model size — see the
  per-model table below.

## Step 1 — Install with the provider extras

```bash
git clone <repo-url> sci-for-ai
cd sci-for-ai
pip install -e ".[openai]"           # or .[anthropic], .[gemini], or .[all]
```

This installs the provider's official Python SDK and `ecologits`, the
instrumentation that provides measured per-call energy figures.

Confirm the imports succeed:

```bash
python -c "from ecologits import EcoLogits; from openai import OpenAI; print('ok')"
```

## Step 2 — Set your API key

```bash
export OPENAI_API_KEY="sk-..."     # or ANTHROPIC_API_KEY / GEMINI_API_KEY
```

(Or copy `.env.example` to `.env` and put it there.)

## Step 3 — Pick a model

EcoLogits 0.10+ has energy profiles for a wide range of OpenAI,
Anthropic, and Google Gemini models. Some illustrative picks for the
demo:

| Model           | Pricing (input/output)  | Notes                                              | EcoLogits energy |
| --------------- | ----------------------- | -------------------------------------------------- | ---------------- |
| `gpt-4o-mini`   | $0.15 / $0.60 per M     | Lowest-cost demo: ~$0.05 for a full comparison run | ✓ measured       |
| `gpt-5.4-nano`  | $0.20 / $1.25 per M     | Current budget tier                                | ✓ measured       |
| `gpt-4.1-mini`  | $0.40 / $1.60 per M     | Mid-tier with measured profile                     | ✓ measured       |
| `gpt-5.4-mini`  | $0.75 / $4.50 per M     | Current best price/performance                     | ✓ measured       |
| `gpt-4o`        | $2.50 / $10 per M       | Prior flagship; ~$0.30 demo cost                   | ✓ measured       |
| `gpt-4.1`       | $2.00 / $8 per M        | Long-context flagship                              | ✓ measured       |
| `gpt-5.4`       | $2.50 / $15 per M       | Current flagship with measured energy              | ✓ measured       |
| `gpt-5.5`       | $5.00 / $30 per M       | Newest (April 2026); ~$1 demo cost                 | falls back to estimate |

> **Note on `gpt-5.5`**: It is the most recent flagship, but EcoLogits
> 0.10.1 does not yet include a profile for it. The tool falls back to
> the calibrated model-card estimate and labels the run as `estimated`
> rather than `measured`. When the energy figure needs to come from
> direct instrumentation, prefer `gpt-5.4` until EcoLogits adds
> `gpt-5.5`.

The audio, realtime, image, and embedding variants don't match the
chat-completion pipeline this tool runs, so use the standard
chat-completion model ids.

To check whether a specific model has an EcoLogits profile:

```bash
python -c "
from ecologits.model_repository import models
match = [m for m in models.list_models()
         if 'openai' in str(m.provider).lower() and 'gpt-5.4' in m.name]
for m in match[:5]:
    print(m.name)
"
```

At least one match means a measured profile is available.

## Step 4 — Record a comparison run

```bash
sci-for-ai compare \
    --provider openai \
    --model gpt-4o-mini \
    --region us-central1 \
    --query "How do I reduce energy use in a Python image processing pipeline?" \
    --record-to docs/fixtures/openai-gpt-4o-mini.json
```

What each flag does:

* `--provider openai` — use the OpenAI adapter (triggers
  `EcoLogits.init(providers=["openai"])` internally).
* `--model gpt-4o-mini` — pick the model; EcoLogits applies the
  matching energy profile.
* `--region us-central1` — the deployment region used to look up
  carbon intensity (the `I` term in SCI).
* `--query "..."` — the question fed to the Planner → Collector →
  Writer pipeline.
* `--record-to FILE.json` — save the complete result as a replayable
  fixture.

The CLI makes six API calls in total (three for baseline, three for
optimized) and prints a comparison report. Look for **"Energy source:
measured"** in the report header to confirm EcoLogits is providing the
numbers.

## Step 5 — Verify the recording

After the run finishes, two things should be true:

1. The terminal output shows `Energy source: measured (baseline) /
   measured (optimized) — measured via EcoLogits`. If it says
   `estimated`, EcoLogits isn't initialised — check `pip show ecologits`.
2. The fixture file exists and contains real numbers:

```bash
python -c "
import json
d = json.load(open('docs/fixtures/openai-gpt-4o-mini.json'))
print('Baseline SCI per request:', d['baseline']['totals']['sci_per_request'])
print('Optimized SCI per request:', d['optimized']['totals']['sci_per_request'])
print('Energy source:', d['baseline']['energy_source'])
print('Model:', d.get('model'))
"
```

## Step 6 — Replay the recording (no API key needed)

```bash
sci-for-ai compare \
    --provider recorded \
    --fixture docs/fixtures/openai-gpt-4o-mini.json \
    --query "How do I reduce energy use in a Python image processing pipeline?"
```

This prints the same report as Step 4, without making any API calls.
The fixture is self-contained: anyone with the repo can reproduce the
run.

## Step 7 — Share the fixture

The fixture file is a single JSON document. Commit it to
`docs/fixtures/` in the repo, reference it from `README.md` as a
canonical example, and any reader can verify the numbers by running
Step 6 themselves.

## Troubleshooting

### `Energy source: estimated` instead of `measured`

EcoLogits isn't being picked up. Common causes:

* `ecologits` is not installed in the active Python environment.
  `pip show ecologits` should show version 0.10 or newer.
* You're running inside a virtualenv or Conda environment that doesn't
  have it. `which sci-for-ai` to confirm the path.
* The model id isn't in the EcoLogits repository (for example, a
  fine-tuned model). EcoLogits silently falls back; the verbose log
  shows the source:
  ```bash
  sci-for-ai compare --provider openai --model gpt-4o-mini --query "..." -v
  ```

### `.impacts` returns `None` or is missing

EcoLogits attaches `.impacts` to the response, but for some models the
energy values can come back as `None` or the field is missing
entirely. The tool falls back to the model-card estimate in that case
and labels the source as `estimated` — the report still includes a
real number, just from the estimate path rather than the measured
path.

### Empty responses or rate-limit errors

The pipeline aborts cleanly with a `PipelineError`. If responses are
being truncated, increase `--max-output-tokens` (default 1024 is
usually enough; reasoning models may need 4096 or more). For rate
limits, retry once the limit window passes — the tool does not
auto-retry, so that partial runs don't accidentally double the API
spend.

### Cost is higher than expected

The baseline prompts are deliberately verbose — that's the comparison
the demo is showing. Typical spend for one full `compare` run on
`gpt-4o-mini`:

* Baseline: ~5,000 tokens in, ~2,500 tokens out
* Optimized: ~1,500 tokens in, ~750 tokens out
* Total: about $0.04–$0.06 at current pricing

Larger models scale proportionally.

## What EcoLogits is doing internally

When `EcoLogits.init(providers=["openai"])` runs, it instruments the
OpenAI SDK's chat completion method. For every response it:

1. Reads `response.usage` to get input and output token counts.
2. Looks up the model's profile in its internal repository (parameter
   count, architecture estimate, hardware assumptions).
3. Computes per-call energy in kWh from those tokens and that profile.
4. Attaches `response.impacts.energy.value` (a RangeValue with `.min`
   and `.max`) and `response.impacts.gwp.value` (total CO₂eq).

The `_read_ecologits_impacts()` function in `providers.py` reads those
fields and uses the midpoint. The SCI formula `(E × I + M) / R` then
applies the regional carbon intensity `I` from the `--region` flag.

EcoLogits's own documentation notes that for providers which don't
publish their model architecture or serving infrastructure, the
returned energy figures are *estimates derived from a published
methodology*, not direct hardware measurements. See
[`docs/SCI_METHODOLOGY.md`](SCI_METHODOLOGY.md) for the methodology
discussion.
