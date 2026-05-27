#!/usr/bin/env python3
"""
Generate the cross-model comparison table for the README from the
recorded fixtures in docs/fixtures/.

This script reads each fixture, projects per-request metrics to 10,000
requests/day, and emits a markdown table that can be pasted into the
README. The point is reproducibility: anyone who re-records the fixtures
can rerun this and see the same table with their updated numbers.

Run from the repo root:
    python scripts/build_cross_model_table.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Fixtures we expect, in display order (lowest pricing → highest pricing).
# Add a new model by recording a fixture and adding a row here.
FIXTURES = [
    ("docs/fixtures/openai-gpt-4o-mini.json", "gpt-4o-mini",  "non-reasoning"),
    ("docs/fixtures/openai-gpt-4o.json",      "gpt-4o",       "non-reasoning"),
    ("docs/fixtures/openai-gpt-5.4.json",     "gpt-5.4",      "reasoning"),
]

REQUESTS_PER_DAY = 10_000
EQUIV_KG_CO2_PER_KM_CAR = 0.171      # EPA passenger car average


def fmt_kg(v: float) -> str:
    if v >= 1.0:
        return f"{v:.2f} kg"
    if v >= 1e-3:
        return f"{v * 1000:.1f} g"
    return f"{v * 1e6:.1f} mg"


def fmt_usd(v: float) -> str:
    if v >= 1000:
        return f"${v:,.0f}"
    if v >= 1.0:
        return f"${v:,.2f}"
    if v >= 0.01:
        return f"${v:.4f}"
    return f"${v:.6f}"


def fmt_pct(v: float) -> str:
    return f"-{v:.1f}%"


def load_fixture(repo_root: Path, rel_path: str) -> dict:
    path = repo_root / rel_path
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    with open(path) as f:
        return json.load(f)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent

    rows = []
    for rel_path, model_label, kind in FIXTURES:
        try:
            data = load_fixture(repo_root, rel_path)
        except FileNotFoundError as e:
            print(f"  skipping: {e}", file=sys.stderr)
            continue

        b_totals = data["baseline"]["totals"]
        o_totals = data["optimized"]["totals"]

        b_emissions = b_totals["total_emissions_kg"]
        o_emissions = o_totals["total_emissions_kg"]
        b_cost = b_totals.get("cost_usd", 0.0)
        o_cost = o_totals.get("cost_usd", 0.0)

        emis_reduction_pct = (b_emissions - o_emissions) / b_emissions * 100 if b_emissions else 0
        cost_reduction_pct = (b_cost - o_cost) / b_cost * 100 if b_cost else 0

        annual_b_kg = b_emissions * 365 * REQUESTS_PER_DAY
        annual_o_kg = o_emissions * 365 * REQUESTS_PER_DAY
        annual_b_usd = b_cost * 365 * REQUESTS_PER_DAY
        annual_o_usd = o_cost * 365 * REQUESTS_PER_DAY
        annual_save_kg = annual_b_kg - annual_o_kg
        annual_save_usd = annual_b_usd - annual_o_usd
        car_km_avoided = annual_save_kg / EQUIV_KG_CO2_PER_KM_CAR

        rows.append({
            "model": model_label,
            "kind": kind,
            "energy_source": data["baseline"].get("energy_source", "?"),
            "b_emissions_mg": b_emissions * 1e6,
            "o_emissions_mg": o_emissions * 1e6,
            "emis_reduction_pct": emis_reduction_pct,
            "b_cost": b_cost,
            "o_cost": o_cost,
            "cost_reduction_pct": cost_reduction_pct,
            "annual_b_kg": annual_b_kg,
            "annual_o_kg": annual_o_kg,
            "annual_b_usd": annual_b_usd,
            "annual_o_usd": annual_o_usd,
            "annual_save_kg": annual_save_kg,
            "annual_save_usd": annual_save_usd,
            "car_km_avoided": car_km_avoided,
        })

    if not rows:
        print("No fixtures found. Record some with `sci-for-ai compare --record-to ...` first.", file=sys.stderr)
        return 1

    # Emit markdown.
    print("### Per-request results (one report generation)")
    print()
    print("| Model | Type | Baseline | Optimized | Reduction | Baseline cost | Optimized cost | Cost reduction |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(
            f"| `{r['model']}` | {r['kind']} | "
            f"{fmt_kg(r['b_emissions_mg']/1e6)} | {fmt_kg(r['o_emissions_mg']/1e6)} | "
            f"**{fmt_pct(r['emis_reduction_pct'])}** | "
            f"{fmt_usd(r['b_cost'])} | {fmt_usd(r['o_cost'])} | "
            f"**{fmt_pct(r['cost_reduction_pct'])}**"
            f" |"
        )

    print()
    print(f"### At {REQUESTS_PER_DAY:,} requests / day — annualized")
    print()
    print("| Model | Annual emissions (baseline) | Annual cost (baseline) | Annual savings (CO₂) | Annual savings ($) | Car-km avoided |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        print(
            f"| `{r['model']}` | "
            f"{fmt_kg(r['annual_b_kg'])} | {fmt_usd(r['annual_b_usd'])} | "
            f"**{fmt_kg(r['annual_save_kg'])}** | **{fmt_usd(r['annual_save_usd'])}** | "
            f"**{r['car_km_avoided']:,.0f} km**"
            f" |"
        )

    print()
    print(f"_All energy figures measured via EcoLogits. "
          f"All cost figures from OpenAI list pricing (May 2026). "
          f"Recorded on the same query: \"How can I reduce the energy consumption and carbon footprint of a Python web service that processes user-uploaded images for resizing and format conversion?\"_")

    return 0


if __name__ == "__main__":
    sys.exit(main())
