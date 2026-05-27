"""Tests for the MockProvider — the network-free reference implementation."""

from __future__ import annotations

from sci_for_ai import MockProvider, build_provider
from sci_for_ai.providers import GenerationResult, LLMProvider


def test_mock_provider_satisfies_protocol():
    provider = MockProvider()
    assert isinstance(provider, LLMProvider)


def test_mock_generate_returns_result():
    provider = MockProvider()
    result = provider.generate("hello world")
    assert isinstance(result, GenerationResult)
    assert result.text  # non-empty
    assert result.measurement.input_tokens > 0
    assert result.measurement.output_tokens > 0


def test_mock_count_tokens_nonzero():
    provider = MockProvider()
    assert provider.count_tokens("hello world") >= 1


def test_mock_provider_is_deterministic():
    provider = MockProvider()
    r1 = provider.generate("the same prompt")
    r2 = provider.generate("the same prompt")
    assert r1.text == r2.text
    assert r1.measurement.input_tokens == r2.measurement.input_tokens


def test_build_provider_factory_mock():
    p = build_provider("mock")
    assert isinstance(p, MockProvider)


def test_build_provider_unknown_raises():
    import pytest
    with pytest.raises(ValueError):
        build_provider("not-a-real-provider")


def test_phase_propagates_to_measurement():
    provider = MockProvider()
    result = provider.generate("hi", phase="custom-phase")
    assert result.measurement.phase == "custom-phase"


def test_region_propagates_to_measurement():
    provider = MockProvider(region="europe-north1")
    result = provider.generate("hi")
    assert result.measurement.region == "europe-north1"
    # Finland's carbon intensity should be the one applied
    from sci_for_ai.sci import DEFAULT_CARBON_INTENSITY
    assert result.measurement.carbon_intensity == DEFAULT_CARBON_INTENSITY["europe-north1"]


# ----------------------------------------------------------------------
# Mock conciseness behaviour
# ----------------------------------------------------------------------
class TestMockConcisenessResponsiveness:
    """
    The mock's output length must respond to 'be concise' hints in the
    prompt; otherwise the baseline-vs-optimized comparison doesn't
    exercise the same code paths a real LLM would (input shrinks but
    output doesn't, so per-token SCI moves for the wrong reason).
    """

    def _ratio(self, prompt: str) -> float:
        p = MockProvider()
        r = p.generate(prompt)
        return r.measurement.output_tokens / max(1, r.measurement.input_tokens)

    def test_conciseness_hint_shrinks_output_vs_no_hint(self):
        # Same prompt length, one with hints, one without.
        # Pad both to identical length so input_tokens are equal.
        verbose_pad = " context " * 50
        no_hint = "Write a report on energy efficient computing." + verbose_pad
        with_hint = ("Write a report on energy efficient computing. "
                     "Be concise, bullets only, no preamble.") + verbose_pad
        # Make them exactly the same length so we isolate the effect.
        target_len = max(len(no_hint), len(with_hint))
        no_hint = no_hint.ljust(target_len)
        with_hint = with_hint.ljust(target_len)

        verbose_ratio = self._ratio(no_hint)
        terse_ratio = self._ratio(with_hint)
        assert terse_ratio < verbose_ratio

    def test_multiple_hints_shrink_more(self):
        # Two hints should produce a shorter output than one.
        one_hint = "Generate analysis. Be concise. " + ("x" * 200)
        two_hints = "Generate analysis. Be concise, bullets only. " + ("x" * 200)
        # Same length to isolate effect
        target = max(len(one_hint), len(two_hints))
        out_one = self._ratio(one_hint.ljust(target))
        out_two = self._ratio(two_hints.ljust(target))
        assert out_two <= out_one


# ----------------------------------------------------------------------
# Energy source labelling
# ----------------------------------------------------------------------
def test_mock_energy_source_is_estimated():
    """Mock never has EcoLogits available — label should reflect that."""
    p = MockProvider()
    r = p.generate("test")
    assert r.energy_source == "estimated"


def test_ecologits_init_helper_returns_false_without_package():
    """_try_init_ecologits should return False (not raise) when ecologits absent."""
    from sci_for_ai.providers import _try_init_ecologits
    # The package may or may not be installed in CI; we just check it doesn't raise.
    result = _try_init_ecologits("anthropic")
    assert isinstance(result, bool)
