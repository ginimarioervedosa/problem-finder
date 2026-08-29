# AGENTS.md

Read `CLAUDE.md` in this directory in full before taking any action. It is the canonical
instruction file for this repository and it governs every agent harness that reads this
file, whatever the harness is called.

This file carries no instructions of its own, by design. It used to be a near-identical
copy of `CLAUDE.md`, and the copies drifted.

## Reading `CLAUDE.md` under a non-Claude harness

Everything in `CLAUDE.md` applies unchanged, including the conventions and rule files it
points to.

Paths, filenames and commands are literal. Do not substitute your own tool's name into
them. The previous version of this file did exactly that, and every path in the left-hand
column below was invented by the substitution:

| The old `AGENTS.md` said | What is actually on disk |
|---|---|
| `.Codex/skills/new-source-adapter/` | `.claude/skills/new-source-adapter/` |
| `.Codex/skills/new-dashboard-view/` | `.claude/skills/new-dashboard-view/` |
| `.Codex/skills/add-migration/` | `.claude/skills/add-migration/` |

Where `CLAUDE.md` names a Claude Code feature your harness has no equivalent for (slash
commands, `CLAUDE.local.md`, hooks, skills discovery), use the nearest thing your harness
offers, or skip that line. Never invent a substitute path to make it fit.

## Harness-specific configuration

Verified on disk 29 August 2026.

| Harness | Directory | Holds |
|---|---|---|
| Claude Code | `.claude/` | `skills/` (3 skills), `launch.json`, `settings.local.json`, `worktrees/` |
| Any harness | `.agents/skills/` | the same 3 skills, as a separate real directory |

`.agents/skills/` is a copy rather than a symlink, so a skill edited in one place does not
reach the other.
