"""
Pretty-printing for pipeline and comparison results.

No external dependencies. The output is plain text with optional ANSI
colours; you can pipe it through `less` or redirect to a file without
mangling.
"""

from __future__ import annotations

import sys
from typing import Any

from .pipeline import ComparisonResult, PipelineResult


_USE_COLOR = sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def _bold(text: str) -> str:    return _c(text, "1")
def _green(text: str) -> str:   return _c(text, "32")
def _red(text: str) -> str:     return _c(text, "31")
def _cyan(text: str) -> str:    return _c(text, "36")
def _dim(text: str) -> str:     return _c(text, "2")


def _fmt_kg(v: float) -> str:
    """Format kg CO2eq with sensible precision."""
    if v >= 1.0:
        return f"{v:.3f} kg"
    if v >= 1e-3:
        return f"{v * 1000:.3f} g"
    return f"{v * 1e6:.3f} mg"


def _fmt_kwh(v: float) -> str:
    if v >= 1.0:
        return f"{v:.3f} kWh"
    return f"{v * 1000:.3f} Wh"


def _fmt_sci(v: float | None) -> str:
    return f"{v:.3e} kgCO2eq/token" if v is not None else "n/a"


def _fmt_usd(v: float) -> str:
    """Format USD with adaptive precision."""
    if v >= 1000:
        return f"${v:,.0f}"
    if v >= 1.0:
        return f"${v:,.2f}"
    if v >= 0.01:
        return f"${v:.4f}"
    if v > 0:
        return f"${v:.6f}"
    return "$0.00"


def _fmt_int(v: float) -> str:
    """Format a large number with commas."""
    return f"{int(round(v)):,}"


def _fmt_pct(v: float) -> str:
    if v > 0:
        return _green(f"-{v:.1f}%")
    if v < 0:
        return _red(f"+{abs(v):.1f}%")
    return "0.0%"


# ----------------------------------------------------------------------
# Public formatters
# ----------------------------------------------------------------------
def format_pipeline(result: PipelineResult) -> str:
    """Single-run report."""
    t = result.totals
    lines = [
        _bold(f"=== Pipeline: {result.prompt_set_name} ==="),
        f"Query: {result.query}",
        "",
        _bold("Per-phase measurements:"),
    ]
    for m in result.measurements:
        lines.append(
            f"  {m.phase:<32} "
            f"tokens={m.input_tokens:>5}+{m.output_tokens:<5}={m.total_tokens:<5} "
            f"energy={_fmt_kwh(m.energy_kwh):<12} "
            f"emissions={_fmt_kg(m.total_emissions_kg):<10} "
            f"wall={m.wall_time_s:.2f}s"
        )
    lines += [
        "",
        _bold("Totals:"),
        f"  Region:            {result.measurements[0].region} "
        f"(I = {result.measurements[0].carbon_intensity} kgCO2eq/kWh)",
        f"  Energy source:     {result.energy_source}"
        f"{'  (EcoLogits)' if result.energy_source == 'measured' else '  (model-card)' if result.energy_source == 'estimated' else ''}",
        f"  Tokens (in/out):   {t['input_tokens']:,} / {t['output_tokens']:,}  (total {t['total_tokens']:,})",
        f"  Energy:            {_fmt_kwh(t['energy_kwh'])}",
        f"  Operational CO2:   {_fmt_kg(t['operational_kg'])}",
        f"  Embodied CO2:      {_fmt_kg(t['embodied_kg'])} ({t['embodied_pct']:.1f}%)",
        f"  Total emissions:   {_bold(_fmt_kg(t['total_emissions_kg']))}",
        f"  SCI / request:     {_bold(_fmt_kg(t.get('sci_per_request') or t['total_emissions_kg']))}  "
        + _dim("(R = 1 pipeline run — primary metric)"),
        f"  SCI / token:       {_fmt_sci(t.get('sci_per_token') or t.get('sci'))}  "
        + _dim("(infrastructure-comparison metric)"),
        f"  Wall time:         {t['wall_time_s']:.2f}s",
    ]
    return "\n".join(lines)


def format_comparison(result: ComparisonResult) -> str:
    """Side-by-side baseline vs optimized comparison."""
    b = result.baseline.totals
    o = result.optimized.totals
    d = result.delta

    # Backward-compat: older fixtures only have "sci" (== per-token).
    sci_per_request_b = b.get("sci_per_request") or b.get("total_emissions_kg")
    sci_per_request_o = o.get("sci_per_request") or o.get("total_emissions_kg")
    sci_per_call_b = b.get("sci_per_call")
    sci_per_call_o = o.get("sci_per_call")
    sci_per_token_b = b.get("sci_per_token") or b.get("sci")
    sci_per_token_o = o.get("sci_per_token") or o.get("sci")

    n_calls_b = b.get("n_calls", 0)
    n_calls_o = o.get("n_calls", 0)

    request_delta = d.get("sci_per_request", d.get("total_emissions_kg", {})).get("reduction_pct", 0.0)
    call_delta = d.get("sci_per_call", {}).get("reduction_pct", 0.0)
    token_delta = d.get("sci_per_token", d.get("sci", {})).get("reduction_pct", 0.0)
    em_delta = d['total_emissions_kg']['reduction_pct']

    cost_b = b.get("cost_usd", 0.0)
    cost_o = o.get("cost_usd", 0.0)
    cost_delta = d.get("cost_usd", {}).get("reduction_pct", 0.0)

    lines = [
        _bold(_cyan("================================================================")),
        _bold(_cyan("                  SCI for AI — Comparison Report                ")),
        _bold(_cyan("================================================================")),
        f"Query: {result.query}",
        f"Energy source: {result.baseline.energy_source} (baseline) / "
        f"{result.optimized.energy_source} (optimized)"
        f"{'  — measured via EcoLogits' if result.baseline.energy_source == 'measured' else '  — model-card estimates'}",
        f"Model: {getattr(result.baseline, 'model', 'unknown')}  "
        f"Region: {getattr(result.baseline, 'region', 'unknown')}  "
        f"LLM calls per pipeline run: {n_calls_b} (baseline) / {n_calls_o} (optimized)",
        "",
        _bold("PRIMARY METRIC — SCI per request"),
        _dim("In this tool, one \"request\" = one full report generation = one user query."),
        _dim("The pipeline makes 3 LLM calls (Planner → Collector → Writer) internally,"),
        _dim("but the user-facing unit of work is the generated report. R = 1."),
        _dim("This unit stays consistent across prompt, region, and model changes."),
        "",
        f"{'Metric':<28} {'Baseline':>16} {'Optimized':>16} {'Delta':>12}",
        _dim("-" * 76),
        f"{'SCI per request':<28} {_fmt_kg(sci_per_request_b):>16} "
        f"{_fmt_kg(sci_per_request_o):>16} "
        f"{_fmt_pct(request_delta):>20}",
        f"{'Cost per request':<28} {_fmt_usd(cost_b):>16} {_fmt_usd(cost_o):>16} "
        f"{_fmt_pct(cost_delta):>20}",
        f"{'Total emissions':<28} {_fmt_kg(b['total_emissions_kg']):>16} "
        f"{_fmt_kg(o['total_emissions_kg']):>16} "
        f"{_fmt_pct(em_delta):>20}",
        "",
        _bold("SUPPORTING DETAIL"),
        _dim("-" * 76),
        f"{'Input tokens':<28} {b['input_tokens']:>16,} {o['input_tokens']:>16,} "
        f"{_fmt_pct(d['input_tokens']['reduction_pct']):>20}",
        f"{'Output tokens':<28} {b['output_tokens']:>16,} {o['output_tokens']:>16,} "
        f"{_fmt_pct(d['output_tokens']['reduction_pct']):>20}",
        f"{'Total tokens':<28} {b['total_tokens']:>16,} {o['total_tokens']:>16,} "
        f"{_fmt_pct(d['total_tokens']['reduction_pct']):>20}",
        f"{'Energy':<28} {_fmt_kwh(b['energy_kwh']):>16} {_fmt_kwh(o['energy_kwh']):>16} "
        f"{_fmt_pct(d['energy_kwh']['reduction_pct']):>20}",
        f"{'Avg per LLM call':<28} {_fmt_kg(sci_per_call_b) if sci_per_call_b is not None else 'n/a':>16} "
        f"{_fmt_kg(sci_per_call_o) if sci_per_call_o is not None else 'n/a':>16} "
        f"{_fmt_pct(call_delta):>20}",
        "",
        _bold("ADDITIONAL METRIC — SCI per token"),
        _dim("Comparable across runs where the token workload is held fixed"),
        _dim("(e.g. same prompt, different region / model / hardware). When"),
        _dim("the prompt itself changes, R changes too, so the per-token ratio"),
        _dim("is best read alongside the per-request metric rather than alone."),
        "",
        f"{'SCI / token':<28} {_fmt_sci(sci_per_token_b):>16} "
        f"{_fmt_sci(sci_per_token_o):>16} "
        f"{_fmt_pct(token_delta):>20}",
        "",
    ]

    # Verdict driven by SCI/request (the primary metric).
    NOISE_FLOOR = 5.0

    if request_delta > NOISE_FLOOR:
        verdict = _green(
            f"Optimized prompts show {request_delta:.1f}% lower SCI per request "
            f"than baseline ({_fmt_kg(sci_per_request_b)} → "
            f"{_fmt_kg(sci_per_request_o)} per request)."
        )
    elif abs(request_delta) <= NOISE_FLOOR:
        verdict = (
            "Change in SCI per request is within the measurement model's "
            "resolution — no clear directional difference to report."
        )
    else:
        verdict = _red(
            f"Optimized prompts show {abs(request_delta):.1f}% higher SCI per "
            f"request than baseline."
        )
    lines.append(_bold(verdict))
    return "\n".join(lines)


def format_scale(projection: dict[str, Any]) -> str:
    """
    Format a scale projection (output of `scale.project_comparison`) for the
    terminal. Shows daily / annual emissions and cost at the chosen scale,
    plus real-world equivalents so the numbers feel concrete.
    """
    req_per_day = projection["requests_per_day"]
    b = projection["baseline"]
    o = projection["optimized"]
    s = projection["savings"]

    def _row(label: str, b_val: str, o_val: str, save_val: str) -> str:
        # Pad before colouring so ANSI codes don't break alignment.
        return f"{label:<22} {b_val:>17} {o_val:>17} {_green(f'{save_val:>17}')}"

    lines = [
        "",
        _bold(_cyan("================================================================")),
        _bold(_cyan(f"      SCALE PROJECTION  —  {req_per_day:,} requests / day")),
        _bold(_cyan("================================================================")),
        _dim("Multiplying per-request impact by an operational user base."),
        "",
        f"{'':<22} {'Baseline':>17} {'Optimized':>17} {'Savings':>17}",
        _dim("-" * 76),
        _row("Per day — emissions",
             _fmt_kg(b['per_day']['emissions_kg']),
             _fmt_kg(o['per_day']['emissions_kg']),
             _fmt_kg(b['per_day']['emissions_kg'] - o['per_day']['emissions_kg'])),
        _row("Per day — cost",
             _fmt_usd(b['per_day']['cost_usd']),
             _fmt_usd(o['per_day']['cost_usd']),
             _fmt_usd(b['per_day']['cost_usd'] - o['per_day']['cost_usd'])),
        _row("Per month — emissions",
             _fmt_kg(b['per_month']['emissions_kg']),
             _fmt_kg(o['per_month']['emissions_kg']),
             _fmt_kg(s['per_month']['emissions_kg'])),
        _row("Per month — cost",
             _fmt_usd(b['per_month']['cost_usd']),
             _fmt_usd(o['per_month']['cost_usd']),
             _fmt_usd(s['per_month']['cost_usd'])),
        _row("Per year — emissions",
             _fmt_kg(b['per_year']['emissions_kg']),
             _fmt_kg(o['per_year']['emissions_kg']),
             _fmt_kg(s['per_year']['emissions_kg'])),
        _row("Per year — cost",
             _fmt_usd(b['per_year']['cost_usd']),
             _fmt_usd(o['per_year']['cost_usd']),
             _fmt_usd(s['per_year']['cost_usd'])),
        "",
        _bold("Annual savings translate to:"),
        f"  • {_fmt_int(s['equivalents_per_year']['car_km_avoided']):>10} km of car driving avoided",
        f"  • {_fmt_int(s['equivalents_per_year']['home_days_electricity_saved']):>10} days of average household electricity",
        f"  • {_fmt_int(s['equivalents_per_year']['trees_planted_equivalent']):>10} trees' worth of annual CO₂ sequestration",
        "",
        _dim("Equivalents from EPA/USDA averages; see README for sources."),
    ]
    return "\n".join(lines)


def format_report_preview(result: ComparisonResult, fixture_path: str | None = None,
                          max_lines: int = 30) -> str:
    """
    Show the generated optimized report as a preview, with a pointer to the
    fixture for the full content. We display the first `max_lines` lines so
    the user can see what was generated without dumping a 200-line report
    into the terminal.
    """
    report = result.optimized.report or ""
    report_lines = report.splitlines()
    truncated = len(report_lines) > max_lines
    shown = "\n".join(report_lines[:max_lines])

    lines = [
        "",
        _bold(_cyan("================================================================")),
        _bold(_cyan("        GENERATED REPORT  —  Optimized run output (preview)     ")),
        _bold(_cyan("================================================================")),
        shown,
    ]
    if truncated:
        lines.append(
            _dim(f"\n... [truncated — {len(report_lines) - max_lines} more lines]")
        )
    if fixture_path:
        lines.append("")
        lines.append(_bold(
            f"Full content (both baseline and optimized reports, all metrics, "
            f"per-call breakdowns):"
        ))
        lines.append(f"  → {fixture_path}")
    return "\n".join(lines)
