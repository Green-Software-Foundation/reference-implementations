"""Turn findings into pillar scores and a weighted composite."""
from __future__ import annotations

from .config import PILLARS, SEVERITY_PENALTY, GRADE_BANDS
from .model import PillarResult


def _grade(score: float) -> str:
    for threshold, letter in GRADE_BANDS:
        if score >= threshold:
            return letter
    return "F"


def score_pillar(key: str, findings, notes) -> PillarResult:
    meta = PILLARS[key]
    applicable = not any("not applicable" in n.lower() for n in notes)

    if not applicable:
        return PillarResult(key=key, label=meta["label"], weight=meta["weight"],
                            score=None, tier=1, findings=findings, notes=notes)

    penalty = sum(SEVERITY_PENALTY.get(f.severity, 0) for f in findings)
    score = max(0.0, 100.0 - penalty)
    tier = min([f.tier for f in findings], default=1)
    return PillarResult(key=key, label=meta["label"], weight=meta["weight"],
                        score=round(score, 1), tier=tier, findings=findings, notes=notes)


def composite(pillars: list[PillarResult]) -> tuple[float, str, int]:
    """Weighted mean over APPLICABLE pillars, with weights renormalized so a
    non-applicable pillar neither helps nor hurts the score."""
    scored = [p for p in pillars if p.score is not None]
    total_weight = sum(p.weight for p in scored)
    if total_weight == 0:
        return 0.0, "F", 1
    value = sum(p.score * p.weight for p in scored) / total_weight
    overall_tier = min((p.tier for p in scored), default=1)
    return round(value, 1), _grade(value), overall_tier
