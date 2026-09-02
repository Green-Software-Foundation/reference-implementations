"""The formula must be right before anything else matters."""
import pytest

from mcp_sci.sci import EMBODIED_FRACTION, carbon_intensity_for, compute_sci


def test_formula_matches_hand_calculation():
    # E=0.001 kWh, I=0.5 kg/kWh, M=0.0001 kg, R=2 -> (0.0005 + 0.0001)/2 = 0.0003
    r = compute_sci(energy_kwh=0.001, carbon_intensity=0.5, functional_units=2, embodied_kg=0.0001)
    assert r.operational_kg == pytest.approx(0.0005)
    assert r.total_kg == pytest.approx(0.0006)
    assert r.sci_kg_per_unit == pytest.approx(0.0003)


def test_embodied_defaults_to_fraction_of_operational():
    r = compute_sci(energy_kwh=1.0, carbon_intensity=1.0, functional_units=1)
    assert r.embodied_kg == pytest.approx(EMBODIED_FRACTION)


def test_zero_units_gives_no_sci_not_zero():
    assert compute_sci(0.001, 0.5, functional_units=0).sci_kg_per_unit is None


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        compute_sci(-1, 0.5, 1)


def test_unknown_region_falls_back_to_world_average():
    assert carbon_intensity_for("nowhere") == carbon_intensity_for("world-average")
