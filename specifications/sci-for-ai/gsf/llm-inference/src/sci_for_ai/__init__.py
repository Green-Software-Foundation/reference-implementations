"""
SCI for AI — measure Software Carbon Intensity of LLM inference pipelines.

Public API:

    >>> from sci_for_ai import build_provider, BASELINE, OPTIMIZED, compare_prompt_sets
    >>> provider = build_provider("mock")
    >>> result = compare_prompt_sets(provider, BASELINE, OPTIMIZED, "your query here")
    >>> print(result.delta["sci"]["reduction_pct"])
"""

from .energy import (ModelEnergyProfile, estimate_kwh, profile_for,
                     register_model_energy)
from .pipeline import (ComparisonResult, PipelineError, PipelineResult,
                       compare_prompt_sets, run_pipeline)
from .pricing import (ModelPricing, estimate_cost_usd, pricing_for,
                      register_model_pricing)
from .prompts import BASELINE, OPTIMIZED, PROMPT_SETS, PromptSet
from .providers import (AnthropicProvider, GeminiProvider, GenerationResult,
                        LLMProvider, MockProvider, OpenAIProvider,
                        RecordedProvider, build_provider)
from .scale import project_comparison, project_to_scale
from .sci import (DEFAULT_CARBON_INTENSITY, DEFAULT_EMBODIED_FRACTION,
                  CallMeasurement, aggregate, carbon_intensity_for, compare,
                  estimate_embodied_kg, sci_score)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # SCI math
    "CallMeasurement",
    "DEFAULT_CARBON_INTENSITY",
    "DEFAULT_EMBODIED_FRACTION",
    "aggregate",
    "carbon_intensity_for",
    "compare",
    "estimate_embodied_kg",
    "sci_score",
    # Energy estimation
    "ModelEnergyProfile",
    "estimate_kwh",
    "profile_for",
    "register_model_energy",
    # Pricing
    "ModelPricing",
    "estimate_cost_usd",
    "pricing_for",
    "register_model_pricing",
    # Scale projection
    "project_comparison",
    "project_to_scale",
    # Providers
    "AnthropicProvider",
    "GeminiProvider",
    "GenerationResult",
    "LLMProvider",
    "MockProvider",
    "OpenAIProvider",
    "RecordedProvider",
    "build_provider",
    # Prompts
    "BASELINE",
    "OPTIMIZED",
    "PROMPT_SETS",
    "PromptSet",
    # Pipeline
    "ComparisonResult",
    "PipelineError",
    "PipelineResult",
    "compare_prompt_sets",
    "run_pipeline",
]
