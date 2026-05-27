"""
Energy estimation for LLM inference.

We support two paths, in order of preference:

  1. **Measured energy** — if the provider returns energy data (e.g. via
     EcoLogits for some SDKs), we use it directly. Always preferred.
  2. **Estimated energy** — derived from public model-card energy-per-token
     figures. Necessary when the provider exposes no telemetry.

The model-card table below is intentionally small and explicit.
Public per-token energy figures are scarce; we cite sources in the README.
Add entries via `register_model_energy()` rather than editing this dict
in your fork — keeps the upstream comparison fair.

All figures: kWh per token.
"""

from __future__ import annotations

from dataclasses import dataclass


# ----------------------------------------------------------------------
# Model energy profiles
# ----------------------------------------------------------------------
# Sources & methodology in docs/SCI_METHODOLOGY.md. Treat these as
# order-of-magnitude estimates rather than direct measurements. When
# adding or updating entries, please record the source so downstream
# users can trace where each number came from.
@dataclass(frozen=True, slots=True)
class ModelEnergyProfile:
    """Per-token energy profile for a model."""
    model_id: str
    kwh_per_input_token: float
    kwh_per_output_token: float
    source: str  # citation note

    def estimate_kwh(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.kwh_per_input_token
                + output_tokens * self.kwh_per_output_token)


# Per-token estimates calibrated against current instrumentation tools
# and present-day transformer inference. These reflect the methodology
# used by EcoLogits 0.10 and similar tools at the time of writing —
# the ratios and per-model values will evolve as architectures, serving
# infrastructure, and measurement methodologies change. Real numbers are
# also workload- and hardware-dependent.
#
# Calibrated against EcoLogits 0.10 measurements (gpt-4o-mini run of
# 3,716 input + 3,072 output tokens measured at 0.226 Wh). The fallback
# path uses these values whenever a measured energy figure isn't
# available from EcoLogits.
_MODEL_ENERGY: dict[str, ModelEnergyProfile] = {
    # Small / efficient models
    "gemini-2.0-flash": ModelEnergyProfile(
        model_id="gemini-2.0-flash",
        kwh_per_input_token=1.2e-8,
        kwh_per_output_token=6.0e-8,
        source="Estimate; mini-tier comparable to gpt-4o-mini measured energy",
    ),
    "gemini-2.5-flash-lite": ModelEnergyProfile(
        model_id="gemini-2.5-flash-lite",
        kwh_per_input_token=1.0e-8,
        kwh_per_output_token=5.5e-8,
        source="Estimate; lite tier comparable to nano-class models",
    ),
    "gemini-2.5-flash": ModelEnergyProfile(
        model_id="gemini-2.5-flash",
        kwh_per_input_token=5.0e-8,
        kwh_per_output_token=3.0e-7,
        source="Estimate; mid-tier flash, similar profile to gpt-4o",
    ),
    "gemini-2.5-pro": ModelEnergyProfile(
        model_id="gemini-2.5-pro",
        kwh_per_input_token=1.8e-7,
        kwh_per_output_token=1.1e-6,
        source="Estimate; flagship-class reasoning. EcoLogits has profile.",
    ),
    "gemini-3-flash-preview": ModelEnergyProfile(
        model_id="gemini-3-flash-preview",
        kwh_per_input_token=8.0e-8,
        kwh_per_output_token=5.0e-7,
        source="Estimate; newer flash generation",
    ),
    "gemini-3.1-pro-preview": ModelEnergyProfile(
        model_id="gemini-3.1-pro-preview",
        kwh_per_input_token=2.5e-7,
        kwh_per_output_token=1.5e-6,
        source="Estimate; newest flagship reasoning model (Feb 2026)",
    ),
    "claude-haiku-4-5": ModelEnergyProfile(
        model_id="claude-haiku-4-5",
        kwh_per_input_token=1.0e-8,
        kwh_per_output_token=5.5e-8,
        source="Estimate from comparable-size open weights benchmarks",
    ),
    "gpt-4o-mini": ModelEnergyProfile(
        model_id="gpt-4o-mini",
        kwh_per_input_token=1.2e-8,
        kwh_per_output_token=5.9e-8,
        source="Calibrated from EcoLogits 0.10 measurement (3716 in + 3072 out = 0.226 Wh)",
    ),
    "gpt-5.4-nano": ModelEnergyProfile(
        model_id="gpt-5.4-nano",
        kwh_per_input_token=1.0e-8,
        kwh_per_output_token=5.5e-8,
        source="Estimate; nano-tier comparable to gpt-4o-mini",
    ),
    # Mid-tier — roughly 5x mini per token (matches the price ratio)
    "gpt-5.4-mini": ModelEnergyProfile(
        model_id="gpt-5.4-mini",
        kwh_per_input_token=5.0e-8,
        kwh_per_output_token=3.0e-7,
        source="Estimate; mini flagship, ~5x mini-tier energy",
    ),
    "claude-sonnet-4-6": ModelEnergyProfile(
        model_id="claude-sonnet-4-6",
        kwh_per_input_token=4.0e-8,
        kwh_per_output_token=2.5e-7,
        source="Estimate from comparable-size open weights benchmarks",
    ),
    "gpt-4o": ModelEnergyProfile(
        model_id="gpt-4o",
        kwh_per_input_token=4.5e-8,
        kwh_per_output_token=3.0e-7,
        source="Estimate; mid-tier ~5x gpt-4o-mini's calibrated value",
    ),
    # Large / frontier — roughly 15-25x mini per token
    "gpt-5.4": ModelEnergyProfile(
        model_id="gpt-5.4",
        kwh_per_input_token=1.8e-7,
        kwh_per_output_token=1.1e-6,
        source="Estimate; current flagship class. EcoLogits 0.10 has profile.",
    ),
    "gpt-5.5": ModelEnergyProfile(
        model_id="gpt-5.5",
        kwh_per_input_token=2.5e-7,
        kwh_per_output_token=1.5e-6,
        source="Estimate; newest flagship (Apr 2026). Not yet in EcoLogits → falls back here.",
    ),
    "gpt-5.5-pro": ModelEnergyProfile(
        model_id="gpt-5.5-pro",
        kwh_per_input_token=5.0e-7,
        kwh_per_output_token=3.0e-6,
        source="Estimate; pro variant uses more reasoning compute",
    ),
    "claude-opus-4-6": ModelEnergyProfile(
        model_id="claude-opus-4-6",
        kwh_per_input_token=2.2e-7,
        kwh_per_output_token=1.3e-6,
        source="Estimate; flagship-class compute. EcoLogits 0.10 has profile.",
    ),
    "claude-opus-4-7": ModelEnergyProfile(
        model_id="claude-opus-4-7",
        kwh_per_input_token=2.5e-7,
        kwh_per_output_token=1.5e-6,
        source="Estimate; newest flagship (Apr 2026). Not yet in EcoLogits — falls back here.",
    ),
}

# Fallback used when we have no profile at all. Sized between mid-tier and
# frontier — better to slightly over-report than to silently miss emissions.
_FALLBACK = ModelEnergyProfile(
    model_id="unknown",
    kwh_per_input_token=8.0e-8,
    kwh_per_output_token=5.0e-7,
    source="Fallback (no model-specific data); see docs/SCI_METHODOLOGY.md",
)


def register_model_energy(profile: ModelEnergyProfile) -> None:
    """Register a custom profile. Useful for fine-tuned, internal, or newly released models."""
    _MODEL_ENERGY[profile.model_id] = profile


def profile_for(model_id: str) -> ModelEnergyProfile:
    """Return the energy profile for `model_id`, falling back if unknown."""
    return _MODEL_ENERGY.get(model_id, _FALLBACK)


def estimate_kwh(model_id: str, input_tokens: int, output_tokens: int) -> tuple[float, str]:
    """
    Estimate energy in kWh. Returns (kwh, source_note) so callers can
    log provenance alongside the value — useful for traceability when
    reporting on green-software metrics.
    """
    profile = profile_for(model_id)
    return profile.estimate_kwh(input_tokens, output_tokens), profile.source
