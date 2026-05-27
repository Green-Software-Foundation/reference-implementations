"""
LLM pricing per million tokens.

This is a small data table updated periodically. All figures USD per
million tokens, separated for input and output because providers
typically charge a higher rate per output token than per input token,
often by a factor of 3–6×.

Why this lives in code rather than a config file: pricing changes
occasionally but not constantly. Keeping it in source with citations
means every change is reviewed and dated. For production use, check
the provider's official pricing page; the values here are intended
for the comparative-analysis demo.

Last verified: see `_PRICING_LAST_VERIFIED` constant below.
"""

from __future__ import annotations

from dataclasses import dataclass


_PRICING_LAST_VERIFIED = "2026-05"


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Per-million-token pricing for one model."""
    model_id: str
    usd_per_million_input: float
    usd_per_million_output: float
    source: str        # citation note
    last_verified: str = _PRICING_LAST_VERIFIED

    def cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        """Total USD cost for one call with these token counts."""
        return (
            input_tokens * self.usd_per_million_input / 1_000_000
            + output_tokens * self.usd_per_million_output / 1_000_000
        )


# Current published pricing. See README for sources.
_PRICING: dict[str, ModelPricing] = {
    # ----- OpenAI: latest flagship family (GPT-5.5, April 2026) -----
    # GPT-5.5 is too new for EcoLogits 0.10.1's profile table — energy will
    # fall back to our model-card estimate and be labeled "estimated" in
    # the report. Cost calculation is unaffected (uses this table).
    "gpt-5.5": ModelPricing(
        model_id="gpt-5.5",
        usd_per_million_input=5.00,
        usd_per_million_output=30.00,
        source="openai.com/api/pricing (verified May 2026) — flagship, released April 2026",
    ),
    "gpt-5.5-pro": ModelPricing(
        model_id="gpt-5.5-pro",
        usd_per_million_input=30.00,
        usd_per_million_output=180.00,
        source="openai.com/api/pricing (verified May 2026) — highest-precision variant",
    ),
    # ----- OpenAI: GPT-5.4 family (March 2026) -----
    # GPT-5.4 IS in EcoLogits 0.10.1 — energy will be measured.
    "gpt-5.4": ModelPricing(
        model_id="gpt-5.4",
        usd_per_million_input=2.50,
        usd_per_million_output=15.00,
        source="openai.com/api/pricing (verified May 2026) — prior flagship, still active",
    ),
    "gpt-5.4-mini": ModelPricing(
        model_id="gpt-5.4-mini",
        usd_per_million_input=0.75,
        usd_per_million_output=4.50,
        source="openai.com/api/pricing (verified May 2026) — best price/perf for production",
    ),
    "gpt-5.4-nano": ModelPricing(
        model_id="gpt-5.4-nano",
        usd_per_million_input=0.20,
        usd_per_million_output=1.25,
        source="openai.com/api/pricing (verified May 2026) — budget tier",
    ),
    "gpt-5.4-pro": ModelPricing(
        model_id="gpt-5.4-pro",
        usd_per_million_input=30.00,
        usd_per_million_output=180.00,
        source="openai.com/api/pricing (verified May 2026)",
    ),
    # ----- OpenAI: prior generations (kept for comparison / legacy use) -----
    "gpt-4o-mini": ModelPricing(
        model_id="gpt-4o-mini",
        usd_per_million_input=0.15,
        usd_per_million_output=0.60,
        source="openai.com/api/pricing (verified May 2026)",
    ),
    "gpt-4o": ModelPricing(
        model_id="gpt-4o",
        usd_per_million_input=2.50,
        usd_per_million_output=10.00,
        source="openai.com/api/pricing (verified May 2026)",
    ),
    "gpt-4.1": ModelPricing(
        model_id="gpt-4.1",
        usd_per_million_input=2.00,
        usd_per_million_output=8.00,
        source="openai.com/api/pricing (verified May 2026)",
    ),
    "gpt-4.1-mini": ModelPricing(
        model_id="gpt-4.1-mini",
        usd_per_million_input=0.40,
        usd_per_million_output=1.60,
        source="openai.com/api/pricing (verified May 2026)",
    ),
    "gpt-4.1-nano": ModelPricing(
        model_id="gpt-4.1-nano",
        usd_per_million_input=0.10,
        usd_per_million_output=0.40,
        source="openai.com/api/pricing (verified May 2026)",
    ),
    # Anthropic — list pricing as of May 2026
    "claude-haiku-4-5": ModelPricing(
        model_id="claude-haiku-4-5",
        usd_per_million_input=1.00,
        usd_per_million_output=5.00,
        source="anthropic.com/pricing (verified May 2026)",
    ),
    "claude-sonnet-4-6": ModelPricing(
        model_id="claude-sonnet-4-6",
        usd_per_million_input=3.00,
        usd_per_million_output=15.00,
        source="anthropic.com/pricing (verified May 2026)",
    ),
    "claude-opus-4-6": ModelPricing(
        model_id="claude-opus-4-6",
        usd_per_million_input=5.00,
        usd_per_million_output=25.00,
        source="anthropic.com/pricing (verified May 2026) — prior flagship, EcoLogits-profiled",
    ),
    "claude-opus-4-7": ModelPricing(
        model_id="claude-opus-4-7",
        usd_per_million_input=5.00,
        usd_per_million_output=25.00,
        source="anthropic.com/pricing (verified May 2026) — current flagship, released Apr 2026",
    ),
    # Google — list pricing as of May 2026.
    # Standard (interactive) pricing. Note Pro models use context-tiered
    # pricing: rates roughly double for prompts >200K tokens. Values here
    # are for the standard <=200K context tier.
    "gemini-2.0-flash": ModelPricing(
        model_id="gemini-2.0-flash",
        usd_per_million_input=0.10,
        usd_per_million_output=0.40,
        source="ai.google.dev/pricing (verified May 2026) — deprecated, shutdown June 2026",
    ),
    "gemini-2.5-flash-lite": ModelPricing(
        model_id="gemini-2.5-flash-lite",
        usd_per_million_input=0.10,
        usd_per_million_output=0.40,
        source="ai.google.dev/pricing (verified May 2026) — lowest-cost text route",
    ),
    "gemini-2.5-flash": ModelPricing(
        model_id="gemini-2.5-flash",
        usd_per_million_input=0.30,
        usd_per_million_output=2.50,
        source="ai.google.dev/pricing (verified May 2026) — standard interactive",
    ),
    "gemini-2.5-pro": ModelPricing(
        model_id="gemini-2.5-pro",
        usd_per_million_input=1.25,
        usd_per_million_output=10.00,
        source="ai.google.dev/pricing (verified May 2026) — <=200K context tier",
    ),
    "gemini-3-flash-preview": ModelPricing(
        model_id="gemini-3-flash-preview",
        usd_per_million_input=0.50,
        usd_per_million_output=3.00,
        source="ai.google.dev/pricing (verified May 2026)",
    ),
    "gemini-3.1-pro-preview": ModelPricing(
        model_id="gemini-3.1-pro-preview",
        usd_per_million_input=2.00,
        usd_per_million_output=12.00,
        source="ai.google.dev/pricing (verified May 2026) — newest flagship, <=200K context",
    ),
}

# Default for unknown models — uses a median of the mid-tier prices
# as a placeholder. For accurate reporting, add the actual model to
# the _PRICING table above with its real rates.
_FALLBACK_PRICING = ModelPricing(
    model_id="unknown",
    usd_per_million_input=1.00,
    usd_per_million_output=4.00,
    source=f"Fallback (no model-specific pricing); update _PRICING in pricing.py",
    last_verified="fallback",
)


def register_model_pricing(pricing: ModelPricing) -> None:
    """Register custom pricing — useful for fine-tuned, internal, or newly released models."""
    _PRICING[pricing.model_id] = pricing


def pricing_for(model_id: str) -> ModelPricing:
    """Return pricing for `model_id`, falling back if unknown."""
    return _PRICING.get(model_id, _FALLBACK_PRICING)


def estimate_cost_usd(model_id: str, input_tokens: int, output_tokens: int) -> tuple[float, str]:
    """
    Estimate USD cost. Returns (cost, source_note) so callers can log
    the pricing source alongside the value for traceability.
    """
    p = pricing_for(model_id)
    return p.cost_usd(input_tokens, output_tokens), p.source
