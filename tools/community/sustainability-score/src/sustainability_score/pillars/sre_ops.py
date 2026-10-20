"""Pillar: SRE / Operations (weight 0.15).

Observability and capacity discipline are what let a team *find* waste without
hurting reliability. Absence of them caps how far any efficiency work can go.
"""
from __future__ import annotations

from ..model import Finding

OBS_HINTS = ("prometheus", "opentelemetry", "otel", "datadog", "grafana",
             "newrelic", "new_relic", "sentry", "cloudwatch", "statsd")


def detect(ctx):
    findings: list[Finding] = []
    notes: list[str] = []

    corpus = ""
    for f in (ctx.basename_matches("requirements.txt", "package.json", "go.mod",
                                   "pom.xml", "build.gradle", "pyproject.toml")
              + ctx.glob(".yaml", ".yml")):
        corpus += ctx.read(f).lower()

    has_obs = any(h in corpus for h in OBS_HINTS)
    if not has_obs:
        findings.append(Finding(
            pillar="sre_ops",
            id="SRE-NO-OBSERVABILITY",
            title="No observability/metrics stack detected in manifests",
            severity="high",
            tier=1,
            evidence="dependency manifests / k8s manifests",
            recommendation="Instrument with metrics (utilization, request rate, saturation). "
                           "You cannot right-size or prove an efficiency win you cannot "
                           "measure. This is the precondition for reaching Tier 3.",
        ))
    else:
        notes.append("Observability tooling detected in manifests.")

    # Health checks / probes -> lets platform reclaim unhealthy capacity.
    k8s = [f for f in ctx.glob(".yaml", ".yml") if "kind: Deployment" in ctx.read(f)]
    for f in k8s:
        txt = ctx.read(f)
        if "livenessProbe" not in txt and "readinessProbe" not in txt:
            findings.append(Finding(
                pillar="sre_ops",
                id="SRE-NO-PROBES",
                title="Deployment without liveness/readiness probes",
                severity="low",
                tier=1,
                evidence=f,
                recommendation="Add probes so the platform can route around and reclaim "
                               "unhealthy pods rather than wasting capacity on them.",
                slo_risk="None; probes improve resiliency. Tune thresholds to avoid "
                         "premature restarts.",
            ))

    # Retry-without-backoff smell (retry storms waste compute).
    for f in ctx.glob(".py", ".js", ".ts", ".go", ".java"):
        txt = ctx.read(f).lower()
        if "retry" in txt and "backoff" not in txt and "jitter" not in txt:
            findings.append(Finding(
                pillar="sre_ops",
                id="SRE-RETRY-NO-BACKOFF",
                title="Retry logic without visible backoff/jitter",
                severity="low",
                tier=1,
                evidence=f,
                recommendation="Add exponential backoff with jitter; naive retries amplify "
                               "load during incidents, burning compute for no progress.",
                slo_risk="None; backoff improves stability under failure.",
            ))
            break
    return findings, notes
