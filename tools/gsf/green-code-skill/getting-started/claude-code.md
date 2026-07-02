# Green Code Skill — Claude Code

Quickstart for installing and using the Green Software skill in Claude Code (terminal, VS Code, or JetBrains).

## Install

Claude Code reads skills directly from the filesystem — no upload step needed.

**Personal scope** (available in all your Claude Code sessions):

```bash
cp -r green-code-skill/ ~/.claude/skills/green-code-skill/
```

**Project scope** (available only inside this project):

```bash
cp -r green-code-skill/ .claude/skills/green-code-skill/
```

Confirm the folder name matches the skill name (`green-code-skill`) — Claude Code uses the folder name to identify the skill.

## Verify

Start (or restart) a Claude Code session in a directory where the skill is scoped. Send:

> Using the green-code-skill, generate a Node.js Express endpoint that returns a paginated list of products from a PostgreSQL database.

If Claude produces code followed by a **Green Notes** block citing GSF pattern URLs, the skill is active.

## Tool-specific notes

**Auto-discovery.** Claude Code scans both personal (`~/.claude/skills/`) and project (`.claude/skills/`) skill directories on session start. Project skills override personal skills with the same name.

**No upload, no toggle.** Unlike claude.ai, Claude Code does not present a skills UI. Presence on the filesystem is the enablement mechanism. To disable a skill temporarily, move or rename its folder.

**Composability.** Claude Code can use multiple skills in one session. The green-code-skill composes naturally with other skills you have installed — code style, testing conventions, deployment guidelines.

**Team distribution.** For organization-wide install, you can bundle the skill as a Claude Code Plugin. This is optional and only relevant if you want a managed distribution path rather than having each developer copy the folder manually.

## Troubleshooting

**The skill does not trigger.** Confirm the folder is at `~/.claude/skills/green-code-skill/` (personal) or `.claude/skills/green-code-skill/` (project). Restart your Claude Code session — skills load at session start.

**The wrong version loads.** If both personal and project scopes have the skill, project scope wins. Delete or update the personal version if you want the project version to be authoritative.

**Skills conflict.** If multiple installed skills contain overlapping guidance (for example, another green-code-skill or sustainability skill), Claude Code composes them but may produce mixed output. Consider scoping conflicting skills to specific projects.

## Next steps

For worked examples of both generation and review modes, prompts to try across workload types, and best-practice prompting patterns, see the [shared usage guide](../GETTING_STARTED.md).
