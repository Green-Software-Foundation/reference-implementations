import os

from sustainability_score import scan

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_service")


def _ids(result):
    return {f.id for p in result.pillars for f in p.findings}


def test_scan_produces_composite_and_grade():
    r = scan(FIXTURE)
    assert 0 <= r.composite_score <= 100
    assert r.grade in {"A", "B", "C", "D", "F"}
    assert r.meta["method"] == "static-analysis-only"


def test_expected_findings_fire():
    ids = _ids(scan(FIXTURE))
    for expected in {
        "CE-NESTED-LOOP", "CE-SELECT-STAR", "CE-BLOCKING-SLEEP",
        "CN-HEAVY-BASE", "CN-NO-RESOURCE-LIMITS",
        "CI-NO-CACHE",
        "CLOUD-HIGH-CARBON-REGION", "CLOUD-FIXED-CAPACITY", "CLOUD-LARGE-INSTANCE",
        "SRE-NO-OBSERVABILITY",
    }:
        assert expected in ids, f"missing {expected}"


def test_weights_sum_to_one():
    r = scan(FIXTURE)
    assert abs(sum(p.weight for p in r.pillars) - 1.0) < 1e-9


def test_every_finding_declares_a_tier():
    r = scan(FIXTURE)
    for p in r.pillars:
        for f in p.findings:
            assert f.tier in (1, 2, 3, 4)
