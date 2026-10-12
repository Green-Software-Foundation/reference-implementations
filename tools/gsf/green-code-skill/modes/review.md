# Review mode

Existing code audited against green patterns, reported as severity-ranked findings.

## Steps

1. **Read every file in scope end to end** before flagging anything. Done when you can list the files reviewed.
2. **Name the workload(s)** and open the matching pattern file(s) (index in `SKILL.md`).
3. **Sweep the detection signals.** Check each pattern in the opened files against the code and sort it into one bucket: *finding*, *pass*, *out of scope* (needs ops input: region, instance type, grid), or *not applicable* (no such code). Done when every pattern in those files sits in exactly one bucket.
4. **Test each finding against context** using the matching family in `references/trade-offs.md`. Drop or downgrade findings the context makes wrong, such as SSR for a low-traffic tool or batching on a real-time path.
5. **Rate severity and write the report**, sorted High → Low. Findings, passes, and out-of-scope fill the template's three sections. Leave *not applicable* out.

## Severity

- **High**: scaled, ongoing emissions on every request or every user. Examples: uncompressed images served to all visitors; unbounded LLM retries on a production hot path.
- **Medium**: meaningful but bounded, or the fix is non-trivial. Example: sync I/O in an hourly batch job.
- **Low**: minor or context-dependent. Example: one decorative GIF.

SCI impact stays *directional* (honesty rule 1). When the user disputes a High finding's impact or wants numbers, offer Measure mode with the current code as baseline and the fix as variant.

## Report template

```
## Green Software Review

**Workload type:** <web | cloud backend | data pipeline | AI/ML | agentic AI | mixed>
**Files reviewed:** <list>

### Findings

#### [High] <Pattern name>
- **Location:** <file:line or function>
- **Issue:** <one or two sentences>
- **Pattern:** <name + URL>
- **SCI impact:** <which term, directional magnitude>
- **Suggested fix:** <concrete refactor: snippet if short, approach if long>

#### [Medium] ...
#### [Low] ...

### Patterns checked and passed
- <patterns the code already follows>

### Out of scope (need ops/architecture input)
- <patterns code alone can't settle: region, instance type, grid intensity>
```
