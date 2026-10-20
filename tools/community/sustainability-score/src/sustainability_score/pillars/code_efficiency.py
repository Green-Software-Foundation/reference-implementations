"""Pillar: Code / Algorithm Efficiency (weight 0.30).

Static heuristics that flag likely energy-per-request waste. Deliberately
conservative: every finding is Tier 1 (directional) because a static scan
cannot observe how hot a path actually is at runtime.
"""
from __future__ import annotations

import ast
import re

from ..model import Finding

PY = (".py",)


def _py_findings(ctx) -> list[Finding]:
    out: list[Finding] = []
    for f in ctx.glob(*PY):
        src = ctx.read(f)
        if not src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            # Nested loops -> potential quadratic hot path.
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if child is node:
                        continue
                    if isinstance(child, (ast.For, ast.While)):
                        out.append(Finding(
                            pillar="code_efficiency",
                            id="CE-NESTED-LOOP",
                            title="Nested loop may indicate super-linear work on a hot path",
                            severity="low",
                            tier=1,
                            evidence=f"{f}:{node.lineno}",
                            recommendation="Confirm the collection sizes; if they grow with "
                                           "load, consider a set/dict lookup or precomputed "
                                           "index to cut CPU time (lowers E).",
                        ))
                        break

            # Blocking sleep in library/app code -> idle CPU holding resources.
            if isinstance(node, ast.Call):
                fn = node.func
                name = getattr(fn, "attr", getattr(fn, "id", ""))
                if name == "sleep":
                    out.append(Finding(
                        pillar="code_efficiency",
                        id="CE-BLOCKING-SLEEP",
                        title="Blocking sleep() holds a worker/thread idle",
                        severity="low",
                        tier=1,
                        evidence=f"{f}:{node.lineno}",
                        recommendation="Prefer event-driven waits or async scheduling so the "
                                       "worker can be reclaimed while idle.",
                        slo_risk="None if replaced with an equivalent async wait; verify "
                                 "retry/backoff semantics are preserved.",
                    ))

        # String concatenation in a loop (classic allocator churn).
        for m in re.finditer(r"for\s+.+:\s*(?:\n\s+.*)*?\n\s+\w+\s*\+=\s*['\"]", src):
            line = src[:m.start()].count("\n") + 1
            out.append(Finding(
                pillar="code_efficiency",
                id="CE-STR-CONCAT-LOOP",
                title="String built by repeated concatenation in a loop",
                severity="low",
                tier=1,
                evidence=f"{f}:{line}",
                recommendation="Accumulate into a list and ''.join() once to avoid O(n^2) "
                               "allocation churn.",
            ))
            break  # one per file is enough signal
    return out


def _generic_findings(ctx) -> list[Finding]:
    out: list[Finding] = []
    # SELECT * and missing pagination hints across any language.
    for f in ctx.glob(".py", ".js", ".ts", ".go", ".java", ".rb", ".sql"):
        for ln in ctx.find_lines(f, "SELECT *"):
            out.append(Finding(
                pillar="code_efficiency",
                id="CE-SELECT-STAR",
                title="SELECT * pulls unused columns over the wire",
                severity="medium",
                tier=1,
                evidence=f"{f}:{ln}",
                recommendation="Select only needed columns; reduces I/O, network and "
                               "serialization energy per query.",
            ))
    return out


def detect(ctx):
    findings = _py_findings(ctx) + _generic_findings(ctx)
    notes = []
    if not ctx.glob(*PY):
        notes.append("No Python sources found; deep AST checks skipped. "
                     "Language-agnostic checks still ran.")
    return findings, notes
