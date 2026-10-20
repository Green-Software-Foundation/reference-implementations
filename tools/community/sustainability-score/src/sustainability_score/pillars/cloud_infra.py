"""Pillar: Cloud Infrastructure Choices (weight 0.25).

The single largest lever: region carbon intensity, right-sizing, autoscaling.
Reads IaC (Terraform, k8s, serverless) statically. When declared infra is
present, findings can rise to Tier 2 (static + declared infra).
"""
from __future__ import annotations

import re

from ..model import Finding

# Rough relative grid carbon intensity signal for common cloud regions.
# Directional only (Tier 1/2): real intensity is time-varying and provider-
# specific. Higher = dirtier grid.
HIGH_CARBON_REGIONS = {
    "us-east-1", "us-west-2", "ap-south-1", "ap-southeast-1", "ap-southeast-2",
    "eastus", "southeastasia", "australiaeast",
}
LOW_CARBON_REGIONS = {
    "eu-north-1", "eu-west-1", "ca-central-1", "us-west-1",
    "northeurope", "westeurope", "canadacentral", "switzerlandnorth",
}


def detect(ctx):
    findings: list[Finding] = []
    notes: list[str] = []

    tf = ctx.glob(".tf")
    k8s = [f for f in ctx.glob(".yaml", ".yml")
           if "kind:" in ctx.read(f)]
    serverless = ctx.basename_matches("serverless.yml", "serverless.yaml", "template.yaml")

    if not (tf or k8s or serverless):
        notes.append("No infrastructure-as-code found; cloud checks not applicable "
                     "(scored neutral for this pillar).")
        return findings, notes

    declared = bool(tf or serverless)
    tier = 2 if declared else 1
    if declared:
        notes.append("Declared infrastructure found -> cloud findings evaluated at "
                     "Tier 2 (static + declared infra).")

    for f in tf + list(serverless):
        txt = ctx.read(f)

        for m in re.finditer(r'region\s*=\s*"([a-z0-9-]+)"', txt):
            region = m.group(1)
            ln = txt[:m.start()].count("\n") + 1
            if region in HIGH_CARBON_REGIONS:
                findings.append(Finding(
                    pillar="cloud_infra",
                    id="CLOUD-HIGH-CARBON-REGION",
                    title=f"Deploys to a relatively high-carbon region ({region})",
                    severity="medium",
                    tier=tier,
                    evidence=f"{f}:{ln}",
                    recommendation=f"If latency/data-residency allow, prefer a lower-carbon "
                                   f"region. Region choice directly changes carbon intensity "
                                   f"I in SCI.",
                    slo_risk="Region moves affect latency and data residency; validate "
                             "compliance and RTO/RPO before relocating.",
                    ghg_scope="GHG Protocol Scope 3 Category 1 (purchased cloud services).",
                ))

        # Always-on / no real autoscaling. Two smells: (a) a desired_capacity
        # with no scaling policy at all, or (b) an ASG pinned to min == max
        # (fixed size dressed up as an autoscaling group).
        dc = re.search(r"desired_capacity\s*=\s*(\d+)", txt)
        mn = re.search(r"min_size\s*=\s*(\d+)", txt)
        mx = re.search(r"max_size\s*=\s*(\d+)", txt)
        has_policy = ("aws_autoscaling_policy" in txt or "target_tracking" in txt.lower()
                      or "scaling_policy" in txt.lower())
        pinned = mn and mx and mn.group(1) == mx.group(1)
        if dc and (pinned or not has_policy):
            ln = txt[:dc.start()].count("\n") + 1
            findings.append(Finding(
                pillar="cloud_infra",
                id="CLOUD-FIXED-CAPACITY",
                title="Fixed capacity with no effective autoscaling"
                      + (" (min == max)" if pinned else ""),
                severity="high",
                tier=tier,
                evidence=f"{f}:{ln}",
                recommendation="Add a target-tracking scaling policy and let min < max so "
                               "capacity follows demand instead of running peak-sized 24/7 "
                               "(large E win).",
                slo_risk="Configure min capacity and scale-out cooldowns to protect "
                         "availability during spikes.",
                ghg_scope="GHG Protocol Scope 3 Category 1.",
            ))

        # Oversized / previous-gen instance hints.
        for m in re.finditer(r'instance_type\s*=\s*"([a-z0-9.]+)"', txt):
            itype = m.group(1)
            if re.search(r"\.(8|12|16|24)xlarge$", itype):
                findings.append(Finding(
                    pillar="cloud_infra",
                    id="CLOUD-LARGE-INSTANCE",
                    title=f"Very large instance type declared ({itype})",
                    severity="medium",
                    tier=tier,
                    evidence=f,
                    recommendation="Confirm the workload needs this size; right-size from "
                                   "observed utilization, and prefer current-gen (e.g. "
                                   "Graviton/ARM) for better performance-per-watt.",
                    ghg_scope="GHG Protocol Scope 3 Category 1.",
                ))

    for f in k8s:
        txt = ctx.read(f)
        if "kind: HorizontalPodAutoscaler" not in txt and "kind: Deployment" in txt:
            findings.append(Finding(
                pillar="cloud_infra",
                id="CLOUD-NO-HPA",
                title="Deployment without a HorizontalPodAutoscaler",
                severity="low",
                tier=1,
                evidence=f,
                recommendation="Add an HPA so replica count tracks load rather than sitting "
                               "at a fixed count around the clock.",
                slo_risk="Set sensible min replicas and stabilization windows to avoid "
                         "flapping under bursty load.",
            ))
    return findings, notes
