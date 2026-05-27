"""Tests for the pure SCI math module."""

from __future__ import annotations

import math

import pytest

from sci_for_ai.sci import (DEFAULT_CARBON_INTENSITY, CallMeasurement,
                            aggregate, carbon_intensity_for, compare,
                            estimate_embodied_kg, sci_score)


# ----------------------------------------------------------------------
# sci_score
# ----------------------------------------------------------------------
class TestSciScore:
    def test_basic_calculation(self):
        # 1 kWh * 0.5 kgCO2/kWh = 0.5 kgCO2 / 1000 tokens = 5e-4 kg/token
        result = sci_score(energy_kwh=1.0, tokens=1000, carbon_intensity=0.5)
        assert math.isclose(result, 5e-4)

    def test_with_embodied(self):
        # (1 * 0.5 + 0.1) / 1000 = 6e-4
        result = sci_score(energy_kwh=1.0, tokens=1000,
                           carbon_intensity=0.5, embodied_kg=0.1)
        assert math.isclose(result, 6e-4)

    def test_zero_tokens_returns_none(self):
        # 0 tokens means SCI is undefined; we must not return 0.
        assert sci_score(energy_kwh=1.0, tokens=0, carbon_intensity=0.5) is None

    def test_negative_tokens_returns_none(self):
        assert sci_score(energy_kwh=1.0, tokens=-5, carbon_intensity=0.5) is None

    def test_negative_energy_raises(self):
        with pytest.raises(ValueError):
            sci_score(energy_kwh=-1.0, tokens=100, carbon_intensity=0.5)

    def test_negative_carbon_intensity_raises(self):
        with pytest.raises(ValueError):
            sci_score(energy_kwh=1.0, tokens=100, carbon_intensity=-0.1)

    def test_negative_embodied_raises(self):
        with pytest.raises(ValueError):
            sci_score(energy_kwh=1.0, tokens=100, carbon_intensity=0.5, embodied_kg=-0.1)

    def test_zero_energy_zero_embodied_gives_zero(self):
        assert sci_score(energy_kwh=0.0, tokens=100, carbon_intensity=0.5) == 0.0


# ----------------------------------------------------------------------
# carbon_intensity_for
# ----------------------------------------------------------------------
class TestCarbonIntensity:
    def test_known_region(self):
        assert carbon_intensity_for("us-central1") == DEFAULT_CARBON_INTENSITY["us-central1"]

    def test_unknown_region_falls_back_to_world_average(self):
        assert carbon_intensity_for("mars-base-1") == DEFAULT_CARBON_INTENSITY["world-average"]

    def test_low_carbon_region(self):
        # Finland should be lower than Mumbai
        assert carbon_intensity_for("europe-north1") < carbon_intensity_for("asia-south1")


# ----------------------------------------------------------------------
# estimate_embodied_kg
# ----------------------------------------------------------------------
class TestEmbodied:
    def test_default_fraction(self):
        # 0.12 default fraction
        assert math.isclose(estimate_embodied_kg(1.0), 0.12)

    def test_custom_fraction(self):
        assert math.isclose(estimate_embodied_kg(2.0, fraction=0.25), 0.5)

    def test_zero_operational(self):
        assert estimate_embodied_kg(0.0) == 0.0

    def test_invalid_fraction_raises(self):
        with pytest.raises(ValueError):
            estimate_embodied_kg(1.0, fraction=1.5)
        with pytest.raises(ValueError):
            estimate_embodied_kg(1.0, fraction=-0.1)

    def test_negative_operational_raises(self):
        with pytest.raises(ValueError):
            estimate_embodied_kg(-1.0)


# ----------------------------------------------------------------------
# CallMeasurement
# ----------------------------------------------------------------------
class TestCallMeasurement:
    def _make(self, **overrides) -> CallMeasurement:
        defaults = dict(
            phase="test", input_tokens=100, output_tokens=200,
            energy_kwh=0.001, carbon_intensity=0.5, embodied_kg=0.00005,
        )
        defaults.update(overrides)
        return CallMeasurement(**defaults)

    def test_total_tokens(self):
        assert self._make().total_tokens == 300

    def test_operational_kg(self):
        m = self._make()
        assert math.isclose(m.operational_kg, 0.001 * 0.5)

    def test_total_emissions(self):
        m = self._make()
        assert math.isclose(m.total_emissions_kg, 0.001 * 0.5 + 0.00005)

    def test_sci(self):
        m = self._make()
        expected = (0.001 * 0.5 + 0.00005) / 300
        assert math.isclose(m.sci, expected)

    def test_sci_zero_tokens(self):
        m = self._make(input_tokens=0, output_tokens=0)
        assert m.sci is None

    def test_immutable(self):
        m = self._make()
        with pytest.raises(Exception):  # FrozenInstanceError, but exact class varies
            m.input_tokens = 999  # type: ignore[misc]

    def test_to_dict_roundtrip(self):
        m = self._make()
        d = m.to_dict()
        assert d["total_tokens"] == 300
        assert "sci" in d
        assert "operational_kg" in d


# ----------------------------------------------------------------------
# aggregate
# ----------------------------------------------------------------------
class TestAggregate:
    def test_empty(self):
        result = aggregate([])
        assert result["total_tokens"] == 0
        assert result["sci"] is None
        assert result["n_calls"] == 0

    def test_single(self):
        m = CallMeasurement(
            phase="x", input_tokens=10, output_tokens=20,
            energy_kwh=0.001, carbon_intensity=0.4, embodied_kg=0.0001,
        )
        result = aggregate([m])
        assert result["total_tokens"] == 30
        assert result["n_calls"] == 1
        assert math.isclose(result["energy_kwh"], 0.001)

    def test_multiple_sums_correctly(self):
        ms = [
            CallMeasurement(phase="a", input_tokens=10, output_tokens=20,
                            energy_kwh=0.001, carbon_intensity=0.4, embodied_kg=0.0001),
            CallMeasurement(phase="b", input_tokens=30, output_tokens=40,
                            energy_kwh=0.002, carbon_intensity=0.4, embodied_kg=0.0002),
        ]
        result = aggregate(ms)
        assert result["input_tokens"] == 40
        assert result["output_tokens"] == 60
        assert result["total_tokens"] == 100
        assert math.isclose(result["energy_kwh"], 0.003)
        assert math.isclose(result["operational_kg"], 0.003 * 0.4)
        assert math.isclose(result["embodied_kg"], 0.0003)

    def test_embodied_percentage(self):
        m = CallMeasurement(
            phase="x", input_tokens=10, output_tokens=10,
            energy_kwh=1.0, carbon_intensity=1.0, embodied_kg=0.25,
        )
        # operational = 1.0, embodied = 0.25, total = 1.25, embodied_pct = 20%
        result = aggregate([m])
        assert math.isclose(result["embodied_pct"], 20.0)

    def test_sci_per_request_equals_total_emissions(self):
        """SCI/request with R=1 should equal total emissions exactly."""
        ms = [
            CallMeasurement(phase="a", input_tokens=10, output_tokens=20,
                            energy_kwh=0.001, carbon_intensity=0.4, embodied_kg=0.0001),
            CallMeasurement(phase="b", input_tokens=30, output_tokens=40,
                            energy_kwh=0.002, carbon_intensity=0.4, embodied_kg=0.0002),
        ]
        result = aggregate(ms)
        assert math.isclose(result["sci_per_request"], result["total_emissions_kg"])

    def test_sci_per_call_amortises_correctly(self):
        """SCI/call = total emissions / number of calls."""
        ms = [
            CallMeasurement(phase=f"call-{i}", input_tokens=10, output_tokens=10,
                            energy_kwh=0.001, carbon_intensity=0.5, embodied_kg=0.0)
            for i in range(3)
        ]
        result = aggregate(ms)
        expected = result["total_emissions_kg"] / 3
        assert math.isclose(result["sci_per_call"], expected)

    def test_sci_per_token_legacy_alias(self):
        """The legacy 'sci' key should equal 'sci_per_token' for backward compat."""
        ms = [
            CallMeasurement(phase="x", input_tokens=10, output_tokens=20,
                            energy_kwh=0.001, carbon_intensity=0.4, embodied_kg=0.0001),
        ]
        result = aggregate(ms)
        assert result["sci"] == result["sci_per_token"]

    def test_empty_measurements_no_sci(self):
        """Empty measurement list gives None for all SCI metrics."""
        result = aggregate([])
        assert result["sci_per_request"] is None
        assert result["sci_per_call"] is None
        assert result["sci_per_token"] is None


# ----------------------------------------------------------------------
# compare
# ----------------------------------------------------------------------
class TestCompare:
    def _mk_totals(self, *, input_tok, output_tok, energy, emissions, sci_val):
        return {
            "input_tokens": input_tok,
            "output_tokens": output_tok,
            "total_tokens": input_tok + output_tok,
            "energy_kwh": energy,
            "total_emissions_kg": emissions,
            "sci": sci_val,
        }

    def test_improvement(self):
        baseline = self._mk_totals(input_tok=1000, output_tok=2000,
                                   energy=0.001, emissions=0.0005, sci_val=1.67e-7)
        optimized = self._mk_totals(input_tok=400, output_tok=800,
                                    energy=0.0004, emissions=0.0002, sci_val=1.67e-7)
        result = compare(baseline, optimized)
        # 1000 -> 400 = 60% reduction
        assert math.isclose(result["input_tokens"]["reduction_pct"], 60.0)
        # 2000 -> 800 = 60%
        assert math.isclose(result["output_tokens"]["reduction_pct"], 60.0)

    def test_zero_baseline_safe(self):
        baseline = self._mk_totals(input_tok=0, output_tok=0,
                                   energy=0, emissions=0, sci_val=None)
        optimized = self._mk_totals(input_tok=100, output_tok=100,
                                    energy=0.0001, emissions=0.00005, sci_val=2.5e-7)
        result = compare(baseline, optimized)
        # No division-by-zero panic
        assert result["input_tokens"]["reduction_pct"] == 0.0

    def test_regression(self):
        # Optimized worse than baseline → negative reduction
        baseline = self._mk_totals(input_tok=100, output_tok=100,
                                   energy=0.0001, emissions=0.00005, sci_val=2.5e-7)
        optimized = self._mk_totals(input_tok=200, output_tok=200,
                                    energy=0.0002, emissions=0.0001, sci_val=2.5e-7)
        result = compare(baseline, optimized)
        # 100 -> 200 means reduction_pct = -100%
        assert math.isclose(result["input_tokens"]["reduction_pct"], -100.0)
