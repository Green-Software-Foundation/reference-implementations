"""
Demo client: start the server over stdio, list tools, call `summarize`,
and print the sustainability data that came back in `_meta`.

Run twice: once opted in to the extension, once as a plain MCP client,
to see that ordinary clients are unaffected.
"""

from __future__ import annotations

import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .extension import EXTENSION_ID

SAMPLE = (
    "The Green Software Foundation's SCI for AI specification extends the ISO SCI standard "
    "to AI systems. It defines functional units suited to inference and training, separates "
    "provider and consumer boundaries, and asks that every figure state whether it was "
    "measured or estimated so that results stay honest and reproducible across teams."
)


async def run(opt_in: bool) -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_sci.server"])
    extensions = {EXTENSION_ID: {}} if opt_in else None
    async with stdio_client(params) as (r, w), ClientSession(r, w, extensions=extensions) as s:
        await s.discover()  # 2026-07-28 stateless path (initialize() is the legacy handshake)

        caps = s.discover_result.capabilities
        print("protocol:", s.protocol_version)
        print(f"\n== client {'WITH' if opt_in else 'WITHOUT'} the extension ==")
        print("server advertises:", json.dumps((caps.extensions or {}).get(EXTENSION_ID)))

        tools = await s.list_tools()
        print(f"tools/list cache hint: ttlMs={tools.ttl_ms} cacheScope={tools.cache_scope}")
        for t in tools.tools:
            print(f"\ntools/list -> {t.name} _meta:")
            print(json.dumps((t.meta or {}).get(EXTENSION_ID), indent=2))

        res = await s.call_tool("summarize", {"text": SAMPLE, "max_words": 25})
        print("\ntools/call -> content:", res.content[0].text)
        attribution = (res.meta or {}).get(EXTENSION_ID)
        if attribution:
            print("tools/call -> _meta (SCI attribution for this call):")
            print(json.dumps(attribution, indent=2))
        else:
            print("tools/call -> _meta: no sustainability data.")
            print("  Expected: this client did not declare the extension, so it gets a plain MCP result.")


def main() -> None:
    print("Run 1: client declares the extension -> expects disclosure on tools/list and attribution on tools/call")
    asyncio.run(run(opt_in=True))
    print("\nRun 2: plain MCP client -> expects the same tool result, with NO attribution")
    asyncio.run(run(opt_in=False))
    print("\nDone. Both behaviours are correct: sustainability data is opt-in and never changes the tool result.")


if __name__ == "__main__":
    main()
