"""
Tests for RecordedProvider — the record-and-replay path used to ship
real EcoLogits data as a fixture without requiring API keys at replay time.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sci_for_ai import (BASELINE, OPTIMIZED, MockProvider, RecordedProvider,
                        compare_prompt_sets, run_pipeline)
from sci_for_ai.providers import LLMProvider


@pytest.fixture
def fixture_path(tmp_path) -> Path:
    """Record a real (well, mock) comparison run and return the file path."""
    provider = MockProvider(model_id="claude-haiku-4-5", region="us-central1")
    result = compare_prompt_sets(provider, BASELINE, OPTIMIZED, "test query")
    path = tmp_path / "recorded.json"
    path.write_text(json.dumps(result.to_dict(), indent=2, default=str))
    return path


def test_recorded_provider_satisfies_protocol(fixture_path):
    provider = RecordedProvider(fixture_path=str(fixture_path))
    assert isinstance(provider, LLMProvider)


def test_recorded_replay_matches_original(fixture_path):
    """
    The replay should reproduce the recorded numbers exactly. Within
    floating-point precision, they should be identical to the original run.
    """
    # Read the original numbers from the fixture
    original = json.loads(fixture_path.read_text())
    original_optimized_sci = original["optimized"]["totals"]["sci"]
    original_optimized_emissions = original["optimized"]["totals"]["total_emissions_kg"]

    # Replay it
    provider = RecordedProvider(fixture_path=str(fixture_path))
    replayed = compare_prompt_sets(provider, BASELINE, OPTIMIZED, "replayed")

    assert replayed.optimized.totals["sci"] == pytest.approx(
        original_optimized_sci, rel=1e-12
    )
    assert replayed.optimized.totals["total_emissions_kg"] == pytest.approx(
        original_optimized_emissions, rel=1e-12
    )


def test_recorded_provider_preserves_energy_source(fixture_path):
    """
    Energy source label must come from the fixture, not default to 'measured'.
    Replaying a fixture recorded with mock (estimated) must report 'estimated'.
    """
    provider = RecordedProvider(fixture_path=str(fixture_path))
    result = compare_prompt_sets(provider, BASELINE, OPTIMIZED, "replayed")
    # The fixture was recorded with mock, so energy_source should be 'estimated'
    assert result.baseline.energy_source == "estimated"
    assert result.optimized.energy_source == "estimated"


def test_recorded_provider_exhaustion_raises(fixture_path, tmp_path):
    """
    Replaying more calls than were recorded should raise a clear error,
    not silently return wrong numbers.
    """
    provider = RecordedProvider(fixture_path=str(fixture_path))
    # Burn all 6 calls (3 baseline + 3 optimized)
    for _ in range(6):
        provider.generate("anything")
    # Seventh call should raise
    with pytest.raises(RuntimeError, match="exhausted"):
        provider.generate("one more")


def test_recorded_provider_rejects_bad_format(tmp_path):
    """A malformed fixture should produce a clear ValueError at load time."""
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps({"not": "a fixture"}))
    with pytest.raises(ValueError, match="Unrecognised fixture"):
        RecordedProvider(fixture_path=str(bad_path))


def test_recorded_provider_works_with_run_pipeline(tmp_path):
    """A fixture from `run_pipeline` (not compare) should replay too."""
    mock = MockProvider()
    result = run_pipeline(mock, BASELINE, "test")
    path = tmp_path / "pipeline.json"
    path.write_text(json.dumps(result.to_dict(), indent=2, default=str))

    provider = RecordedProvider(fixture_path=str(path))
    replayed = run_pipeline(provider, BASELINE, "replayed")
    assert replayed.totals["sci"] == pytest.approx(result.totals["sci"], rel=1e-12)


def test_build_provider_recorded(fixture_path):
    """The factory should accept 'recorded' with a fixture_path kwarg."""
    from sci_for_ai import build_provider
    provider = build_provider("recorded", fixture_path=str(fixture_path))
    assert isinstance(provider, RecordedProvider)
