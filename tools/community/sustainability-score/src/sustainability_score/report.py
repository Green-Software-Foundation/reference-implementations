"""Render a ScanResult as JSON and as an advisory Markdown report."""
from __future__ import annotations

import json

from .config import DATA_QUALITY_TIERS, PILLARS
from .model import ScanResult

SEV_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


def to_json(result: ScanResult) -> str:
    return json.dumps(result.as_dict(), indent=2)


def to_markdown(result: ScanResult) -> str:
    lines: list[str] = []
    tier = DATA_QUALITY_TIERS[result.overall_tier]

    lines.append(f"# Sustainability Score Report")
    lines.append("")
    lines.append(f"**Repository:** `{result.repo}`  ")
    lines.append(f"**Generated:** {result.generated_at}  ")
    lines.append(f"**Method:** static analysis only  ")
    lines.append("")
    lines.append(f"## Score: {result.composite_score}/100 (Grade {result.grade})")
    lines.append("")
    lines.append(f"> Confidence: **Tier {result.overall_tier} - {tier['label']}** "
                 f"({tier['confidence']}). {tier['description']}")
    lines.append(">")
    lines.append("> This report is **advisory**. Nothing here should gate a build or "
                 "deploy. Every recommendation that could affect capacity or resiliency "
                 "states the SLO trade-off explicitly.")
    lines.append("")
    lines.append("Grounded in the Green Software Foundation "
                 "[Software Carbon Intensity (SCI)](https://sci.greensoftware.foundation/) "
                 "specification: `SCI = ((E x I) + M) / R`.")
    lines.append("")

    # Pillar table.
    lines.append("## Pillars")
    lines.append("")
    lines.append("| Pillar | Weight | Score | Confidence |")
    lines.append("|---|---:|---:|---|")
    for p in result.pillars:
        score = "n/a" if p.score is None else f"{p.score:g}"
        conf = "not applicable" if p.score is None else f"Tier {p.tier}"
        lines.append(f"| {p.label} | {int(p.weight*100)}% | {score} | {conf} |")
    lines.append("")

    # Findings by pillar.
    lines.append("## Findings")
    lines.append("")
    total = 0
    for p in result.pillars:
        lines.append(f"### {p.label}")
        if p.notes:
            for n in p.notes:
                lines.append(f"_{n}_")
                lines.append("")
        if not p.findings:
            lines.append("No findings.")
            lines.append("")
            continue
        for f in sorted(p.findings, key=lambda x: SEV_ORDER.get(x.severity, 9)):
            total += 1
            lines.append(f"- **[{f.severity.upper()}] {f.title}** "
                         f"(`{f.id}`, Tier {f.tier})")
            lines.append(f"  - Evidence: `{f.evidence}`")
            lines.append(f"  - Advice: {f.recommendation}")
            if f.slo_risk:
                lines.append(f"  - SLO/resiliency note: {f.slo_risk}")
            if f.ghg_scope:
                lines.append(f"  - GHG mapping: {f.ghg_scope}")
        lines.append("")

    # Sample non-blocking PR comment.
    lines.append("## Sample PR comment (advisory, non-blocking)")
    lines.append("")
    lines.append("```markdown")
    lines.append(_pr_comment(result))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _pr_comment(result: ScanResult) -> str:
    tier = DATA_QUALITY_TIERS[result.overall_tier]
    top = []
    for p in result.pillars:
        for f in p.findings:
            if f.severity in ("high", "medium"):
                top.append(f"- {f.title} (`{f.evidence}`)")
    top = top[:3]
    body = [
        f"Sustainability score: **{result.composite_score}/100 (Grade {result.grade})** "
        f"- confidence Tier {result.overall_tier} ({tier['confidence']}).",
        "",
        "This is an advisory signal, not a gate. A few directional suggestions:" if top
        else "No medium/high sustainability findings on this change. Nice.",
    ]
    body += top
    body += ["", "_Scores are directional from static analysis; see the full report "
             "for SLO trade-offs before acting._"]
    return "\n".join(body)
