"""
Demo MCP server: one tool, `summarize`, backed by a mock LLM (no API key).

The only sustainability-specific lines are marked  # <-- SCI.
Everything else is an ordinary MCP server built with the official SDK.
"""

from __future__ import annotations

from mcp.server.caching import CacheHint
from mcp.server.mcpserver import MCPServer

from .extension import Boundary, Disclosure, SustainabilityExtension, Usage, record  # <-- SCI

REGION = "europe-north1"

# What the `summarize` tool discloses about its footprint.               # <-- SCI
SUMMARIZE_DISCLOSURE = Disclosure(
    functional_unit="request",
    functional_unit_description="One summarization request, whatever its length.",
    boundary=Boundary(
        persona="consumer",
        phase="inference",
        description=(
            "Inference on the hosted model endpoint: GPU/host energy for the call and "
            "an allocated share of hardware embodied emissions. Excludes model training, "
            "network transit, the MCP transport itself, and the calling agent."
        ),
        includes=("compute", "embodied-hardware"),
        excludes=("training", "network-transit", "mcp-transport", "calling-agent"),
    ),
    region=REGION,
)

mcp = MCPServer(
    "sci-demo",
    extensions=[SustainabilityExtension({"summarize": SUMMARIZE_DISCLOSURE})],  # <-- SCI
    # The disclosure on tools/list is static, so let clients cache it for an hour.
    # Keep this shorter than the disclosure's validity period.             # <-- SCI
    cache_hints={"tools/list": CacheHint(ttl_ms=3_600_000, scope="public")},
)


def _mock_llm(text: str, max_words: int) -> tuple[str, int, int]:
    """Deterministic stand-in for a model call. Returns (summary, in_tokens, out_tokens)."""
    words = text.split()
    summary = " ".join(words[:max_words]) + (" ..." if len(words) > max_words else "")
    tok = lambda s: int(len(s.split()) * 1.3) + 1  # crude token estimate
    return summary, tok(text), tok(summary)


@mcp.tool(
    description="Summarize a piece of text.",
    meta={  # static disclosure, shown on tools/list                    # <-- SCI
        "foundation.greensoftware/sustainability": SUMMARIZE_DISCLOSURE.to_meta(
            typical_input_tokens=400, typical_output_tokens=60
        )
    },
)
def summarize(text: str, max_words: int = 40) -> str:
    summary, in_tok, out_tok = _mock_llm(text, max_words)
    record(Usage(input_tokens=in_tok, output_tokens=out_tok, functional_units=1))  # <-- SCI
    return summary


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
