# Green Code Skill — Other Tools

Quickstart for installing the Green Software skill in agentic coding tools not covered by a dedicated guide. The general approach: find where your tool reads project-level instructions or system prompts, then put the contents of `AGENTS.md` there.

## The general approach

Most agentic coding tools support one or more of these instruction mechanisms:

1. **A project-level instructions file** at the repository root (or a `.tool/` subdirectory), loaded automatically when the tool opens the project.
2. **A user-level or global instructions file** at a location like `~/.tool/`, applied to every session.
3. **A custom instructions or system prompt field** in the tool's UI, applied to every conversation.

Any of these can host the green-code-skill guidance. The content is the same — the contents of `AGENTS.md` — the only thing that changes is where it lives.

## Common tools and their instruction file locations

| Tool | Where to put `AGENTS.md` contents |
|---|---|
| **Continue** (VS Code, JetBrains) | `.continue/rules.md` at project root, or a custom rules file referenced from `.continue/config.json` |
| **Cline** (VS Code) | `.clinerules` at project root |
| **Roo Code** (VS Code) | `.roo/rules/green-code-skill.md`, or per-mode: `.roo/rules-code/`, `.roo/rules-architect/` |
| **Zed AI Assistant** | Assistant panel → Settings → Custom instructions, or the Zed settings file |
| **JetBrains AI Assistant** | Settings → Tools → AI Assistant → Custom instructions (project-level or global) |
| **ChatGPT Projects** | Project → Instructions field (paste `AGENTS.md`) |
| **Claude Projects** | Project → Custom instructions (paste `AGENTS.md`) |
| **Gemini Gems** | Gem instructions field |
| **Any tool with an "agents" file convention** | Check for `AGENTS.md`, `AI_INSTRUCTIONS.md`, `.ai/instructions.md`, `.rules/`, `.rules.md`, or similar — many tools have converged on `AGENTS.md` |

If your tool is not listed, search its documentation for "custom instructions," "system prompt," "rules for AI," "project guidelines," "context files," or "agent instructions" — the phrasing varies.

## Install

Once you have found the right file or field for your tool:

```bash
cp green-code-skill/AGENTS.md /path/to/your/tool/instructions/file
```

Or paste the contents of `AGENTS.md` into the appropriate UI field.

If the file already contains other guidance, append the green-code-skill content under a clear heading like `## Green Software guidance` rather than replacing it.

## Verify

In your tool, send:

> Using the green-code-skill, generate a Node.js Express endpoint that returns a paginated list of products from a PostgreSQL database.

If the response includes code followed by a **Green Notes** block citing GSF pattern URLs, the guidance is active.

## Tool-agnostic notes

**System-prompt-only tools.** Some tools only expose a single system-prompt field with no project-level scoping. This works, but the guidance will apply to every conversation in that tool, not just coding tasks. If that is too broad, consider creating a dedicated project (or "custom GPT / gem") for coding work with the guidance loaded there.

**Model choice.** Any tool built on a capable LLM (Claude, GPT-4-class, Gemini Pro, o-series, or comparable) will follow the AGENTS.md-style guidance. Weaker models may produce less consistent Green Notes blocks. If output quality is poor, try upgrading the model your tool uses.

**Portability.** The `AGENTS.md` file in this package is designed to be portable. It contains all pattern summaries inline (no external references) so it works in tools that only accept a single instructions file.

## Troubleshooting

**Guidance not applied.** Confirm the file is in the right location and readable by your tool. Restart the tool or session — many tools cache instructions at startup.

**No Green Notes block in output.** Add a prompt-level nudge: "produce output following the Green Notes format described in the instructions." Some tools follow embedded output formats more loosely than others.

**Output style varies between conversations.** This is normal for tools without strict rule enforcement. If consistency matters, name the skill explicitly in each session's first message: "use the green-code-skill for this conversation."

## Contributing a dedicated guide

If your tool has enough users and specific quirks to warrant a dedicated quickstart in this package, contributions are welcome. Follow the same four-section structure the other guides use — Install, Verify, Tool-specific notes, Troubleshooting — plus a link to the shared usage guide.

## Next steps

For worked examples of both generation and review modes, prompts to try across workload types, and best-practice prompting patterns, see the [shared usage guide](../GETTING_STARTED.md).
