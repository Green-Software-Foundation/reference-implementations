# Write mode

New code, refactors, and designs with green patterns built into the first draft.

## Steps

1. **Name the workload**: web frontend, cloud backend, data pipeline, AI/ML, agentic AI, or a mix. Note the scale signals the user gave (traffic, data volume, call rate), because they decide which patterns pay off.
2. **Shortlist 2–5 patterns.** Open the pattern file(s) for the workload (index in `SKILL.md`) and the matching families in `references/trade-offs.md`. Keep a pattern only if it passes the four-part test in that file's "The general rule". Done when every shortlisted pattern passes and every rejected candidate has a one-line reason.
3. **Write the code with the shortlist as defaults**, so the patterns are visible in the code itself: bounded retries, async I/O, paginated and projected queries, compressed payloads, a cache in front of LLM calls.
4. **Append Green Notes.** Done when every applied pattern has an entry with its SCI term and URL, and every rejected candidate from step 2 appears under *Trade-offs considered*.

## Green Notes template

```
<code>

---
Green Notes
- <Pattern name> (reduces E) — <one sentence on why it pays off here>
  https://patterns.greensoftware.foundation/<path>
- <Pattern name> (reduces M) — <one sentence>
  https://patterns.greensoftware.foundation/<path>

Trade-offs considered: <rejected patterns and why, e.g. "skipped SSR: internal admin tool, <10 concurrent users">
```

When no pattern fits, write `Green Notes: no pattern applies — <reason>` in place of the block.
