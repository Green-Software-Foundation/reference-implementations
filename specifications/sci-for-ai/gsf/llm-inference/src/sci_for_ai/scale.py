"""
Project a single-request measurement to operational scale.

Per-request impact figures (mg of CO2eq, fractions of a cent) are
useful for engineering comparisons but small enough to feel abstract.
Multiplying by an operational user base gives per-day, per-month, and
per-year projections that are easier to reason about for both
sustainability and finance contexts.

This module is pure: it takes a totals dict from `aggregate()` and
returns the projected values across time horizons. Real-world
equivalents (car-km, household-days of electricity, tree-years of
sequestration) are included to give the numbers tangible reference
points.
"""

from __future__ import annotations

from typing import Any


# Reference equivalents for translating kg CO2eq into intuitive units.
# Values are rounded averages from published sources (see README).
_KG_CO2_PER_KM_CAR = 0.171           # average passenger car, mixed fuel, EPA 2024
_KG_CO2_PER_KWH_HOME = 0.413         # US average grid intensity 2024
_KG_CO2_PER_TREE_YEAR = 21.77        # urban tree CO2 sequestration, USDA Forest Service


def project_to_scale(totals: dict[str, Any],
                     requests_per_day: int = 10_000) -> dict[str, Any]:
    """
    Scale a per-request measurement to per-day / month / year totals.

    `totals` is the dict returned by `aggregate()`. We use only:
      - sci_per_request (kgCO2eq per request)
      - cost_usd (USD per request)
      - energy_kwh (kWh per request)

    Returns a dict with per-day / month / year breakdowns and a few
    real-world equivalents to make the numbers concrete.
    """
    if requests_per_day <= 0:
        raise ValueError("requests_per_day must be positive")

    per_request_kg = totals.get("sci_per_request") or totals.get("total_emissions_kg", 0.0) or 0.0
    per_request_usd = totals.get("cost_usd", 0.0)
    per_request_kwh = totals.get("energy_kwh", 0.0)

    daily_kg = per_request_kg * requests_per_day
    daily_usd = per_request_usd * requests_per_day
    daily_kwh = per_request_kwh * requests_per_day

    monthly_kg = daily_kg * 30
    monthly_usd = daily_usd * 30

    annual_kg = daily_kg * 365
    annual_usd = daily_usd * 365
    annual_kwh = daily_kwh * 365

    return {
        "requests_per_day": requests_per_day,
        "per_request": {
            "emissions_kg": per_request_kg,
            "cost_usd": per_request_usd,
            "energy_kwh": per_request_kwh,
        },
        "per_day": {
            "emissions_kg": daily_kg,
            "cost_usd": daily_usd,
            "energy_kwh": daily_kwh,
        },
        "per_month": {
            "emissions_kg": monthly_kg,
            "cost_usd": monthly_usd,
        },
        "per_year": {
            "emissions_kg": annual_kg,
            "cost_usd": annual_usd,
            "energy_kwh": annual_kwh,
        },
        "equivalents_per_year": {
            "car_km": annual_kg / _KG_CO2_PER_KM_CAR,
            "home_days_electricity": annual_kwh / 30.0,   # ~30 kWh/day avg US home
            "trees_to_offset": annual_kg / _KG_CO2_PER_TREE_YEAR,
        },
    }


def project_comparison(baseline_totals: dict[str, Any],
                       optimized_totals: dict[str, Any],
                       requests_per_day: int = 10_000) -> dict[str, Any]:
    """
    Project both baseline and optimized to scale, plus the savings.

    Returns three dicts: baseline_at_scale, optimized_at_scale, and the
    absolute savings at scale across per-month and per-year horizons,
    with annual real-world equivalents.
    """
    baseline_at_scale = project_to_scale(baseline_totals, requests_per_day)
    optimized_at_scale = project_to_scale(optimized_totals, requests_per_day)

    savings_annual_kg = (baseline_at_scale["per_year"]["emissions_kg"]
                         - optimized_at_scale["per_year"]["emissions_kg"])
    savings_annual_usd = (baseline_at_scale["per_year"]["cost_usd"]
                          - optimized_at_scale["per_year"]["cost_usd"])
    savings_annual_kwh = (baseline_at_scale["per_year"]["energy_kwh"]
                          - optimized_at_scale["per_year"]["energy_kwh"])

    savings_monthly_kg = (baseline_at_scale["per_month"]["emissions_kg"]
                          - optimized_at_scale["per_month"]["emissions_kg"])
    savings_monthly_usd = (baseline_at_scale["per_month"]["cost_usd"]
                           - optimized_at_scale["per_month"]["cost_usd"])

    return {
        "requests_per_day": requests_per_day,
        "baseline": baseline_at_scale,
        "optimized": optimized_at_scale,
        "savings": {
            "per_month": {
                "emissions_kg": savings_monthly_kg,
                "cost_usd": savings_monthly_usd,
            },
            "per_year": {
                "emissions_kg": savings_annual_kg,
                "cost_usd": savings_annual_usd,
                "energy_kwh": savings_annual_kwh,
            },
            "equivalents_per_year": {
                "car_km_avoided": savings_annual_kg / _KG_CO2_PER_KM_CAR,
                "home_days_electricity_saved": savings_annual_kwh / 30.0,
                "trees_planted_equivalent": savings_annual_kg / _KG_CO2_PER_TREE_YEAR,
            },
        },
    }
