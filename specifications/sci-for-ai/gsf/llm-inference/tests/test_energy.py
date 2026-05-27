"""Tests for the energy estimation module."""

from __future__ import annotations

import math

from sci_for_ai.energy import (ModelEnergyProfile, estimate_kwh, profile_for,
                               register_model_energy)


def test_known_model_profile():
    profile = profile_for("gemini-2.0-flash")
    assert profile.model_id == "gemini-2.0-flash"
    assert profile.kwh_per_input_token > 0
    assert profile.kwh_per_output_token > profile.kwh_per_input_token  # output is more expensive


def test_unknown_model_falls_back():
    profile = profile_for("nonexistent-model-9000")
    assert profile.model_id == "unknown"
    assert "Fallback" in profile.source


def test_estimate_kwh_known_model():
    kwh, source = estimate_kwh("gemini-2.0-flash", 100, 200)
    profile = profile_for("gemini-2.0-flash")
    expected = 100 * profile.kwh_per_input_token + 200 * profile.kwh_per_output_token
    assert math.isclose(kwh, expected)
    assert source  # source string non-empty


def test_estimate_kwh_zero_tokens():
    kwh, _ = estimate_kwh("gemini-2.0-flash", 0, 0)
    assert kwh == 0.0


def test_output_tokens_more_expensive_than_input():
    # Same total, all-output costs more than all-input — verifies the
    # asymmetry that motivates output-length compression.
    input_heavy, _ = estimate_kwh("claude-haiku-4-5", 1000, 0)
    output_heavy, _ = estimate_kwh("claude-haiku-4-5", 0, 1000)
    assert output_heavy > input_heavy


def test_register_model_energy():
    custom = ModelEnergyProfile(
        model_id="test-custom-model",
        kwh_per_input_token=1e-9,
        kwh_per_output_token=1e-8,
        source="test",
    )
    register_model_energy(custom)
    looked_up = profile_for("test-custom-model")
    assert looked_up is custom
