# SCI for AI over MCP

A reference implementation showing **one simple way to carry Green Software
Foundation SCI for AI figures through the Model Context Protocol (MCP)**, using
MCP's extension mechanism.

It answers one question in working code:

> When an AI agent calls a tool over MCP, how can the tool tell the agent what
> that call cost in energy and carbon, in a standard way?


---

## Disclaimer

This is an **educational, illustrative prototype**, not a standard and not
production code.

- The MCP extension shape here is a **proposal to start a conversation**. The
  normative specification is intended to be developed as a GSF working-group
  project. See [Next steps](#next-steps).
- The energy figures come from a **mock model with estimated per-token energy**.
  They are not measurements and not claims about any real provider.
- The SCI maths is the GSF formula, unchanged. What this project adds is only
  the *transport*: how the numbers travel inside MCP messages.

---

## What it shows

```
 MCP client (agent)                      MCP server (tool provider)
 ──────────────────                      ──────────────────────────
 server/discover  ───────────────────►   "I support foundation.greensoftware/sustainability"
                  ◄───────────────────   capabilities.extensions[...]

 tools/list       ───────────────────►   tool `summarize`
                  ◄───────────────────   _meta: methodology, functional unit, boundary,
                                                typical SCI per request      (static, cached)

 tools/call       ───────────────────►   run the tool
   (client declares the extension)
                  ◄───────────────────   content: the summary
                                          _meta: energy, carbon intensity, operational,
                                                 embodied, total, SCI for THIS call
```

Three ideas, kept deliberately small:

1. **Disclosure on `tools/list`.** What standard, what unit of work, what is in
   and out of the boundary, and a typical figure. Static, so it is cacheable.
2. **Attribution on `tools/call`.** Energy, carbon intensity, operational and
   embodied emissions, and the SCI score for that specific call. Sent only when
   the client asked for the extension.
3. **Nothing changes for ordinary clients.** A client that does not know about
   the extension gets exactly the same tool results as before.

The formula is the SCI for AI formula, in one pure file:

```
SCI = (E × I + M) / R
```

| Symbol | Where it comes from in this demo |
|---|---|
| **E** energy (kWh) | Estimated from token counts using a per-token profile. Swap in a measured figure by passing `energy_kwh` to `Usage`. |
| **I** carbon intensity (kgCO2e/kWh) | Location-based table for the deployment region. |
| **M** embodied (kgCO2e) | 12% of operational unless the provider reports a real figure. |
| **R** functional unit | One request. |

Every figure is labelled `measured` or `estimated`, following the GSF
`llm-inference` reference implementation.

## Quick start

```bash
pip install -e .
mcp-sci-demo
```

The demo starts the server over stdio and runs the client twice: once with the
extension declared, once as a plain MCP client. You will see the disclosure on
`tools/list`, the attribution on `tools/call`, and then the same call from a
plain client with no sustainability data attached. Recorded output is in
`docs/fixtures/demo-output.txt`.

Run the tests:

```bash
pip install -e ".[dev]"
pytest
```

## What the messages look like

**`server/discover`** – the server advertises the extension:

```json
"extensions": {
  "foundation.greensoftware/sustainability": {
    "version": "0.1.0-experimental",
    "methodology": "SCI-for-AI",
    "publisher": { "name": "Example Service Provider" }
  }
}
```

**`tools/list`** – each tool carries its disclosure in `_meta` (abridged):

```json
"_meta": {
  "foundation.greensoftware/sustainability": {
    "methodology":    { "id": "SCI-for-AI", "base": "SCI (ISO/IEC 21031:2024)" },
    "functionalUnit": { "name": "request", "description": "One summarization request." },
    "boundary": {
      "persona": "consumer", "phase": "inference",
      "description": "Inference on the hosted model endpoint ... Excludes training, network transit, the MCP transport, and the calling agent.",
      "includes": ["compute", "embodied-hardware"],
      "excludes": ["training", "network-transit", "mcp-transport", "calling-agent"]
    },
    "typical": { "sci": { "value": 0.000546, "unit": "gCO2e/request" }, "basis": "estimated" }
  }
}
```

**`tools/call`** – the result carries the attribution for that call:

```json
"_meta": {
  "foundation.greensoftware/sustainability": {
    "functionalUnit":  { "name": "request", "quantity": 1 },
    "boundary":        { "persona": "consumer", "phase": "inference" },
    "energy":          { "value": 1.46e-06, "unit": "kWh", "basis": "estimated" },
    "carbonIntensity": { "value": 0.058, "unit": "kgCO2e/kWh", "region": "europe-north1", "basis": "location-based" },
    "emissions":       { "operational": 0.0000849, "embodied": 0.0000102, "total": 0.0000951, "unit": "gCO2e",
                         "embodiedBasis": "estimated (12% of operational)" },
    "sci":             { "value": 0.0000951, "unit": "gCO2e/request" },
    "details":         { "model": "mock-mini", "inputTokens": 34, "outputTokens": 17, "outcome": "completed" }
  }
}
```

Full recorded messages: `docs/fixtures/server-discover.json`,
`docs/fixtures/tools-list.json`, `docs/fixtures/tools-call-result.json`.

## How it is built

```
src/mcp_sci/
├── sci.py         The SCI formula. Pure Python, no MCP. Mirrors the GSF llm-inference example.
├── extension.py   The MCP extension: builds the _meta blocks and attaches them.
├── server.py      A normal MCP server with one tool. The SCI-specific lines are marked "# <-- SCI".
└── client.py      A demo client that prints what came back.
```

The extension uses the official MCP Python SDK's `Extension` base class, so
adding it to any server is one line:

```python
mcp = MCPServer("my-server", extensions=[SustainabilityExtension({"my_tool": disclosure})])
```

and a tool reports its usage with one line:

```python
record(Usage(input_tokens=in_tok, output_tokens=out_tok, functional_units=1))
```

Everything else, including deciding whether the client opted in and attaching
the attribution to the result, happens in the extension.

## Choices made here, and why

| Choice | Reason |
|---|---|
| Disclosure on `tools/list`, attribution on `tools/call` | The disclosure is static; putting it on every call wastes bytes. MCP 2026-07-28 lets list responses be cached (`ttlMs`), so the server sets a one-hour cache hint. |
| Attribution only when the client opts in | Keeps ordinary tool calls unchanged and small. |
| `gCO2e` for output, `kWh` for energy | Readable at per-request scale. The formula works in kg internally. |
| Every number labelled measured / estimated | Same rule as the GSF llm-inference example. |
| Free-text boundary plus include/exclude tags | Free text is authoritative; tags let software spot when two disclosures measure different things. |
| Identifier `foundation.greensoftware/sustainability` | MCP's reverse-DNS rule for vendor extensions. If adopted officially it would become `io.modelcontextprotocol/...`. |

## Next steps

This prototype is meant to seed a proper specification. The suggested path:

1. **Discuss** the shape here in the GSF community and with the MCP maintainers
   under the Agentic AI Foundation.
2. **Form a joint working-group project** (GSF for the meaning of the data; MCP
   for transport and negotiation) to write the normative spec: required fields,
   units, boundary vocabulary, assurance and provenance, task and multi-step
   interactions, conformance tests.
3. **Reference implementation in an official MCP SDK**, which MCP requires before
   an extension can be accepted on its Extensions Track.
4. **Submit a SEP** on the MCP Extensions Track.

Alternative implementations (TypeScript, other functional units, measured
energy via an instrumentation library, other AI workload classes) are welcome
alongside this one.

## References

- SCI for AI: https://sci-for-ai.greensoftware.foundation/
- SCI (ISO/IEC 21031:2024): https://greensoftware.foundation/standards/sci/
- GSF llm-inference reference implementation: https://github.com/Green-Software-Foundation/reference-implementations/tree/main/specifications/sci-for-ai/gsf/llm-inference
- MCP extensions: https://modelcontextprotocol.io/extensions/overview
- MCP 2026-07-28 changelog: https://modelcontextprotocol.io/specification/2026-07-28/changelog

## License

MIT. See `LICENSE`.
