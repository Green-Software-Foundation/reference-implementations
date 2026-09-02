"""
The MCP side: a pluggable Extension that carries SCI for AI figures in `_meta`.

Two places in the protocol are used, nothing else:

  tools/list   ->  each tool's `_meta` carries a *disclosure*: what standard,
                   what functional unit, what boundary, and a typical figure.
                   This is static and cacheable.

  tools/call   ->  the result's `_meta` carries an *attribution*: the energy,
                   carbon, embodied and SCI figures for that specific call.
                   Only sent when the client declared the extension.

The extension identifier follows the MCP reverse-DNS rule:
    foundation.greensoftware/sustainability

Uses the official MCP Python SDK's `Extension` base class (SEP-2133), so the
whole thing plugs into `MCPServer(extensions=[...])` with no changes to tools.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Any

from mcp.server.extension import Extension
from mcp.types import CallToolResult

from .sci import EnergyProfile, MOCK_PROFILE, carbon_intensity_for, compute_sci

EXTENSION_ID = "foundation.greensoftware/sustainability"
EXTENSION_VERSION = "0.1.0-experimental"


# ---------------------------------------------------------------------------
# What a tool declares about itself (static, goes on tools/list)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Boundary:
    persona: str            # "provider" or "consumer" (SCI for AI)
    phase: str              # "inference", "training", "fine-tuning", ...
    description: str
    includes: tuple[str, ...]
    excludes: tuple[str, ...]


@dataclass(frozen=True)
class Disclosure:
    functional_unit: str
    functional_unit_description: str
    boundary: Boundary
    region: str
    profile: EnergyProfile = MOCK_PROFILE

    def to_meta(self, typical_input_tokens: int, typical_output_tokens: int) -> dict[str, Any]:
        """Build the `_meta` block for tools/list. Includes a typical per-unit
        figure so a client can reason about the tool before calling it."""
        typical = _attribution(self, typical_input_tokens, typical_output_tokens, functional_units=1)
        return {
            "version": EXTENSION_VERSION,
            "methodology": _METHODOLOGY,
            "functionalUnit": {
                "name": self.functional_unit,
                "description": self.functional_unit_description,
            },
            "boundary": {
                "persona": self.boundary.persona,
                "phase": self.boundary.phase,
                "description": self.boundary.description,
                "includes": list(self.boundary.includes),
                "excludes": list(self.boundary.excludes),
            },
            "typical": {
                "sci": typical["sci"],
                "energy": typical["energy"],
                "basis": "estimated",
                "note": f"Typical request of {typical_input_tokens} input and {typical_output_tokens} output tokens.",
            },
        }


_METHODOLOGY = {
    "id": "SCI-for-AI",
    "base": "SCI (ISO/IEC 21031:2024)",
    "uri": "https://sci-for-ai.greensoftware.foundation/",
}


# ---------------------------------------------------------------------------
# What a tool reports per call (dynamic, goes on the tools/call result)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Usage:
    """What the tool observed while doing the work."""

    input_tokens: int
    output_tokens: int
    functional_units: float = 1
    energy_kwh: float | None = None    # set this if you have a *measured* figure
    embodied_kg: float | None = None   # set this if the provider reports embodied


# A mutable holder is used rather than setting the contextvar directly, because
# sync tools run in a worker thread with a *copy* of the context: a value set
# there would not be visible to the interceptor. A shared dict is.
_holder: contextvars.ContextVar[dict[str, Usage] | None] = contextvars.ContextVar("mcp_sci_usage", default=None)


def record(usage: Usage) -> None:
    """Called by a tool during execution to hand its usage to the extension."""
    holder = _holder.get()
    if holder is not None:
        holder["usage"] = usage


def _attribution(d: Disclosure, input_tokens: int, output_tokens: int, functional_units: float,
                 energy_kwh: float | None = None, embodied_kg: float | None = None) -> dict[str, Any]:
    """Turn observed usage into the `_meta` attribution block."""
    measured = energy_kwh is not None
    e = energy_kwh if measured else d.profile.energy_kwh(input_tokens, output_tokens)
    i = carbon_intensity_for(d.region)
    r = compute_sci(e, i, functional_units, embodied_kg)
    g = 1000.0  # kg -> g for readability
    return {
        "energy": {"value": round(e, 12), "unit": "kWh", "basis": "measured" if measured else "estimated"},
        "carbonIntensity": {"value": i, "unit": "kgCO2e/kWh", "region": d.region, "basis": "location-based"},
        "emissions": {
            "operational": round(r.operational_kg * g, 9),
            "embodied": round(r.embodied_kg * g, 9),
            "total": round(r.total_kg * g, 9),
            "unit": "gCO2e",
            "embodiedBasis": "provider-reported" if embodied_kg is not None else "estimated (12% of operational)",
        },
        "sci": {
            "value": None if r.sci_kg_per_unit is None else round(r.sci_kg_per_unit * g, 9),
            "unit": f"gCO2e/{d.functional_unit}",
        },
    }


# ---------------------------------------------------------------------------
# The extension itself
# ---------------------------------------------------------------------------
class SustainabilityExtension(Extension):
    identifier = EXTENSION_ID

    def __init__(self, disclosures: dict[str, Disclosure]):
        # tool name -> what that tool discloses
        self._disclosures = disclosures

    def settings(self) -> dict[str, Any]:
        """Advertised under capabilities.extensions[identifier] in server/discover."""
        return {
            "version": EXTENSION_VERSION,
            "methodology": _METHODOLOGY["id"],
            "publisher": {"name": "Example Service Provider"},
        }

    async def intercept_tool_call(self, params, ctx, call_next):
        """Run the tool, then attach the attribution to the result's `_meta`."""
        holder: dict[str, Usage] = {}
        token = _holder.set(holder)
        try:
            result = await call_next(ctx)
        finally:
            _holder.reset(token)
        usage = holder.get("usage")

        if not isinstance(result, CallToolResult):
            return result                       # e.g. an input_required interim result
        if not _client_opted_in(ctx):
            return result                       # plain MCP client: unchanged result
        d = self._disclosures.get(params.name)
        if d is None or usage is None:
            return result                       # tool has no disclosure, or reported nothing

        attribution = {
            "version": EXTENSION_VERSION,
            "methodology": _METHODOLOGY["id"],
            "functionalUnit": {"name": d.functional_unit, "quantity": usage.functional_units},
            "boundary": {"persona": d.boundary.persona, "phase": d.boundary.phase},
            **_attribution(d, usage.input_tokens, usage.output_tokens, usage.functional_units,
                           usage.energy_kwh, usage.embodied_kg),
            "details": {
                "model": d.profile.model,
                "inputTokens": usage.input_tokens,
                "outputTokens": usage.output_tokens,
                "outcome": "failed" if result.is_error else "completed",
                "energySource": d.profile.source if usage.energy_kwh is None else "instrumentation",
            },
        }
        meta = dict(result.meta or {})
        meta[EXTENSION_ID] = attribution
        result.meta = meta
        return result


def _client_opted_in(ctx) -> bool:
    caps = getattr(ctx.session, "client_capabilities", None)
    exts = getattr(caps, "extensions", None) or {}
    return EXTENSION_ID in exts
