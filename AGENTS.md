# AGENTS.md — agent-glance

> Shared agent guide. Claude Code, Codex, agy, and hermes all load this file.

## Role

TODO: describe what this plugin does. The authoritative workflow is
`skills/agent-glance/SKILL.md`. Host-discovery copies live under `.claude/skills/`,
`.codex/skills/`, and `.hermes/skills/` and must mirror it.

## Host differences

- **Claude Code**: uses `commands/` (slash commands) + SKILL.
- **Codex / agy / hermes**: no `commands/` support — follow SKILL.md intent->action table.
