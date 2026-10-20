"""Scoring configuration for the codebase sustainability score.

Grounded in the Green Software Foundation (GSF) Software Carbon Intensity (SCI)
specification. SCI is defined as:

    SCI = ((E * I) + M) / R

where
    E = energy consumed by the software (kWh)
    I = carbon intensity of the energy (gCO2e/kWh, location- or market-based)
    M = embodied emissions of the hardware the software runs on (gCO2e)
    R = the functional unit the score is expressed per (e.g. per request)

A purely static repository scan cannot *measure* E, I, M or R directly. What it
CAN do is assess the engineering practices and architectural choices that push
each of those SCI terms up or down, and report how confident it is given the
data it actually had access to. That honesty is encoded in the data-quality
tiers below.
"""

# --- The five weighted scoring pillars -------------------------------------
# Weights sum to 1.0. Sourced from the product master prompt.
PILLARS = {
    "code_efficiency": {
        "label": "Code / Algorithm Efficiency",
        "weight": 0.30,
        "sci_terms": ["E", "R"],
        "rationale": "Wasteful algorithms and hot-path inefficiency raise energy "
                     "per functional unit (E/R).",
    },
    "containerization": {
        "label": "Containerization",
        "weight": 0.15,
        "sci_terms": ["E", "M"],
        "rationale": "Bloated images and over-provisioned containers waste both "
                     "runtime energy and embodied hardware capacity (E, M).",
    },
    "cicd": {
        "label": "CI/CD Practices",
        "weight": 0.15,
        "sci_terms": ["E"],
        "rationale": "Redundant, uncached, always-on pipelines burn compute for "
                     "no functional gain (E).",
    },
    "cloud_infra": {
        "label": "Cloud Infrastructure Choices",
        "weight": 0.25,
        "sci_terms": ["E", "I", "M"],
        "rationale": "Region carbon intensity, right-sizing and autoscaling drive "
                     "the largest, most direct sustainability levers (E, I, M).",
    },
    "sre_ops": {
        "label": "SRE / Operations",
        "weight": 0.15,
        "sci_terms": ["E", "R"],
        "rationale": "Observability and capacity discipline let teams find and "
                     "cut waste without hurting reliability (E/R).",
    },
}

assert abs(sum(p["weight"] for p in PILLARS.values()) - 1.0) < 1e-9, "weights must sum to 1.0"

# --- Data-quality tiers -----------------------------------------------------
# Every finding is stamped with the highest tier its evidence supports. A
# static-only scan can never claim above Tier 1 on its own.
DATA_QUALITY_TIERS = {
    1: {
        "label": "Static analysis only",
        "confidence": "directional",
        "description": "Inferred from source, config and manifests. No runtime "
                       "or billing data. Findings indicate likely direction of "
                       "impact, not measured magnitude.",
    },
    2: {
        "label": "Static + declared infra",
        "confidence": "estimated",
        "description": "Static signals corroborated by declared infrastructure "
                       "(IaC, region, instance types). Rough magnitude possible.",
    },
    3: {
        "label": "Static + operational telemetry",
        "confidence": "measured-partial",
        "description": "Backed by observability/telemetry (utilization, request "
                       "rates). Real per-unit trends available.",
    },
    4: {
        "label": "Direct measurement",
        "confidence": "measured",
        "description": "Energy/carbon measured directly (e.g. power telemetry, "
                       "cloud carbon APIs). Full SCI can be computed.",
    },
}

# Severity -> how many points it deducts from a pillar's 100-point base.
SEVERITY_PENALTY = {
    "high": 20,
    "medium": 10,
    "low": 4,
    "info": 0,
}

# Letter grade bands for the composite 0-100 score.
GRADE_BANDS = [
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
    (0, "F"),
]
