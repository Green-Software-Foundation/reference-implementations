"""Pipeline integration tests — use the MockProvider, no network."""

from __future__ import annotations

import pytest

from sci_for_ai import (BASELINE, OPTIMIZED, MockProvider, compare_prompt_sets,
                        run_pipeline)
from sci_for_ai.pipeline import PipelineError


@pytest.fixture
def provider():
    return MockProvider(model_id="claude-haiku-4-5", region="us-central1")


class TestRunPipeline:
    def test_basic_run(self, provider):
        result = run_pipeline(provider, BASELINE, "How do I reduce energy use in Python?")
        assert result.plan
        assert result.insights
        assert result.report
        assert len(result.measurements) == 3
        assert result.totals["sci"] is not None
        assert result.totals["total_tokens"] > 0

    def test_phase_names_are_set(self, provider):
        result = run_pipeline(provider, BASELINE, "test query")
        phases = [m.phase for m in result.measurements]
        assert any("planning" in p for p in phases)
        assert any("collection" in p for p in phases)
        assert any("writing" in p for p in phases)

    def test_empty_query_raises(self, provider):
        with pytest.raises(ValueError):
            run_pipeline(provider, BASELINE, "")

    def test_whitespace_query_raises(self, provider):
        with pytest.raises(ValueError):
            run_pipeline(provider, BASELINE, "   ")

    def test_to_dict_serializable(self, provider):
        import json
        result = run_pipeline(provider, BASELINE, "test query")
        # Default=str for any objects that don't serialise natively
        s = json.dumps(result.to_dict(), default=str)
        assert "plan" in s
        assert "totals" in s


class TestCompare:
    def test_compare_returns_both_runs(self, provider):
        result = compare_prompt_sets(
            provider, BASELINE, OPTIMIZED, "Reduce energy use in image processing"
        )
        assert result.baseline.prompt_set_name == "baseline"
        assert result.optimized.prompt_set_name == "optimized"
        assert result.delta is not None

    def test_optimized_uses_fewer_input_tokens(self, provider):
        # The optimized prompts are objectively shorter, so the mock token
        # count (chars / 4) should be lower for them.
        result = compare_prompt_sets(
            provider, BASELINE, OPTIMIZED, "Reduce energy use in image processing"
        )
        assert result.optimized.totals["input_tokens"] < result.baseline.totals["input_tokens"]
        assert result.delta["input_tokens"]["reduction_pct"] > 0

    def test_optimized_also_reduces_output_tokens(self, provider):
        """
        The realistic pattern: optimized prompts contain conciseness
        instructions which shrink output too. If output didn't shrink, the
        per-token SCI math would mislead — see the comments in MockProvider.
        """
        result = compare_prompt_sets(
            provider, BASELINE, OPTIMIZED, "Reduce energy use in image processing"
        )
        assert result.optimized.totals["output_tokens"] < result.baseline.totals["output_tokens"]
        assert result.delta["output_tokens"]["reduction_pct"] > 0

    def test_optimized_reduces_total_emissions(self, provider):
        """The whole point: optimization should cut absolute emissions."""
        result = compare_prompt_sets(
            provider, BASELINE, OPTIMIZED, "test query"
        )
        assert result.optimized.totals["total_emissions_kg"] < result.baseline.totals["total_emissions_kg"]
        assert result.delta["total_emissions_kg"]["reduction_pct"] > 0

    def test_optimized_lowers_sci_per_token(self, provider):
        """
        Optimized prompts should also lower per-token SCI, not just absolute
        emissions. This holds when conciseness instructions cap output near
        an absolute size (rather than scaling with input), shifting the
        input/output mix toward lower-weight input tokens.

        If this test fails, the mock's output-sizing model has reverted to
        a proportional shrink, which would give users an inaccurate picture
        of how conciseness instructions affect SCI on real LLMs.
        """
        result = compare_prompt_sets(
            provider, BASELINE, OPTIMIZED, "Reduce energy use in image processing"
        )
        baseline_sci = result.baseline.totals["sci"]
        optimized_sci = result.optimized.totals["sci"]
        assert optimized_sci < baseline_sci, (
            f"Expected SCI/token to drop with optimized prompts. "
            f"Got baseline={baseline_sci:.3e}, optimized={optimized_sci:.3e}."
        )

    def test_optimized_shifts_input_output_ratio(self, provider):
        """
        Verify the mechanism behind SCI reduction: optimized prompts should
        have a *lower* output-to-input ratio than baseline. That shift toward
        lower-weight input tokens is what drives the per-token intensity down.
        """
        result = compare_prompt_sets(
            provider, BASELINE, OPTIMIZED, "Reduce energy use in image processing"
        )
        baseline_ratio = (result.baseline.totals["output_tokens"]
                          / result.baseline.totals["input_tokens"])
        optimized_ratio = (result.optimized.totals["output_tokens"]
                           / result.optimized.totals["input_tokens"])
        assert optimized_ratio < baseline_ratio, (
            f"Expected optimized output/input ratio to be lower. "
            f"Got baseline={baseline_ratio:.2f}, optimized={optimized_ratio:.2f}."
        )

    def test_delta_has_all_metrics(self, provider):
        result = compare_prompt_sets(provider, BASELINE, OPTIMIZED, "test")
        for key in ("input_tokens", "output_tokens", "total_tokens",
                    "energy_kwh", "total_emissions_kg", "sci"):
            assert key in result.delta
            assert "baseline" in result.delta[key]
            assert "optimized" in result.delta[key]
            assert "reduction_pct" in result.delta[key]


class TestPipelineError:
    def test_empty_response_raises(self, provider, monkeypatch):
        # Patch the provider so its `generate` returns empty text once.
        original = provider.generate
        call_count = {"n": 0}

        def fake_generate(prompt, *, phase="generate", max_output_tokens=1024):
            r = original(prompt, phase=phase, max_output_tokens=max_output_tokens)
            call_count["n"] += 1
            if call_count["n"] == 1:
                # Replace with empty-text result
                from sci_for_ai.providers import GenerationResult
                return GenerationResult(text="", measurement=r.measurement)
            return r

        monkeypatch.setattr(provider, "generate", fake_generate)
        with pytest.raises(PipelineError):
            run_pipeline(provider, BASELINE, "test")
