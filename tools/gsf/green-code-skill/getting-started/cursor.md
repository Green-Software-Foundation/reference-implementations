# Green Code Skill — Cursor

Quickstart for installing and using the Green Software skill in Cursor.

## Install

Cursor supports two rule formats. Pick the one your Cursor version uses.

**Current format (Cursor Rules, `.cursor/rules/*.mdc`):**

Create `.cursor/rules/green-code-skill.mdc` in your project root and paste the contents of `AGENTS.md` into it. Add frontmatter at the top to control when the rule applies:

```
---
description: Apply Green Software Foundation patterns and SCI principles to code generation and review.
globs:
  - "**/*.js"
  - "**/*.ts"
  - "**/*.py"
  - "**/*.go"
  - "**/*.java"
alwaysApply: false
---

[paste AGENTS.md content here]
```

Adjust `globs` to match the file types you want the rule scoped to. Set `alwaysApply: true` if you want the rule to apply on every prompt regardless of which files are open.

**Legacy format (`.cursorrules`):**

```bash
cp green-code-skill/AGENTS.md .cursorrules
```

## Verify

Open Cursor in the project. In the chat panel, send:

> Using the green-code-skill, generate a Node.js Express endpoint that returns a paginated list of products from a PostgreSQL database.

If the response includes code followed by a **Green Notes** block citing GSF pattern URLs, the rule is active.

## Tool-specific notes

**Rule scoping.** The `.mdc` format lets you scope the rule to specific file types, paths, or contexts. Use this to keep the rule focused on code work and out of unrelated conversations (release notes, chat drafts).

**Commit to the repo.** For team consistency, commit `.cursor/rules/green-code-skill.mdc` (or `.cursorrules`) to version control. Every collaborator gets the same guidance automatically.

**Multiple rule files.** Cursor merges all matching `.mdc` files. You can layer green-code-skill with existing rules (code style, testing conventions) — no need to combine them into one file.

**Model choice.** Cursor uses different underlying models depending on your settings. All models Cursor supports can follow the AGENTS.md-style guidance, but output style and pattern coverage vary. Stronger reasoning models tend to follow the SCI mapping and Green Notes format most consistently.

## Troubleshooting

**Rule not applying.** Confirm the `.mdc` file is at `.cursor/rules/green-code-skill.mdc` and check the globs cover the file you have open. If using the legacy format, confirm `.cursorrules` is at the project root and Rules for AI is enabled in Cursor settings.

**No Green Notes block.** Ask explicitly: "add a Green Notes block explaining the green software patterns applied." The rule is guidance, not a hard-coded output format — a reminder in the prompt usually elicits it.

**Rule fires in unrelated conversations.** Set `alwaysApply: false` and tighten the `globs` field to code files only.

## Next steps

For worked examples of both generation and review modes, prompts to try across workload types, and best-practice prompting patterns, see the [shared usage guide](../GETTING_STARTED.md).
