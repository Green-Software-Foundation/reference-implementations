"""Core data structures shared across pillar detectors and reporting."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Finding:
    """A single observation from a pillar detector.

    Findings are ADVISORY. They never gate a build. `severity` reflects
    sustainability impact, not correctness. Every finding declares the
    data-quality `tier` its evidence actually supports and the SLO/resiliency
    risk of acting on it (empty string = no capacity/resiliency trade-off).
    """
    pillar: str
    id: str
    title: str
    severity: str            # high | medium | low | info
    tier: int                # 1..4 data-quality tier
    evidence: str            # file:line or file, human-readable
    recommendation: str      # advisory, non-blocking
    slo_risk: str = ""       # explicit resiliency/capacity trade-off, if any
    ghg_scope: str = ""      # optional GHG Protocol mapping note

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class PillarResult:
    key: str
    label: str
    weight: float
    score: float                       # 0..100
    tier: int                          # lowest-confidence tier represented
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["findings"] = [f.as_dict() for f in self.findings]
        return d


@dataclass
class ScanResult:
    repo: str
    generated_at: str
    composite_score: float
    grade: str
    overall_tier: int
    pillars: list[PillarResult] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["pillars"] = [p.as_dict() for p in self.pillars]
        return d
