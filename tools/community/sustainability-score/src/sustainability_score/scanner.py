"""Orchestrates the scan: run every pillar detector, score, assemble result."""
from __future__ import annotations

from datetime import datetime, timezone

from .context import RepoContext
from .pillars import REGISTRY
from .scoring import score_pillar, composite
from .model import ScanResult


def scan(repo_path: str) -> ScanResult:
    ctx = RepoContext(repo_path)

    pillar_results = []
    for key, module in REGISTRY.items():
        findings, notes = module.detect(ctx)
        pillar_results.append(score_pillar(key, findings, notes))

    value, grade, overall_tier = composite(pillar_results)

    applicable = [p for p in pillar_results if p.score is not None]
    return ScanResult(
        repo=repo_path,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        composite_score=value,
        grade=grade,
        overall_tier=overall_tier,
        pillars=pillar_results,
        meta={
            "files_scanned": len(ctx.files),
            "pillars_applicable": [p.key for p in applicable],
            "pillars_not_applicable": [p.key for p in pillar_results if p.score is None],
            "total_findings": sum(len(p.findings) for p in pillar_results),
            "method": "static-analysis-only",
        },
    )
