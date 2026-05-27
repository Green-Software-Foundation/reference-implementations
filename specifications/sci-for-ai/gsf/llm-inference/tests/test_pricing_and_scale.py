"""Tests for pricing and scale projection."""

from __future__ import annotations

import math

import pytest

from sci_for_ai import (ModelPricing, estimate_cost_usd, pricing_for,
                        project_comparison, project_to_scale,
                        register_model_pricing)


# ----------------------------------------------------------------------
# Pricing
# ----------------------------------------------------------------------
class TestPricing:
    def test_known_model_pricing(self):
        p = pricing_for("gpt-4o-mini")
        assert p.model_id == "gpt-4o-mini"
        assert p.usd_per_million_input == 0.15
        assert p.usd_per_million_output == 0.60

    def test_unknown_model_falls_back(self):
        p = pricing_for("definitely-not-a-real-model-2099")
        assert p.model_id == "unknown"
        # Fallback is not free — that would silently hide cost on unknown models
        assert p.usd_per_million_input > 0

    def test_output_is_more_expensive_than_input(self):
        # Every real model has output > input by 3-6x; sanity check that property.
        for model_id in ("gpt-4o-mini", "gpt-4o", "claude-haiku-4-5", "gemini-2.0-flash"):
            p = pricing_for(model_id)
            assert p.usd_per_million_output > p.usd_per_million_input, (
                f"{model_id} has output cheaper than input — almost certainly wrong"
            )

    def test_cost_calculation(self):
        # gpt-4o-mini: $0.15 input + $0.60 output per million
        # 1M input + 1M output should be $0.75 total
        cost, _ = estimate_cost_usd("gpt-4o-mini", 1_000_000, 1_000_000)
        assert math.isclose(cost, 0.75)

    def test_cost_zero_tokens(self):
        cost, _ = estimate_cost_usd("gpt-4o-mini", 0, 0)
        assert cost == 0.0

    def test_register_custom_pricing(self):
        custom = ModelPricing(
            model_id="my-fine-tuned-9000",
            usd_per_million_input=0.50,
            usd_per_million_output=2.00,
            source="test",
        )
        register_model_pricing(custom)
        assert pricing_for("my-fine-tuned-9000") is custom


# ----------------------------------------------------------------------
# Scale projection
# ----------------------------------------------------------------------
class TestProjectToScale:
    def _totals(self, *, emissions_kg=0.0001, cost=0.002, energy=2e-4):
        return {
            "sci_per_request": emissions_kg,
            "total_emissions_kg": emissions_kg,
            "cost_usd": cost,
            "energy_kwh": energy,
        }

    def test_basic_scaling(self):
        totals = self._totals(emissions_kg=0.0001, cost=0.002, energy=2e-4)
        proj = project_to_scale(totals, requests_per_day=10_000)
        # 0.0001 * 10000 = 1.0 kg/day
        assert math.isclose(proj["per_day"]["emissions_kg"], 1.0)
        # $0.002 * 10000 = $20/day
        assert math.isclose(proj["per_day"]["cost_usd"], 20.0)
        # 1.0 kg/day * 365 = 365 kg/year
        assert math.isclose(proj["per_year"]["emissions_kg"], 365.0)
        # $20 * 365 = $7300
        assert math.isclose(proj["per_year"]["cost_usd"], 7300.0)

    def test_requires_positive_users(self):
        totals = self._totals()
        with pytest.raises(ValueError):
            project_to_scale(totals, requests_per_day=0)
        with pytest.raises(ValueError):
            project_to_scale(totals, requests_per_day=-100)

    def test_equivalents_present(self):
        totals = self._totals()
        proj = project_to_scale(totals, requests_per_day=10_000)
        eqs = proj["equivalents_per_year"]
        assert "car_km" in eqs
        assert "home_days_electricity" in eqs
        assert "trees_to_offset" in eqs
        # All should be positive for nonzero emissions input
        for v in eqs.values():
            assert v >= 0

    def test_handles_missing_cost(self):
        """Totals without cost_usd should default to 0."""
        proj = project_to_scale(
            {"sci_per_request": 1e-4, "total_emissions_kg": 1e-4, "energy_kwh": 1e-4},
            requests_per_day=1000,
        )
        assert proj["per_day"]["cost_usd"] == 0.0


class TestProjectComparison:
    def test_savings_are_baseline_minus_optimized(self):
        baseline = {
            "sci_per_request": 0.0001,
            "total_emissions_kg": 0.0001,
            "cost_usd": 0.003,
            "energy_kwh": 2e-4,
        }
        optimized = {
            "sci_per_request": 0.00006,
            "total_emissions_kg": 0.00006,
            "cost_usd": 0.0015,
            "energy_kwh": 1.2e-4,
        }
        result = project_comparison(baseline, optimized, requests_per_day=10_000)

        # Annual savings = (baseline - optimized) * 365 * 10000
        expected_kg = (0.0001 - 0.00006) * 365 * 10_000
        assert math.isclose(result["savings"]["per_year"]["emissions_kg"], expected_kg)

        expected_usd = (0.003 - 0.0015) * 365 * 10_000
        assert math.isclose(result["savings"]["per_year"]["cost_usd"], expected_usd)

    def test_no_optimization_zero_savings(self):
        same = {
            "sci_per_request": 0.0001,
            "total_emissions_kg": 0.0001,
            "cost_usd": 0.003,
            "energy_kwh": 2e-4,
        }
        result = project_comparison(same, same, requests_per_day=1000)
        assert result["savings"]["per_year"]["emissions_kg"] == 0.0
        assert result["savings"]["per_year"]["cost_usd"] == 0.0
