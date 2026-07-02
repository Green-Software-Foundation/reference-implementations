# Green Code Skill — Aider

Quickstart for installing and using the Green Software skill in Aider (CLI).

## Install

Aider supports loading external convention files. Two options.

**Option 1 — Persistent convention file (recommended for team use):**

```bash
cp green-code-skill/AGENTS.md /path/to/your/project/CONVENTIONS.md
```

Then launch Aider with the file loaded:

```bash
aider --read CONVENTIONS.md
```

Or add it to your Aider config file (`.aider.conf.yml`) so it loads automatically every session:

```yaml
read:
  - CONVENTIONS.md
```

**Option 2 — Load per-session:**

Launch Aider normally, then in the Aider prompt:

```
/read AGENTS.md
```

The file remains loaded for the rest of the session.

## Verify

In an Aider session with the conventions loaded, send:

> Using the green-code-skill, generate a Node.js Express endpoint that returns a paginated list of products from a PostgreSQL database.

If Aider produces code followed by a **Green Notes** block citing GSF pattern URLs, the conventions are active.

## Tool-specific notes

**Read-only context.** Aider treats `--read` files as reference material that stays in the context window without being editable. This is what you want — the green-code-skill guidance should influence behavior, not be modified by Aider itself.

**Persistent across the session.** Once loaded, the guidance stays in context for every message in the session. If you `/clear` history or start a new session, you need to reload it (or use the config file to auto-load).

**Model choice.** Aider works with many models. Models with stronger instruction-following (Claude, GPT-4-class, o-series) will produce the most consistent Green Notes blocks and SCI mapping. Aider's default model choice can be adjusted per session.

**Repo maps.** Aider maintains a repo map alongside your conventions. The green-code-skill guidance composes with Aider's understanding of your codebase — refactors it suggests will follow both your code structure and SCI-aligned patterns.

## Troubleshooting

**Guidance not applied.** Confirm the file was loaded — Aider prints a confirmation ("Added CONVENTIONS.md to the chat") when `--read` succeeds. If you loaded per-session with `/read`, confirm the file path was correct.

**Context window pressure.** The green-code-skill AGENTS.md is around 300 lines. On projects with very large repo context, you may see context pressure. If this becomes an issue, keep only the top-level workflows and pattern index in Aider's conventions and let Aider fetch pattern details from the canonical GSF URLs when needed.

**Aider ignores the conventions in a specific mode.** In some Aider modes, context handling differs. Reload with `/read` if needed, or add the file to your config for automatic loading.

## Next steps

For worked examples of both generation and review modes, prompts to try across workload types, and best-practice prompting patterns, see the [shared usage guide](../GETTING_STARTED.md).
