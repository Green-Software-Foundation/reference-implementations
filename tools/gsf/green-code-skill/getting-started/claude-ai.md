# Green Code Skill — Claude (claude.ai web and desktop)

Quickstart for installing and using the Green Software skill in Claude on claude.ai (web or desktop app).

## Install

1. Confirm **Code execution and file creation** is enabled in your account. On Team and Enterprise plans, the organization owner must also enable Skills in Organization settings before individual members can upload skills.
2. Package the skill folder as a ZIP file. The ZIP must contain the `green-code-skill/` folder itself at the root, not just `SKILL.md`.
3. Open https://claude.ai/customize/skills (or navigate through **Customize → Skills**).
4. Click the **+** button, then **+ Create skill**, and upload the ZIP.
5. Toggle the skill on in your skills list.

Custom skills you upload are private to your individual account. On Team and Enterprise plans, you can share the skill with specific colleagues or organization-wide from the same Customize → Skills page.

Reference: Anthropic's official guide is at https://support.claude.com/en/articles/12512180-use-skills-in-claude.

## Verify

Open a new chat in claude.ai and send:

> Using the green-code-skill, generate a Node.js Express endpoint that returns a paginated list of products from a PostgreSQL database.

If Claude produces code followed by a **Green Notes** block citing GSF pattern URLs, the skill is active.

## Tool-specific notes

**Auto-triggering.** Claude activates the skill automatically when your prompt matches its description — you do not need to name it in every message once it is enabled. Naming it explicitly ("use the green-code-skill to...") on the first turn is a helpful way to guarantee activation while you get familiar with it.

**Skill sharing (Team and Enterprise plans).** From the same Customize → Skills page, you can share the skill with specific colleagues or organization-wide. Recipients get read-only access — they can enable and use the skill but cannot edit it. Updates you push propagate to recipients automatically.

**Runtime environment.** claude.ai custom skills run in Anthropic's managed container. Only pre-installed packages are available at runtime; skills cannot install additional packages during execution.

## Troubleshooting

**The skill does not appear in the Customize → Skills list after upload.** Confirm your ZIP contains the `green-code-skill/` folder at the root of the archive, not the individual files (`SKILL.md`, `AGENTS.md`, etc.) extracted from it. Re-zip if needed.

**The skill is uploaded but does not trigger.** Confirm the toggle in your skills list is on. Confirm Code execution and file creation is enabled in your account. Try naming the skill in your first message: "use the green-code-skill to...".

**Getting a "Skills not enabled" message on Team or Enterprise.** Your organization owner needs to enable both Code execution and file creation and Skills in Organization settings before individual members can upload or use custom skills.

## Next steps

For worked examples of both generation and review modes, prompts to try across workload types, and best-practice prompting patterns, see the [shared usage guide](../GETTING_STARTED.md).
