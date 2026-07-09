# Reference Implementations

A community-driven, educational collection maintained by the
[Green Software Foundation](https://greensoftware.foundation/),
holding working examples of how GSF specifications and green-software
tools can be applied in practice.

Each entry is one possible way to apply something — not a recommended
toolchain or a production-grade system. The implementations are
educational starting points, intended to be read, run, and adapted to
each team's own context.

## What is a reference implementation?

A reference implementation in this repository:

- **Demonstrates one concrete way** to apply a GSF specification or to
  encode a green-software practice into a working tool. Alternative
  implementations of the same thing, taking different valid approaches,
  are explicitly welcome.
- **Is runnable** — anyone can clone, install, and explore the example
  locally.
- **Includes sample data or recorded fixtures where applicable**, so the
  example can be tried without paid API access or proprietary
  infrastructure.
- **Is open source** under an OSI-approved license (MIT preferred for
  consistency across GSF code repositories).
- **Documents its scope, choices, and assumptions** so readers can
  evaluate them against their own context.

A reference implementation is an educational, illustrative example.
Different workloads and teams will reasonably make different choices
about tools, measurement providers, and approach. Each implementation
documents the choices it made so readers can evaluate them against
their own context.

## Repository structure

The repository is organised into two top-level categories:

```
reference-implementations/
├── specifications/                    Implementations of GSF specifications
│   └── <specification>/
│       ├── gsf/                       Maintained by the Green Software Foundation
│       └── community/                 Contributed and maintained by the community
│
└── tools/                             Developer tools, agent skills, linters, workflows
    ├── gsf/                           Maintained by the Green Software Foundation
    └── community/                     Contributed and maintained by the community
```

**`specifications/`** holds runnable implementations of GSF
specifications (such as SCI, SCI for AI, and others as they mature)
applied to specific workload classes.

**`tools/`** holds developer-facing tools that encode green-software
practices — agent skills, code-review assistants, linters, GitHub
Actions, dashboards, and similar working examples that help teams
build greener software day to day.

Within each category, the **`gsf/`** subdirectory holds implementations
maintained by the Green Software Foundation, and **`community/`** holds
contributions maintained by the broader community. The folder a project
lives in reflects who stewards it, not who originally built it.

## Available reference implementations

| Project | Implements | Category | Maintainer |
|---|---|---|---|
| [sci-for-ai / llm-inference](./specifications/sci-for-ai/gsf/llm-inference/) | [SCI for AI](https://sci-for-ai.greensoftware.foundation/) applied to LLM inference | Specifications | GSF |
| [green-code-skill](https://github.com/Green-Software-Foundation/reference-implementations/tree/main/tools/gsf/green-code-skill) | GSF Patterns Catalog and SCI principles applied to code generation and code review by agentic coding tools | Tools| GSF |
| [agentic-ai-impact-explorer](https://github.com/Green-Software-Foundation/reference-implementations/tree/main/tools/gsf/agentic-ai-impact-explorer) | An interactive educational simulator for cost, energy, carbon, and water impact of agentic LLM workloads with reduction levers mapped to green software patterns | Tools | GSF |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the contribution process,
including how to propose a new reference implementation, the conventions
each project should follow, and the difference between GSF-maintained
and community-maintained entries.

## License

The reference implementations in this repository are individually
licensed; see each project's `LICENSE` file. Documentation and the
top-level repository contents are licensed under the
[MIT License](./LICENSE).

## Governance

This repository is maintained by the Green Software Foundation. For
questions about scope, governance, or working-group involvement, please
reach out via the
[GSF community channels](https://greensoftware.foundation/community/)
or open an issue.
