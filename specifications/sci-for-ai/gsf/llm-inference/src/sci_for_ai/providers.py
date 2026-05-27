"""
Provider-agnostic LLM interface.

Design notes (these are the "green" choices, not arbitrary style):

  * Adapters import their SDK lazily, inside `__init__`. If you only ever
    use Anthropic, you never pay the import cost of Google or OpenAI —
    a measurable energy saving on cold starts.

  * The interface is a `Protocol`, not an ABC. Structural typing means
    no metaclass machinery and zero inheritance overhead.

  * Every call returns a `GenerationResult` containing both the text and
    the measurements. Token counts come from the provider's response
    metadata where available — never re-tokenize locally just to measure,
    since that doubles the compute for the same number.

  * **EcoLogits is integrated for all three real providers** (anthropic,
    google-genai, openai). When the `ecologits` package is installed and
    initialised, every call returns measured energy and embodied figures
    rather than our model-card estimates. The provider class records
    whether a given call used measured or estimated values, so the
    source of each number is transparent in the reports.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .energy import estimate_kwh
from .sci import (CallMeasurement, carbon_intensity_for,
                  estimate_embodied_kg)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# EcoLogits — optional but strongly recommended
# ----------------------------------------------------------------------
# We track which providers have been registered with EcoLogits so we don't
# re-init on every provider construction (EcoLogits.init patches SDK methods;
# repeated calls are redundant and can be re-entrant).
_ECOLOGITS_INITIALISED: set[str] = set()


def _try_init_ecologits(provider_name: str) -> bool:
    """
    Initialise EcoLogits for `provider_name` if available. Returns True if
    measured energy will now be attached to responses, False if EcoLogits
    isn't installed (we'll fall back to model-card estimates).

    Idempotent: safe to call multiple times.
    """
    if provider_name in _ECOLOGITS_INITIALISED:
        return True
    try:
        from ecologits import EcoLogits  # type: ignore
    except ImportError:
        logger.info(
            "ecologits not installed; %s calls will use model-card energy "
            "estimates rather than measured values. "
            "Install `pip install ecologits` for measured energy.",
            provider_name,
        )
        return False

    try:
        # EcoLogits 0.5+ uses provider= (singular) or providers= depending
        # on version. We try the modern signature first.
        try:
            EcoLogits.init(providers=[provider_name])
        except TypeError:
            EcoLogits.init(provider=[provider_name])
        _ECOLOGITS_INITIALISED.add(provider_name)
        logger.info("EcoLogits initialised for %s — energy will be measured.",
                    provider_name)
        return True
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("EcoLogits init failed for %s: %s. "
                       "Falling back to model-card estimates.", provider_name, e)
        return False


# ----------------------------------------------------------------------
# Result type
# ----------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class GenerationResult:
    text: str
    measurement: CallMeasurement
    energy_source: str = "estimated"   # "measured" (EcoLogits) or "estimated" (model-card)
    raw_response: Any = None  # provider-specific, opt-in for debugging


# ----------------------------------------------------------------------
# Protocol every provider satisfies
# ----------------------------------------------------------------------
@runtime_checkable
class LLMProvider(Protocol):
    """Minimal interface. Add capabilities (streaming, tools) via subclasses."""

    model_id: str
    region: str

    def generate(self, prompt: str, *, phase: str = "generate",
                 max_output_tokens: int = 1024) -> GenerationResult: ...

    def count_tokens(self, text: str) -> int: ...


# ----------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------
def _build_measurement(*, phase: str, input_tokens: int, output_tokens: int,
                       energy_kwh: float, region: str, wall_time_s: float,
                       model_id: str = "unknown",
                       embodied_kg: float | None = None,
                       cost_usd: float | None = None) -> CallMeasurement:
    """
    Assemble a CallMeasurement, filling in embodied and cost if not provided.

    Cost is looked up from the pricing table for `model_id` when not given.
    Pass `cost_usd=0.0` to suppress lookup (used by MockProvider and
    RecordedProvider which already have or don't want a cost figure).
    """
    from .pricing import estimate_cost_usd

    ci = carbon_intensity_for(region)
    if embodied_kg is None:
        embodied_kg = estimate_embodied_kg(energy_kwh * ci)
    if cost_usd is None:
        cost_usd, _src = estimate_cost_usd(model_id, input_tokens, output_tokens)
    return CallMeasurement(
        phase=phase,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        energy_kwh=energy_kwh,
        carbon_intensity=ci,
        embodied_kg=embodied_kg,
        wall_time_s=wall_time_s,
        region=region,
        cost_usd=cost_usd,
    )


# ----------------------------------------------------------------------
# Anthropic adapter (lazy import)
# ----------------------------------------------------------------------
class AnthropicProvider:
    """
    Anthropic Claude provider. Imports the SDK lazily.

    Requires: pip install anthropic, env var ANTHROPIC_API_KEY.
    Optional but recommended: pip install ecologits — for measured (not
    estimated) energy. Energy source is logged and exposed on each result.
    """

    _ecologits_provider_name = "anthropic"

    def __init__(self, model_id: str = "claude-haiku-4-5",
                 region: str = "us-central1",
                 api_key: str | None = None,
                 use_ecologits: bool = True) -> None:
        try:
            import anthropic  # local import; only loaded when this class is used
        except ImportError as e:
            raise ImportError(
                "AnthropicProvider requires the 'anthropic' package. "
                "Install it with: pip install anthropic"
            ) from e

        self.model_id = model_id
        self.region = region
        # Initialise EcoLogits *before* creating the client, because EcoLogits
        # patches SDK methods at init time; a client created earlier won't get
        # the instrumentation in some SDK versions.
        self._has_ecologits = (
            _try_init_ecologits(self._ecologits_provider_name)
            if use_ecologits else False
        )
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

    def generate(self, prompt: str, *, phase: str = "generate",
                 max_output_tokens: int = 1024) -> GenerationResult:
        start = time.monotonic()
        response = self._client.messages.create(
            model=self.model_id,
            max_tokens=max_output_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        wall = time.monotonic() - start

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        text = "".join(b.text for b in response.content if b.type == "text")

        # Prefer measured energy from EcoLogits if available.
        measured_energy, _gwp, measured_embodied = _read_ecologits_impacts(response)
        if measured_energy is not None:
            energy_kwh = measured_energy
            embodied_kg = measured_embodied  # may be None → helper will estimate
            energy_source = "measured"
        else:
            energy_kwh, _src = estimate_kwh(self.model_id, input_tokens, output_tokens)
            embodied_kg = None  # → helper will use 12% heuristic
            energy_source = "estimated"

        measurement = _build_measurement(
            phase=phase, input_tokens=input_tokens, output_tokens=output_tokens,
            energy_kwh=energy_kwh, region=self.region, wall_time_s=wall,
            model_id=self.model_id, embodied_kg=embodied_kg,
        )
        return GenerationResult(
            text=text, measurement=measurement,
            energy_source=energy_source, raw_response=response,
        )

    def count_tokens(self, text: str) -> int:
        # Anthropic exposes count_tokens; this is a single API call.
        return self._client.messages.count_tokens(
            model=self.model_id,
            messages=[{"role": "user", "content": text}],
        ).input_tokens


# ----------------------------------------------------------------------
# Google Gemini adapter (lazy import) — matches the original reference's provider
# ----------------------------------------------------------------------
class GeminiProvider:
    """
    Google Gemini provider. Imports the SDK lazily.

    Requires: pip install google-genai, env var GEMINI_API_KEY.
    Optional but recommended: pip install ecologits — for measured (not
    estimated) energy.
    """

    _ecologits_provider_name = "google_genai"

    def __init__(self, model_id: str = "gemini-2.0-flash",
                 region: str = "us-central1",
                 api_key: str | None = None,
                 use_ecologits: bool = True) -> None:
        try:
            from google import genai
        except ImportError as e:
            raise ImportError(
                "GeminiProvider requires the 'google-genai' package. "
                "Install it with: pip install google-genai"
            ) from e

        self.model_id = model_id
        self.region = region
        self._has_ecologits = (
            _try_init_ecologits(self._ecologits_provider_name)
            if use_ecologits else False
        )
        self._client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))

    def generate(self, prompt: str, *, phase: str = "generate",
                 max_output_tokens: int = 1024) -> GenerationResult:
        from google.genai.types import GenerateContentConfig

        start = time.monotonic()
        response = self._client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                response_modalities=["TEXT"],
            ),
        )
        wall = time.monotonic() - start

        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count or 0
        output_tokens = usage.candidates_token_count or 0
        text = "\n".join(
            p.text for p in response.candidates[0].content.parts if hasattr(p, "text")
        ) if response.candidates else ""

        measured_energy, _gwp, measured_embodied = _read_ecologits_impacts(response)
        if measured_energy is not None:
            energy_kwh = measured_energy
            embodied_kg = measured_embodied
            energy_source = "measured"
        else:
            energy_kwh, _src = estimate_kwh(self.model_id, input_tokens, output_tokens)
            embodied_kg = None
            energy_source = "estimated"

        measurement = _build_measurement(
            phase=phase, input_tokens=input_tokens, output_tokens=output_tokens,
            energy_kwh=energy_kwh, region=self.region, wall_time_s=wall,
            model_id=self.model_id, embodied_kg=embodied_kg,
        )
        return GenerationResult(
            text=text, measurement=measurement,
            energy_source=energy_source, raw_response=response,
        )

    def count_tokens(self, text: str) -> int:
        return self._client.models.count_tokens(
            model=self.model_id, contents=text
        ).total_tokens


def _read_ecologits_impacts(response: Any) -> tuple[float | None, float | None, float | None]:
    """
    Read (energy_kwh, gwp_kg, embodied_kg) from a response that has
    EcoLogits `.impacts` attached. Returns (None, None, None) when the
    response has no impacts (EcoLogits not installed or not initialised
    for this provider).

    EcoLogits returns RangeValue objects (`.min`/`.max`); we take the midpoint
    for a single representative number. The original ranges are still on
    the raw response if a caller wants them.

      * `energy_kwh` — measured/modelled energy for this call.
      * `gwp_kg`    — EcoLogits' end-to-end CO2eq estimate (covers operational
                      + embodied with its own internal carbon-intensity model).
                      We expose this so callers can prefer it over E * I + M.
      * `embodied_kg` — embodied component only, when EcoLogits exposes it.
    """
    impacts = getattr(response, "impacts", None)
    if impacts is None:
        return None, None, None

    def _midpoint(raw: Any) -> float | None:
        if raw is None:
            return None
        if hasattr(raw, "min") and hasattr(raw, "max"):
            return (raw.min + raw.max) / 2
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    energy = gwp = embodied = None
    try:
        energy = _midpoint(impacts.energy.value)
    except AttributeError:
        pass
    try:
        gwp = _midpoint(impacts.gwp.value)
    except AttributeError:
        pass
    try:
        embodied = _midpoint(impacts.embodied.gwp.value)
    except AttributeError:
        pass
    return energy, gwp, embodied


# ----------------------------------------------------------------------
# OpenAI adapter (lazy import)
# ----------------------------------------------------------------------
class OpenAIProvider:
    """
    OpenAI provider. Imports the SDK lazily.

    Requires: pip install openai, env var OPENAI_API_KEY.
    Optional but recommended: pip install ecologits — for measured (not
    estimated) energy.
    """

    _ecologits_provider_name = "openai"

    def __init__(self, model_id: str = "gpt-4o-mini",
                 region: str = "us-central1",
                 api_key: str | None = None,
                 use_ecologits: bool = True) -> None:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "OpenAIProvider requires the 'openai' package. "
                "Install it with: pip install openai"
            ) from e

        self.model_id = model_id
        self.region = region
        self._has_ecologits = (
            _try_init_ecologits(self._ecologits_provider_name)
            if use_ecologits else False
        )
        self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def generate(self, prompt: str, *, phase: str = "generate",
                 max_output_tokens: int = 1024) -> GenerationResult:
        start = time.monotonic()
        # OpenAI deprecated `max_tokens` in favour of `max_completion_tokens`
        # in late 2024. The gpt-5.x family (and o-series reasoning models)
        # reject `max_tokens` outright with a 400 error. The new parameter
        # is also accepted by gpt-4.x for backward compatibility, so it's
        # the safe universal choice.
        try:
            response = self._client.chat.completions.create(
                model=self.model_id,
                max_completion_tokens=max_output_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except TypeError:
            # Very old openai SDK (<1.40) doesn't know about
            # max_completion_tokens; fall back to max_tokens. The user
            # will get a clearer error if their model rejects both.
            response = self._client.chat.completions.create(
                model=self.model_id,
                max_tokens=max_output_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        wall = time.monotonic() - start

        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        text = response.choices[0].message.content or ""

        measured_energy, _gwp, measured_embodied = _read_ecologits_impacts(response)
        if measured_energy is not None:
            energy_kwh = measured_energy
            embodied_kg = measured_embodied
            energy_source = "measured"
        else:
            energy_kwh, _src = estimate_kwh(self.model_id, input_tokens, output_tokens)
            embodied_kg = None
            energy_source = "estimated"

        measurement = _build_measurement(
            phase=phase, input_tokens=input_tokens, output_tokens=output_tokens,
            energy_kwh=energy_kwh, region=self.region, wall_time_s=wall,
            model_id=self.model_id, embodied_kg=embodied_kg,
        )
        return GenerationResult(
            text=text, measurement=measurement,
            energy_source=energy_source, raw_response=response,
        )

    def count_tokens(self, text: str) -> int:
        # OpenAI has no count_tokens API; approximate via tiktoken if available.
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model(self.model_id)
            return len(enc.encode(text))
        except (ImportError, KeyError):
            # 4 chars per token is the common rough estimate. Acceptable for
            # the comparison view, which only needs relative deltas.
            return max(1, len(text) // 4)


# ----------------------------------------------------------------------
# Mock provider — deterministic, zero network, useful for tests and demos
# ----------------------------------------------------------------------
class MockProvider:
    """
    Mock provider for tests and offline demos.

    Returns a deterministic response whose **length is shaped by the prompt**:

      * No conciseness hints → output scales with input (detail in begets
        detail out — typical LLM behaviour for open-ended prompts).
      * Conciseness hints present ("be concise", "bullets only", "no
        preamble", "avoid verbose") → output is **capped near a small
        absolute size**, not a fraction of input. This is what real
        models do: "be concise" caps the response length irrespective of
        prompt length.

    Why the cap is absolute, not proportional: a 500-token prompt and a
    2,000-token prompt with the same "be concise" instruction both elicit
    roughly the same short response. The instruction is about the
    *output*, not a ratio. Modelling it as a ratio (what we did initially)
    hid the SCI effect of conciseness because input and output shrank
    in lockstep, leaving per-token energy intensity flat.

    Modelling it as a cap shifts the input/output ratio toward input
    on optimized runs. Since output tokens carry a higher per-token
    energy weight than input tokens, fewer output tokens per input
    token lowers the per-token energy intensity — so SCI/token drops,
    which matches the behaviour a prompt-optimization tool aims to
    demonstrate.

    Energy is still estimated via the model-card profile (the same
    path used for real providers without EcoLogits) so the math is
    exercised end-to-end. No network, no SDK — runs anywhere.
    """

    # Hints that, in real LLM behaviour, cap output length near-absolutely.
    _CONCISENESS_HINTS = (
        "be concise", "bullets only", "no preamble", "avoid verbose",
        "no filler", "be brief", "concise", "bullet form",
    )

    # Base output ratio when no conciseness hints are present. Output is
    # ~1.5x input — typical for verbose, example-rich technical prompts.
    _BASE_OUTPUT_RATIO = 1.5

    # When conciseness hints are present, output is capped near this size
    # regardless of input. Real-world "be concise" responses for a
    # technical-report task typically land in this range.
    _TERSE_OUTPUT_CAP = 250  # tokens

    # Each additional conciseness hint pulls the cap a bit lower.
    _CAP_REDUCTION_PER_HINT = 30  # tokens
    _MIN_TERSE_OUTPUT = 100  # never go below this

    def __init__(self, model_id: str = "claude-haiku-4-5",
                 region: str = "us-central1") -> None:
        self.model_id = model_id
        self.region = region

    def _output_size_for(self, prompt: str, input_tokens: int,
                         max_output_tokens: int) -> int:
        """Estimate how many output tokens this prompt would elicit."""
        prompt_lower = prompt.lower()
        hits = sum(1 for h in self._CONCISENESS_HINTS if h in prompt_lower)

        if hits > 0:
            # Conciseness hints cap output near-absolutely.
            cap = self._TERSE_OUTPUT_CAP - (hits - 1) * self._CAP_REDUCTION_PER_HINT
            target = max(self._MIN_TERSE_OUTPUT, cap)
        else:
            # No hints: output scales with input.
            target = int(input_tokens * self._BASE_OUTPUT_RATIO)

        return max(20, min(target, max_output_tokens))

    def generate(self, prompt: str, *, phase: str = "generate",
                 max_output_tokens: int = 1024) -> GenerationResult:
        start = time.monotonic()
        input_tokens = self.count_tokens(prompt)
        output_tokens = self._output_size_for(prompt, input_tokens, max_output_tokens)

        # Deterministic stub text of the right length (~4 chars/token).
        # Length matters more than content for measurement purposes.
        response_text = (
            f"[mock-{phase}] " +
            ("response chunk " * (output_tokens // 4)).strip()
        )
        wall = time.monotonic() - start

        energy_kwh, _src = estimate_kwh(self.model_id, input_tokens, output_tokens)
        measurement = _build_measurement(
            phase=phase, input_tokens=input_tokens, output_tokens=output_tokens,
            energy_kwh=energy_kwh, region=self.region, wall_time_s=wall,
            model_id=self.model_id,
        )
        return GenerationResult(text=response_text, measurement=measurement)

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


# ----------------------------------------------------------------------
# Recorded provider — replays a real run's measurements from JSON
# ----------------------------------------------------------------------
class RecordedProvider:
    """
    Replays a real recorded run from a JSON fixture. No network, no SDK.

    Use this to:
      * Distribute a publicly-shareable demo grounded in real EcoLogits
        measurements (you record once, everyone replays).
      * Run reproducible benchmarks without consuming API credits on
        every replay.
      * Test the pipeline end-to-end against realistic numbers in CI.

    To record a fixture, run any real provider with `--record-to FILE.json`.
    To replay it, use `--provider recorded --fixture FILE.json`.

    The fixture format is a list of per-call entries in the order the
    pipeline made them. Each entry contains the prompt text (or its first
    80 chars as a marker), the response text, token counts, energy, and
    embodied emissions. We trust the recorded numbers entirely — the
    point of replay is that the run already happened.

    Calls are matched by order, not by prompt content: pipeline phase 1
    gets fixture entry 1, etc. This keeps the format simple and
    deterministic.
    """

    def __init__(self, fixture_path: str,
                 model_id: str | None = None,
                 region: str | None = None) -> None:
        import json
        from pathlib import Path
        self._fixture_path = str(fixture_path)
        with Path(fixture_path).open() as f:
            data = json.load(f)

        # Fixture root may be a saved ComparisonResult, a PipelineResult,
        # or a raw list of calls. Normalise to a flat list of call dicts
        # in pipeline order (baseline calls first, then optimized).
        if isinstance(data, dict) and "baseline" in data and "optimized" in data:
            # ComparisonResult shape
            calls = []
            for run in (data["baseline"], data["optimized"]):
                run_source = run.get("energy_source", "measured")
                for m in run.get("measurements", []):
                    calls.append({
                        **m,
                        "energy_source": m.get("energy_source", run_source),
                        "_run": run.get("prompt_set", "unknown"),
                    })
            # Also pick up the per-phase texts from the runs
            self._texts = self._extract_texts_from_comparison(data)
            self._meta = {
                "model_id": data["baseline"]["measurements"][0].get("region", "unknown"),
                "fixture_kind": "comparison",
                "original_query": data.get("query"),
            }
        elif isinstance(data, dict) and "measurements" in data:
            run_source = data.get("energy_source", "measured")
            calls = [{**m, "energy_source": m.get("energy_source", run_source)}
                     for m in data["measurements"]]
            self._texts = self._extract_texts_from_pipeline(data)
            self._meta = {"fixture_kind": "pipeline"}
        elif isinstance(data, list):
            calls = data
            self._texts = []
            self._meta = {"fixture_kind": "raw"}
        else:
            raise ValueError(
                f"Unrecognised fixture format in {fixture_path}. "
                f"Expected a recorded ComparisonResult, PipelineResult, or list of calls."
            )

        self._calls = calls
        self._next = 0
        # Honour user override, otherwise infer from fixture
        inferred_model = self._infer_model_id(
            calls, data if isinstance(data, dict) else None
        )
        self.model_id = model_id or inferred_model
        # Flag: did the user override the model post-recording?
        # If so, energy stays as recorded but cost uses the new pricing —
        # an inconsistent mix the report should warn about.
        self._model_overridden = (model_id is not None
                                   and model_id != inferred_model
                                   and inferred_model != "recorded")
        self._recorded_model = inferred_model
        self.region = region or (calls[0].get("region", "unknown") if calls else "unknown")

    @staticmethod
    def _extract_texts_from_comparison(data: dict) -> list[str]:
        texts = []
        for run_key in ("baseline", "optimized"):
            run = data[run_key]
            texts.append(run.get("plan", ""))
            texts.append(run.get("insights", ""))
            texts.append(run.get("report", ""))
        return texts

    @staticmethod
    def _extract_texts_from_pipeline(data: dict) -> list[str]:
        return [data.get("plan", ""), data.get("insights", ""), data.get("report", "")]

    @staticmethod
    def _infer_model_id(calls: list[dict], data: dict | None = None) -> str:
        """
        Look for a model id in this order:
          1. Top-level "model" field of the fixture (preferred — set at record time)
          2. Top-level "model" inside baseline run (for comparison fixtures)
          3. Per-call "model" field (older raw-list fixtures)
          4. "recorded" fallback (cost lookup will use fallback pricing)
        """
        if data is not None:
            if "model" in data:
                return data["model"]
            if "baseline" in data and "model" in data["baseline"]:
                return data["baseline"]["model"]
        for c in calls:
            if "model" in c:
                return c["model"]
        return "recorded"

    def generate(self, prompt: str, *, phase: str = "generate",
                 max_output_tokens: int = 1024) -> GenerationResult:
        if self._next >= len(self._calls):
            raise RuntimeError(
                f"Recorded fixture {self._fixture_path} exhausted after "
                f"{self._next} calls. Re-record with a longer run, or check "
                f"the pipeline is calling the same number of phases."
            )
        call = self._calls[self._next]
        text = self._texts[self._next] if self._next < len(self._texts) else ""
        self._next += 1

        # Use the recorded numbers as-is — this is the whole point.
        # Cost: prefer the recorded value; if the fixture predates cost
        # tracking, recompute from token counts + model_id so old fixtures
        # still show meaningful $ figures.
        recorded_cost = call.get("cost_usd")
        if recorded_cost is None:
            from .pricing import estimate_cost_usd
            recorded_cost, _src = estimate_cost_usd(
                self.model_id,
                int(call["input_tokens"]),
                int(call["output_tokens"]),
            )
        measurement = CallMeasurement(
            phase=call.get("phase", phase),
            input_tokens=int(call["input_tokens"]),
            output_tokens=int(call["output_tokens"]),
            energy_kwh=float(call["energy_kwh"]),
            carbon_intensity=float(call.get("carbon_intensity",
                                            carbon_intensity_for(self.region))),
            embodied_kg=float(call.get("embodied_kg", 0.0)),
            wall_time_s=float(call.get("wall_time_s", 0.0)),
            region=call.get("region", self.region),
            cost_usd=float(recorded_cost),
        )
        return GenerationResult(
            text=text or f"[replayed:{phase}]",
            measurement=measurement,
            energy_source=call.get("energy_source", "measured"),
        )

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


# ----------------------------------------------------------------------
# Provider factory
# ----------------------------------------------------------------------
_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "mock": MockProvider,
    "recorded": RecordedProvider,
}


def build_provider(name: str, **kwargs: Any) -> LLMProvider:
    """
    Factory. `name` is one of: anthropic, gemini, openai, mock, recorded.

    Extra kwargs are forwarded to the provider's constructor. For the
    `recorded` provider, pass `fixture_path="path/to/fixture.json"`.
    """
    name = name.lower()
    if name not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider {name!r}. Choose from: {', '.join(_PROVIDERS)}"
        )
    return _PROVIDERS[name](**kwargs)
