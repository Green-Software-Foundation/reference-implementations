"""Pillar: CI/CD Practices (weight 0.15)."""
from __future__ import annotations

from ..model import Finding


def detect(ctx):
    findings: list[Finding] = []
    notes: list[str] = []

    workflows = [f for f in ctx.files if "/.github/workflows/" in "/" + f
                 and f.endswith((".yml", ".yaml"))]
    other_ci = ctx.basename_matches(".gitlab-ci.yml", "azure-pipelines.yml",
                                    "Jenkinsfile", ".circleci/config.yml")

    if not workflows and not other_ci:
        notes.append("No CI configuration found; pipeline checks not applicable "
                     "(scored neutral for this pillar).")
        return findings, notes

    for wf in workflows:
        txt = ctx.read(wf)
        low = txt.lower()

        if "cache" not in low:
            findings.append(Finding(
                pillar="cicd",
                id="CI-NO-CACHE",
                title="Workflow declares no dependency caching",
                severity="medium",
                tier=1,
                evidence=wf,
                recommendation="Cache dependencies (actions/cache or setup-*'s cache) so "
                               "every run does not re-download and rebuild from scratch (E).",
            ))

        if "on:" in low and ("push:" in low and "paths:" not in low and "paths-ignore:" not in low):
            findings.append(Finding(
                pillar="cicd",
                id="CI-NO-PATH-FILTER",
                title="Pipeline runs on every push with no path filter",
                severity="low",
                tier=1,
                evidence=wf,
                recommendation="Add path filters or concurrency cancellation so docs-only or "
                               "superseded commits do not trigger full builds.",
            ))

        if "concurrency" not in low:
            findings.append(Finding(
                pillar="cicd",
                id="CI-NO-CONCURRENCY",
                title="No concurrency control; superseded runs are not cancelled",
                severity="low",
                tier=1,
                evidence=wf,
                recommendation="Add a concurrency group with cancel-in-progress so an "
                               "outdated run stops when a newer commit lands.",
            ))

        if "cron:" in low:
            findings.append(Finding(
                pillar="cicd",
                id="CI-SCHEDULED-BUILD",
                title="Scheduled (cron) workflow runs regardless of changes",
                severity="info",
                tier=1,
                evidence=wf,
                recommendation="Confirm the schedule is needed; nightly builds on quiet "
                               "repos burn compute with no functional output.",
            ))
    return findings, notes
