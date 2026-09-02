"""
SCI for AI - the formula, and nothing else.

    SCI = (E * I + M) / R

    E  energy used by the software, in kWh
    I  carbon intensity of the electricity, in kgCO2e per kWh (location-based)
    M  embodied emissions of the hardware, in kgCO2e, share allocated to this work
    R  the functional unit - the unit of useful work you divide by

This file is pure: no I/O, no MCP, no network. It mirrors the formula module
in the GSF `sci-for-ai/llm-inference` reference implementation so the maths
here can be trusted independently of the MCP plumbing in extension.py.

Reference: ISO/IEC 21031:2024 (SCI) and https://sci-for-ai.greensoftware.foundation/
"""

from __future__ import annotations

from dataclasses import dataclass

# Location-based grid carbon intensity, kgCO2e per kWh. Published averages;
# override for your real deployment region. Same table as the llm-inference example.
CARBON_INTENSITY: dict[str, float] = {
    "world-average": 0.475,
    "us-central1": 0.413,
    "us-west1": 0.078,
    "europe-west1": 0.167,
    "europe-north1": 0.058,
    "asia-south1": 0.708,
    "asia-southeast1": 0.408,
}

# Embodied share used when the provider gives no embodied figure.
# Cloud inference embodied share is commonly reported at 8-15%; 0.12 is the midpoint.
EMBODIED_FRACTION = 0.12


@dataclass(frozen=True)
class EnergyProfile:
    """Energy per token for one model, in kWh. Estimates, not measurements."""

    model: str
    kwh_per_input_token: float
    kwh_per_output_token: float
    source: str

    def energy_kwh(self, input_tokens: int, output_tokens: int) -> float:
        return input_tokens * self.kwh_per_input_token + output_tokens * self.kwh_per_output_token


# One small profile is enough for a reference implementation. Values are in the
# range the llm-inference example uses for mini-tier models.
MOCK_PROFILE = EnergyProfile(
    model="mock-mini",
    kwh_per_input_token=1.2e-8,
    kwh_per_output_token=6.0e-8,
    source="Illustrative; mini-tier estimate calibrated in the GSF llm-inference example",
)


@dataclass(frozen=True)
class SciResult:
    """Everything the formula produces for one unit of work."""

    energy_kwh: float
    carbon_intensity: float      # kgCO2e / kWh
    operational_kg: float        # E * I
    embodied_kg: float           # M
    total_kg: float              # E * I + M
    functional_units: float      # R
    sci_kg_per_unit: float | None  # (E*I + M) / R, None when R == 0


def carbon_intensity_for(region: str) -> float:
    """Grid intensity for a region, falling back to the world average."""
    return CARBON_INTENSITY.get(region, CARBON_INTENSITY["world-average"])


def compute_sci(
    energy_kwh: float,
    carbon_intensity: float,
    functional_units: float,
    embodied_kg: float | None = None,
) -> SciResult:
    """Apply SCI = (E * I + M) / R.

    If `embodied_kg` is not given, M is estimated as EMBODIED_FRACTION of the
    operational emissions. Pass a real embodied figure whenever you have one.
    """
    if energy_kwh < 0 or carbon_intensity < 0 or functional_units < 0:
        raise ValueError("inputs must be non-negative")
    operational = energy_kwh * carbon_intensity
    embodied = operational * EMBODIED_FRACTION if embodied_kg is None else embodied_kg
    total = operational + embodied
    sci = total / functional_units if functional_units > 0 else None
    return SciResult(
        energy_kwh=energy_kwh,
        carbon_intensity=carbon_intensity,
        operational_kg=operational,
        embodied_kg=embodied,
        total_kg=total,
        functional_units=functional_units,
        sci_kg_per_unit=sci,
    )
