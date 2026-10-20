"""Pillar detectors. Each module exposes `detect(ctx) -> (findings, notes)`."""
from . import code_efficiency, containerization, cicd, cloud_infra, sre_ops

REGISTRY = {
    "code_efficiency": code_efficiency,
    "containerization": containerization,
    "cicd": cicd,
    "cloud_infra": cloud_infra,
    "sre_ops": sre_ops,
}
