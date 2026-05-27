"""
Programmatic usage of sci_for_ai.

Run:
    python examples/compare_example.py
"""

from __future__ import annotations

from sci_for_ai import (BASELINE, OPTIMIZED, build_provider,
                        compare_prompt_sets)
from sci_for_ai.report import format_comparison


def main() -> None:
    # No API keys required — uses the deterministic mock provider.
    # Swap "mock" for "anthropic", "gemini", or "openai" for live calls.
    provider = build_provider("mock", region="europe-north1")  # low-carbon region

    query = "How can I reduce the carbon footprint of a real-time recommendation API?"

    result = compare_prompt_sets(provider, BASELINE, OPTIMIZED, query)
    print(format_comparison(result))

    # The full structured data is on `result`:
    #   result.baseline.totals, result.optimized.totals, result.delta
    # Use `result.to_dict()` for JSON serialisation.
    print()
    print("Saved tokens (input):", result.delta["input_tokens"]["reduction_pct"], "%")
    print("Saved emissions:", result.delta["total_emissions_kg"]["reduction_pct"], "%")


if __name__ == "__main__":
    main()
