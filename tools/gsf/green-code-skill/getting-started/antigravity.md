# Green Code Skill — Google Antigravity

Quickstart for installing and using the Green Software skill in Google Antigravity.

## Install

Antigravity reads project-level agent instructions from `AGENTS.md` at the project root.

**If your project does not yet have an `AGENTS.md`:**

```bash
cp green-code-skill/AGENTS.md /path/to/your/project/AGENTS.md
```

**If your project already has an `AGENTS.md`:**

Append the green-code-skill content under a clear heading:

```bash
echo "" >> /path/to/your/project/AGENTS.md
echo "## Green Software guidance" >> /path/to/your/project/AGENTS.md
cat green-code-skill/AGENTS.md >> /path/to/your/project/AGENTS.md
```

Open the merged file and remove any duplicated boilerplate (repeated section headers, redundant introductions) so both sections read cleanly.

## Verify

Open the project in Antigravity. In an agent conversation, send:

> Using the green-code-skill, generate a Node.js Express endpoint that returns a paginated list of products from a PostgreSQL database.

If the agent produces code followed by a **Green Notes** block citing GSF pattern URLs, the guidance is active.

## Tool-specific notes

**Commit to the repo.** Antigravity picks up `AGENTS.md` on project open. Commit it to version control so every agent session in every clone gets the same guidance.

**Multi-agent workflows.** Antigravity supports multiple concurrent agents. `AGENTS.md` applies to all of them, so the green-code-skill guidance is consistent across agent roles (code, review, planning) without additional setup.

**Model choice.** Antigravity lets you choose the underlying model. Models that follow AGENTS.md conventions most closely will produce the most consistent Green Notes blocks and SCI mapping. If output quality varies, try a stronger reasoning model.

**Layering with team conventions.** If your team already has an `AGENTS.md` with code style and testing conventions, keep both — the green-code-skill guidance is additive and composes with existing rules without conflicts.

## Troubleshooting

**Guidance not applied.** Confirm `AGENTS.md` is at the project root and readable by Antigravity. Restart the agent session — some Antigravity workflows cache the instructions at session start.

**Output style varies between sessions.** This is normal — different model choices and different prompt phrasings produce different output. If you need strict Green Notes formatting, add a prompt-level nudge: "produce output following the Green Notes format described in AGENTS.md."

**Only part of the guidance applies.** `AGENTS.md` is a portable single-file version of the skill with all patterns summarized inline. For the deepest per-pattern detail, agents can fetch the canonical GSF pattern URLs cited in the file when needed.

## Next steps

For worked examples of both generation and review modes, prompts to try across workload types, and best-practice prompting patterns, see the [shared usage guide](../GETTING_STARTED.md).
