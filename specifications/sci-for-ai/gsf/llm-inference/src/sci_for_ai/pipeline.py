"""
Three-phase Planner → Collector → Writer pipeline and comparison runner.

This is the orchestration layer. Two top-level operations:

  * `run_pipeline(provider, prompt_set, query)` — one full run.
  * `compare_prompt_sets(provider, baseline, optimized, query)` — runs both
    and returns the side-by-side delta.

Design notes:

  * Phases short-circuit on empty output. If a prior phase returns no
    usable content, the pipeline stops rather than making further calls
    that would add to the measured footprint without producing usable
    output.
  * Each phase is a pure call to the provider; the pipeline owns no
    network state. This keeps it testable with `MockProvider`.
  * The comparison runner is deliberately sequential, not parallel.
    Parallelism saves wall-clock time but not energy; for a reference
    implementation, the simpler sequential flow is easier to follow.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .prompts import PromptSet
from .providers import LLMProvider
from .sci import CallMeasurement, aggregate, compare

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Full result of one pipeline run."""
    query: str
    prompt_set_name: str
    plan: str
    insights: str
    report: str
    measurements: list[CallMeasurement]
    totals: dict[str, Any]
    energy_source: str = "estimated"   # "measured" if any call used EcoLogits, else "estimated"
    model: str = "unknown"             # model id used for the run
    region: str = "unknown"            # region / carbon-intensity zone

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "prompt_set": self.prompt_set_name,
            "plan": self.plan,
            "insights": self.insights,
            "report": self.report,
            "measurements": [m.to_dict() for m in self.measurements],
            "totals": self.totals,
            "energy_source": self.energy_source,
            "model": self.model,
            "region": self.region,
        }


class PipelineError(RuntimeError):
    """Raised when a phase produces no output."""


def run_pipeline(
    provider: LLMProvider,
    prompt_set: PromptSet,
    query: str,
    *,
    max_output_tokens: int = 1024,
) -> PipelineResult:
    """
    Run Planner → Collector → Writer for `query` using `prompt_set`.
    """
    if not query or not query.strip():
        raise ValueError("query must be non-empty")

    logger.info("[%s] planning: %s", prompt_set.name, query)
    plan_result = provider.generate(
        prompt_set.planner.format(query=query),
        phase=f"{prompt_set.name}:planning",
        max_output_tokens=max_output_tokens,
    )
    if not plan_result.text.strip():
        raise PipelineError("planning phase produced no output")

    logger.info("[%s] collecting", prompt_set.name)
    insights_result = provider.generate(
        prompt_set.collector.format(plan=plan_result.text),
        phase=f"{prompt_set.name}:collection",
        max_output_tokens=max_output_tokens,
    )
    if not insights_result.text.strip():
        raise PipelineError("collection phase produced no output")

    logger.info("[%s] writing", prompt_set.name)
    report_result = provider.generate(
        prompt_set.writer.format(
            plan=plan_result.text,
            insights=insights_result.text,
        ),
        phase=f"{prompt_set.name}:writing",
        max_output_tokens=max_output_tokens,
    )
    if not report_result.text.strip():
        raise PipelineError("writing phase produced no output")

    measurements = [
        plan_result.measurement,
        insights_result.measurement,
        report_result.measurement,
    ]
    totals = aggregate(measurements)

    # If any call used measured (EcoLogits) energy, report the whole run
    # as "measured" — but only when *all* calls did, to keep the label
    # unambiguous. Mixed runs report as "mixed".
    sources = {plan_result.energy_source, insights_result.energy_source,
               report_result.energy_source}
    if sources == {"measured"}:
        energy_source = "measured"
    elif sources == {"estimated"}:
        energy_source = "estimated"
    else:
        energy_source = "mixed"

    return PipelineResult(
        query=query,
        prompt_set_name=prompt_set.name,
        plan=plan_result.text,
        insights=insights_result.text,
        report=report_result.text,
        measurements=measurements,
        totals=totals,
        energy_source=energy_source,
        model=getattr(provider, "model_id", "unknown"),
        region=getattr(provider, "region", "unknown"),
    )


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Side-by-side result of two pipeline runs."""
    query: str
    baseline: PipelineResult
    optimized: PipelineResult
    delta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "baseline": self.baseline.to_dict(),
            "optimized": self.optimized.to_dict(),
            "delta": self.delta,
        }


def compare_prompt_sets(
    provider: LLMProvider,
    baseline: PromptSet,
    optimized: PromptSet,
    query: str,
    *,
    max_output_tokens: int = 1024,
) -> ComparisonResult:
    """Run two prompt sets sequentially and return the comparison."""
    baseline_run = run_pipeline(provider, baseline, query, max_output_tokens=max_output_tokens)
    optimized_run = run_pipeline(provider, optimized, query, max_output_tokens=max_output_tokens)
    delta = compare(baseline_run.totals, optimized_run.totals)
    return ComparisonResult(
        query=query,
        baseline=baseline_run,
        optimized=optimized_run,
        delta=delta,
    )
