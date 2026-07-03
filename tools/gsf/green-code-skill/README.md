# Green Code Skill

A reference implementation of an agent skill that applies Green Software Foundation patterns and the Software Carbon Intensity (SCI) framework to code generation and code review. This project is contributed to the [GSF Reference Implementations](https://github.com/Green-Software-Foundation/reference-implementations) collection under `tools/gsf/`.

The skill enables agentic coding tools — Claude, Claude Code, Cursor, Google Antigravity, OpenAI Codex, Aider, and others — to generate new code that follows green software patterns by default, and to review existing code against those patterns with structured, cited findings.

## Educational purpose

**This is an educational reference implementation, not a production application.** It demonstrates one concrete way to encode green software patterns as an agent skill that engineering teams can adopt and adapt.

Following the guidance shared with the [GSF Reference Implementations](https://greensoftware.foundation/articles/introducing-gsf-reference-implementations/) collection: reference implementations are intended for educational purposes — demonstrating how to apply a specification or a green software practice in code. They are not production-ready applications, and practitioners adopting them should evaluate each against their own tooling and methodology requirements.

In practice, that means:

- Treat the recommendations the skill produces as engineering input, not directives — apply them with judgment for the target context. The `references/trade-offs.md` file describes the contextual considerations that shape how each pattern is best applied.
- Treat any qualitative claim about energy, hardware, or emissions impact as directional unless backed by measurement. For real numbers, pair the skill with runtime measurement tools such as CodeCarbon, Cloud Carbon Footprint, Kepler, or the Impact Framework. The skill itself is a design-time and review-time advisor, not a measurement tool.
- Adapt the patterns, output formats, tool integration paths, and trigger keywords to fit your team's context. Different teams will reasonably make different choices about which patterns to prioritize, how strictly to enforce recommendations, and which tools to target.

## Scope and design choices

The skill covers:

- **23 patterns from the GSF Development category** — data handling, media efficiency, web performance, cloud deployment
- **17 patterns from the GSF Architecture category** — system topology and technology selection
- **9 AI/ML model and training patterns** cross-referenced from the Development and Architecture categories
- **10 agentic AI workload patterns** applying the same SCI principles to LLM-driven orchestration — model routing, retry budgets, planning depth caps, response and prompt caching, parallel tool calls, two-stage retrieval, structured output, `max_tokens` hygiene, and loop-safe tool calling

Choices this implementation made, documented so readers can evaluate them against their own context:

- **Two operating modes.** Generation (writing new code with patterns applied by default) and review (analyzing existing code and producing structured findings). Other valid implementations might specialize to one mode or add a third (for example, an "explain this file's SCI profile" mode).
- **Dual format delivery.** Anthropic-format `SKILL.md` with progressive disclosure into `references/` for tools that support multi-file skills, plus a portable `AGENTS.md` for tools that prefer a single instruction file. Other implementations might target only one format or add tool-native formats (Cursor `.mdc`, Continue `.md`, and so on).
- **SCI-grounded reasoning.** Every recommendation maps to the SCI formula (E × I + M per R), with an explicit distinction between what code can affect (E, M, R) and what deployment and operations affect (I). This reflects a design choice to prioritize honesty over over-claiming.
- **Directional impact language.** The skill avoids inventing quantitative percentages, using directional statements ("reduces E", "smaller payload per request", "improves R") until real measurement is in hand. Other implementations might allow qualitative ranges backed by industry averages.
- **Broad trigger keywords.** The skill's description activates on mentions of sustainability, carbon, energy, green coding, efficiency, and cost reduction. This is deliberate — engineering cost reduction and SCI improvement usually align, so cost-focused prompts are legitimate triggers. Narrower triggering would produce fewer false positives at the cost of missed opportunities.
- **Structured output formats.** Generation appends a "Green Notes" block; review produces a severity-sorted findings list. These are conventions this implementation defines — other implementations might use different formats (structured JSON for machine consumption, inline comments for IDE integration, and so on).

## Package contents

```
green-code-skill/
├── SKILL.md                  Anthropic-format skill (YAML frontmatter + body)
├── AGENTS.md                 Portable single-file version (no frontmatter, all inline)
├── GETTING_STARTED.md        Shared usage guide — worked examples for both modes
├── README.md                 This file
├── LICENSE                   MIT
├── getting-started/          Tool-specific install and verify quickstarts
│   ├── claude-ai.md
│   ├── claude-code.md
│   ├── cursor.md
│   ├── antigravity.md
│   ├── codex.md
│   ├── aider.md
│   └── other-tools.md
└── references/
    ├── sci-formula.md        SCI grounding — what code can and cannot affect
    ├── patterns-development.md
    ├── patterns-architecture.md
    ├── patterns-ai-ml.md
    └── trade-offs.md         Contextual considerations for applying patterns well
```

Two equivalent entry points:

- **`SKILL.md` + `references/`** — for tools that support multi-file skills with progressive disclosure (Anthropic skills on claude.ai and Claude Code). The agent reads `SKILL.md` first, then loads only the reference file(s) relevant to the task.
- **`AGENTS.md`** — for tools that prefer or require a single instruction file (OpenAI Codex, Google Antigravity, Cursor, Aider, Continue, Cline, and others). Self-contained, with pattern summaries inline and canonical links to fetch full detail on demand.

Both express the same skill.

## Getting started

Pick the quickstart for the tool you use:

- [Claude (claude.ai web / desktop)](./getting-started/claude-ai.md)
- [Claude Code](./getting-started/claude-code.md)
- [Cursor](./getting-started/cursor.md)
- [Google Antigravity](./getting-started/antigravity.md)
- [OpenAI Codex (CLI and Cloud)](./getting-started/codex.md)
- [Aider](./getting-started/aider.md)
- [Other tools](./getting-started/other-tools.md) — Continue, Cline, Roo Code, Zed, JetBrains AI, ChatGPT Projects, Claude Projects, Gemini Gems, and any tool with a project-level instructions field

Each quickstart covers install, verification, tool-specific behavior, and troubleshooting for that tool.

After installing, the [shared usage guide](./GETTING_STARTED.md) has worked examples for both modes (code generation and code review), prompts to try across workload types, and prompting best practices.

## What the skill does

The skill activates automatically when the user mentions:

- Sustainability, carbon, energy, emissions, green coding, eco-friendly, climate impact
- Reducing compute or cloud cost
- Designing cloud architectures, AI/ML pipelines, agentic AI systems, web frontends, or data handling

You can also invoke it explicitly:

- "Generate this in green style"
- "Review this for green software patterns"
- "What's the SCI impact of this code?"
- "Apply the green-code-skill"

## Two output modes

**Generation mode** — code, followed by a Green Notes block listing patterns applied, the SCI term each reduces, and links to the canonical GSF pattern. Trade-offs considered are listed explicitly.

**Review mode** — a structured findings list with severity (high/medium/low), location, issue, canonical pattern reference, qualitative SCI impact, and a concrete suggested fix. Patterns the code already passes are listed as positive feedback. Anything code cannot determine (region, instance type, grid intensity) is called out as out of scope.

## Evolution and contribution

This skill is a template as much as a working artifact. Several axes of evolution are anticipated:

- **GSF catalog growth.** The [Green Software Patterns catalog](https://patterns.greensoftware.foundation/) evolves. Future GSF versions have announced persona-based and behavioral patterns; as those are published, they can be added to the reference files here.
- **Agentic AI pattern maturation.** The 10 agentic AI workload patterns in this implementation are drawn from well-recognized engineering practices in the LLM application space. As the community formalizes patterns for this workload class, entries can be updated to reference canonical sources.
- **Tool coverage.** New agentic coding tools appear regularly. The `getting-started/` directory holds one quickstart per tool; new tool guides can be added following the same four-section structure (Install, Verify, Tool-specific notes, Troubleshooting).
- **Alternative implementations.** The GSF Reference Implementations collection explicitly welcomes different approaches to the same problem. If your team has built a skill with different pattern coverage, a different output format, or a different trigger design, contributing it alongside this one is valuable — multiple valid approaches reflect the diversity of how practitioners work.

To contribute changes to this skill or a companion implementation, see the top-level [CONTRIBUTING.md](https://github.com/Green-Software-Foundation/reference-implementations/blob/main/CONTRIBUTING.md) in the reference-implementations repository.

## What this skill is and isn't

**It is:**

- A code-time and review-time advisor grounded in 40+ peer-reviewed GSF patterns, plus agentic AI workload patterns applying the same principles
- An educational reference showing one concrete way to encode green software practices as an agent skill portable across multiple coding tools
- A template intended to evolve as the pattern catalog and agentic AI space mature

**It isn't:**

- A runtime measurement tool — pair with CodeCarbon, Cloud Carbon Footprint, Kepler, or the Impact Framework for real numbers
- A carbon accounting or reporting tool
- A substitute for the GSF Practitioner certification or the SCI specification itself
- A production-ready product — see the Educational purpose section above

## License

MIT License. See [LICENSE](./LICENSE).

## Attribution

Pattern names, descriptions, and URLs from the GSF Development and Architecture categories are sourced from https://patterns.greensoftware.foundation/ (CC BY 4.0). The Software Carbon Intensity specification is available at https://sci.greensoftware.foundation/ and extends ISO/IEC 21031:2024. The agentic AI patterns apply the same SCI principles and three-pillar logic (energy efficiency, hardware efficiency, carbon awareness) to LLM-driven orchestration workloads.

## Links

- **GSF Reference Implementations repository:** https://github.com/Green-Software-Foundation/reference-implementations
- **Introducing GSF Reference Implementations (article):** https://greensoftware.foundation/articles/introducing-gsf-reference-implementations/
- **GSF Patterns catalog:** https://patterns.greensoftware.foundation/
- **SCI specification:** https://sci.greensoftware.foundation/
- **SCI for AI specification:** https://sci-for-ai.greensoftware.foundation/
- **Green Software Foundation:** https://greensoftware.foundation/
- **Practitioner course:** https://learn.greensoftware.foundation/
