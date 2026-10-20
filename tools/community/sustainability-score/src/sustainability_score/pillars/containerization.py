"""Pillar: Containerization (weight 0.15)."""
from __future__ import annotations

import re

from ..model import Finding

HEAVY_BASES = ("ubuntu", "debian", "centos", "python:3", "node:")
SLIM_HINTS = ("slim", "alpine", "distroless", "-bookworm-slim")


def detect(ctx):
    findings: list[Finding] = []
    notes: list[str] = []

    dockerfiles = [f for f in ctx.files
                   if f.split("/")[-1].lower().startswith("dockerfile")]
    if not dockerfiles:
        notes.append("No Dockerfile found; container checks not applicable "
                     "(scored neutral for this pillar).")
        return findings, notes

    for df in dockerfiles:
        src = ctx.read(df)
        lower = src.lower()

        from_lines = [(i + 1, l) for i, l in enumerate(src.splitlines())
                      if l.strip().lower().startswith("from ")]
        base_is_slim = any(any(h in l.lower() for h in SLIM_HINTS) for _, l in from_lines)
        base_is_heavy = any(any(l.lower().split()[1].startswith(h) for h in HEAVY_BASES)
                            for _, l in from_lines if len(l.split()) > 1)

        if base_is_heavy and not base_is_slim:
            ln = from_lines[0][0]
            findings.append(Finding(
                pillar="containerization",
                id="CN-HEAVY-BASE",
                title="Full-fat base image inflates embodied + transfer footprint",
                severity="medium",
                tier=1,
                evidence=f"{df}:{ln}",
                recommendation="Switch to a slim/distroless/alpine base or a multi-stage "
                               "build; smaller images pull faster and use less registry "
                               "storage and cold-start energy (M, E).",
            ))

        if "as builder" not in lower and "as build" not in lower and \
           any(k in lower for k in ("pip install", "npm install", "go build", "mvn ")):
            findings.append(Finding(
                pillar="containerization",
                id="CN-NO-MULTISTAGE",
                title="Build toolchain shipped in the runtime image",
                severity="low",
                tier=1,
                evidence=df,
                recommendation="Use a multi-stage build so compilers/build deps do not ship "
                               "in the final image.",
            ))

        if not re.search(r"^\s*USER\s+\w", src, re.MULTILINE):
            findings.append(Finding(
                pillar="containerization",
                id="CN-NO-USER",
                title="Container runs as root (no USER directive)",
                severity="low",
                tier=1,
                evidence=df,
                recommendation="Add a non-root USER. Sustainability-adjacent hardening; "
                               "does not change carbon directly.",
            ))

    # Missing resource requests/limits in k8s manifests.
    for f in ctx.glob(".yaml", ".yml"):
        txt = ctx.read(f)
        if "kind: Deployment" in txt or "kind: StatefulSet" in txt:
            if "resources:" not in txt:
                findings.append(Finding(
                    pillar="containerization",
                    id="CN-NO-RESOURCE-LIMITS",
                    title="Workload has no CPU/memory requests or limits",
                    severity="medium",
                    tier=1,
                    evidence=f,
                    recommendation="Set requests/limits so the scheduler can bin-pack "
                                   "efficiently instead of stranding node capacity (M, E).",
                    slo_risk="Set limits from observed p99 usage, not guesses; limits set "
                             "too low can throttle or OOM-kill under load.",
                ))
    return findings, notes
