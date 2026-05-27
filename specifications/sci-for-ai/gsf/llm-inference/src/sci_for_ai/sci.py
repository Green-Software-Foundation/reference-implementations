"""
SCI for AI — Software Carbon Intensity calculation for LLM inference.

This module is pure: no I/O, no network, no globals beyond constants.
Every function is deterministic and unit-testable. This is intentional —
the SCI math is the part you most need to trust, so it lives alone.

Reference: ISO 21031 / Green Software Foundation SCI specification.
    SCI = (E * I + M) / R

Where:
    E = Energy consumed by the software (kWh)
    I = Location-based carbon intensity (kgCO2eq / kWh)
    M = Embodied emissions amortised over the functional unit (kgCO2eq)
    R = Functional unit (here: tokens processed)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


# ----------------------------------------------------------------------
# Carbon intensity defaults
# ----------------------------------------------------------------------
# Values in kgCO2eq / kWh. These are published averages — override per
# deployment region for accurate reporting. Sources noted in README.
DEFAULT_CARBON_INTENSITY: dict[str, float] = {
    "world-average": 0.475,        # IEA global average, used when region is unknown
    "us-central1": 0.413,          # Google Cloud Iowa
    "us-west1": 0.078,             # Google Cloud Oregon (hydro-dominant grid)
    "europe-west1": 0.167,         # Belgium
    "europe-north1": 0.058,        # Finland (nuclear and hydro grid)
    "asia-south1": 0.708,          # Mumbai (predominantly thermal generation)
    "asia-southeast1": 0.408,      # Singapore
}

# Default embodied-emissions factor as a fraction of operational emissions.
# Cloud-inference embodied share is typically 8-15%; 0.12 is the midpoint
# of that published range and is used when the provider does not return
# an embodied figure directly. Prefer provider-reported embodied values
# when they are available.
DEFAULT_EMBODIED_FRACTION: float = 0.12


# ----------------------------------------------------------------------
# Data classes
# ----------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class CallMeasurement:
    """One LLM call's measured impact. Immutable so it can be safely shared."""
    phase: str
    input_tokens: int
    output_tokens: int
    energy_kwh: float
    carbon_intensity: float       # kgCO2eq / kWh, region-specific
    embodied_kg: float            # kgCO2eq, already amortised to this call
    wall_time_s: float = 0.0
    region: str = "unknown"
    cost_usd: float = 0.0         # API cost for this call; 0 if unpriced

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def operational_kg(self) -> float:
        return self.energy_kwh * self.carbon_intensity

    @property
    def total_emissions_kg(self) -> float:
        return self.operational_kg + self.embodied_kg

    @property
    def sci(self) -> float | None:
        """SCI per token. None when no tokens were processed."""
        return self.total_emissions_kg / self.total_tokens if self.total_tokens > 0 else None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["total_tokens"] = self.total_tokens
        d["operational_kg"] = self.operational_kg
        d["total_emissions_kg"] = self.total_emissions_kg
        d["sci"] = self.sci
        return d


# ----------------------------------------------------------------------
# Pure calculation functions
# ----------------------------------------------------------------------
def carbon_intensity_for(region: str) -> float:
    """Look up grid carbon intensity for a region; fall back to world average."""
    return DEFAULT_CARBON_INTENSITY.get(region, DEFAULT_CARBON_INTENSITY["world-average"])


def estimate_embodied_kg(operational_kg: float, fraction: float = DEFAULT_EMBODIED_FRACTION) -> float:
    """
    Estimate embodied emissions as a fraction of operational.
    Use only when the provider does not report embodied data directly.
    """
    if operational_kg < 0:
        raise ValueError("operational_kg must be non-negative")
    if not 0 <= fraction <= 1:
        raise ValueError("fraction must be between 0 and 1")
    return operational_kg * fraction


def sci_score(energy_kwh: float, tokens: int, carbon_intensity: float,
              embodied_kg: float = 0.0) -> float | None:
    """
    Compute SCI = (E * I + M) / R.

    Returns None when tokens is 0 (the per-token ratio is undefined in that case;
    returning 0 would suggest a real value where none exists).
    """
    if energy_kwh < 0 or embodied_kg < 0 or carbon_intensity < 0:
        raise ValueError("inputs must be non-negative")
    if tokens <= 0:
        return None
    return (energy_kwh * carbon_intensity + embodied_kg) / tokens


def aggregate(measurements: list[CallMeasurement]) -> dict[str, Any]:
    """
    Aggregate a list of per-call measurements into totals and SCI metrics.

    SCI is computed at two granularities, with different functional units (R):

      * `sci_per_request` — emissions per full pipeline run (R = 1 request).
        This is the right metric for prompt-optimization comparisons because R
        stays constant: the user asks one question, gets one answer, regardless
        of how that internally decomposes into LLM calls. Lower is always better.

      * `sci_per_call` — emissions per individual LLM API call (R = 1 call).
        Useful for sub-pipeline analysis (identifying which phase has
        the highest per-call footprint), though it treats every call
        as equivalent regardless of the work each does.

      * `sci_per_token` — emissions per total token (R = input+output tokens).
        The "per token" formulation matches the original spec's usage
        examples. Note: when comparing two runs in which the
        optimization itself changes the token count, R is no longer
        constant across the comparison, so the per-token ratio is
        most informative for infrastructure comparisons (region,
        model, hardware) where the token workload is held fixed.

    The choice of R is the practitioner's per the GSF SCI specification.
    For LLM pipelines, R = 1 request is a natural choice for end-to-end
    optimization decisions because it remains constant across changes
    in prompts, models, and regions.

    Done in a single pass — no repeated iteration over the same list.
    """
    total_energy = 0.0
    total_input = 0
    total_output = 0
    total_operational = 0.0
    total_embodied = 0.0
    total_wall = 0.0
    total_cost = 0.0

    for m in measurements:
        total_energy += m.energy_kwh
        total_input += m.input_tokens
        total_output += m.output_tokens
        total_operational += m.operational_kg
        total_embodied += m.embodied_kg
        total_wall += m.wall_time_s
        total_cost += m.cost_usd

    total_tokens = total_input + total_output
    total_emissions = total_operational + total_embodied
    n_calls = len(measurements)

    # Per request: the whole list of measurements is treated as one user-facing
    # request. If the caller passes in measurements from multiple requests, they
    # should aggregate them separately first.
    sci_per_request = total_emissions if n_calls > 0 else None

    # Per call: amortise across the individual LLM calls.
    sci_per_call = (total_emissions / n_calls) if n_calls > 0 else None

    # Per token (legacy / spec-style, for infrastructure comparisons).
    sci_per_token = (total_emissions / total_tokens) if total_tokens > 0 else None

    return {
        "energy_kwh": total_energy,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_tokens,
        "operational_kg": total_operational,
        "embodied_kg": total_embodied,
        "total_emissions_kg": total_emissions,
        "wall_time_s": total_wall,
        "cost_usd": total_cost,
        # Primary metric: emissions per user-facing request (one full pipeline run).
        "sci_per_request": sci_per_request,
        # Secondary: per individual LLM API call.
        "sci_per_call": sci_per_call,
        # Legacy/infrastructure: per total token. NOT for prompt optimization.
        "sci_per_token": sci_per_token,
        # Backward-compatible alias for the old "sci" key — equal to sci_per_token.
        # Kept for fixtures and downstream code that referenced the old name.
        "sci": sci_per_token,
        "embodied_pct": (total_embodied / total_emissions * 100) if total_emissions > 0 else 0.0,
        "n_calls": n_calls,
    }


def compare(baseline: dict[str, Any], optimized: dict[str, Any]) -> dict[str, Any]:
    """
    Compare a baseline aggregate against an optimized one.
    Returns absolute and percentage deltas for the metrics that matter.

    Conventions:
        - Positive `reduction_pct` = the optimized run did better (lower).
        - Returns 0% when baseline is 0 to avoid div-by-zero confusion.
    """
    def pct(b: float, o: float) -> float:
        return ((b - o) / b * 100) if b > 0 else 0.0

    return {
        "input_tokens": {
            "baseline": baseline["input_tokens"],
            "optimized": optimized["input_tokens"],
            "reduction_pct": pct(baseline["input_tokens"], optimized["input_tokens"]),
        },
        "output_tokens": {
            "baseline": baseline["output_tokens"],
            "optimized": optimized["output_tokens"],
            "reduction_pct": pct(baseline["output_tokens"], optimized["output_tokens"]),
        },
        "total_tokens": {
            "baseline": baseline["total_tokens"],
            "optimized": optimized["total_tokens"],
            "reduction_pct": pct(baseline["total_tokens"], optimized["total_tokens"]),
        },
        "energy_kwh": {
            "baseline": baseline["energy_kwh"],
            "optimized": optimized["energy_kwh"],
            "reduction_pct": pct(baseline["energy_kwh"], optimized["energy_kwh"]),
        },
        "total_emissions_kg": {
            "baseline": baseline["total_emissions_kg"],
            "optimized": optimized["total_emissions_kg"],
            "reduction_pct": pct(baseline["total_emissions_kg"], optimized["total_emissions_kg"]),
        },
        "cost_usd": {
            "baseline": baseline.get("cost_usd", 0.0),
            "optimized": optimized.get("cost_usd", 0.0),
            "reduction_pct": pct(baseline.get("cost_usd", 0.0),
                                 optimized.get("cost_usd", 0.0)),
        },
        # Primary metric for prompt optimization: emissions per user-facing request.
        "sci_per_request": {
            "baseline": baseline.get("sci_per_request"),
            "optimized": optimized.get("sci_per_request"),
            "reduction_pct": pct(baseline.get("sci_per_request") or 0.0,
                                 optimized.get("sci_per_request") or 0.0),
        },
        # Per individual LLM call.
        "sci_per_call": {
            "baseline": baseline.get("sci_per_call"),
            "optimized": optimized.get("sci_per_call"),
            "reduction_pct": pct(baseline.get("sci_per_call") or 0.0,
                                 optimized.get("sci_per_call") or 0.0),
        },
        # Per token (infrastructure-comparison metric; can mislead for prompt opt).
        "sci_per_token": {
            "baseline": baseline.get("sci_per_token") or baseline.get("sci"),
            "optimized": optimized.get("sci_per_token") or optimized.get("sci"),
            "reduction_pct": pct(
                baseline.get("sci_per_token") or baseline.get("sci") or 0.0,
                optimized.get("sci_per_token") or optimized.get("sci") or 0.0,
            ),
        },
        # Backward-compat alias.
        "sci": {
            "baseline": baseline.get("sci"),
            "optimized": optimized.get("sci"),
            "reduction_pct": pct(baseline.get("sci") or 0.0, optimized.get("sci") or 0.0),
        },
    }
