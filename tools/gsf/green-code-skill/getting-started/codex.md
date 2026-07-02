# Green Code Skill — OpenAI Codex (CLI and Cloud)

Quickstart for installing and using the Green Software skill in OpenAI Codex — CLI, Codex Cloud, or the ChatGPT Codex tab.

## Install

Codex reads project-level agent instructions from `AGENTS.md` at the repository root.

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

**For Codex Cloud, commit and push the file.** Codex Cloud can only see files that are committed to the branch it is running against.

## Verify

**In the CLI:**

```bash
cd /path/to/your/project
codex
```

Then send:

> Using the green-code-skill, generate a Node.js Express endpoint that returns a paginated list of products from a PostgreSQL database.

**In Codex Cloud or the ChatGPT Codex tab:**

Open the repository (with `AGENTS.md` committed at the root) and start a session, then send the same prompt.

If the response includes code followed by a **Green Notes** block citing GSF pattern URLs, the guidance is active.

## Tool-specific notes

**Nested AGENTS.md.** Codex supports nested `AGENTS.md` files in subdirectories. If you have subprojects with different guidance, you can place a green-code-skill-specific `AGENTS.md` in a subfolder to scope the skill there.

**Task delegation.** Codex Cloud often runs tasks in parallel worker sessions. `AGENTS.md` applies to each worker independently, so the green-code-skill guidance is consistent across concurrent tasks.

**Codex CLI vs Cloud.** The CLI reads `AGENTS.md` from your local filesystem; the Cloud reads it from the committed branch. Keep the file identical in both, or Cloud sessions will follow the last-pushed version and CLI sessions will follow your working copy.

## Troubleshooting

**Guidance not applied in the CLI.** Confirm `AGENTS.md` is at the directory where you launched `codex`. Codex reads AGENTS.md from the current working directory and its parents.

**Guidance not applied in the Cloud.** Confirm the file is committed and pushed to the branch Codex is running against. Uncommitted changes are invisible to Cloud sessions.

**Merge conflicts with existing AGENTS.md.** Split the file into clear sections with `## ` headings. Codex reads the whole file — the section headings help both the reader and the model organize the guidance.

## Next steps

For worked examples of both generation and review modes, prompts to try across workload types, and best-practice prompting patterns, see the [shared usage guide](../GETTING_STARTED.md).
