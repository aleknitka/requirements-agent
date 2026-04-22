---
title: Skill auto-update skill
trigger_condition: After rendered docs pipeline is in place and at least 2 skills have SKILL.md files with CLI references that could drift
planted_date: 2026-04-22
---

# Seed: Skill Auto-Update Skill

## Idea

A skill that reads the rendered `docs/api/` documentation and patches SKILL.md files when the package API changes. Self-maintaining skills — the agent keeps itself current.

## Behaviour

When invoked (manually or triggered by a post-commit hook that detects package changes):

1. Read `docs/api/<module>.md` for each changed module
2. Parse current CLI commands, flags, return shapes from rendered docs
3. Compare against CLI invocations described in each `SKILL.md`
4. Produce a diff of what changed: removed commands, renamed flags, new required args
5. Propose SKILL.md patches — user reviews and approves before write
6. Optionally run in autonomous mode: auto-apply non-breaking updates (new optional flags, improved error messages), flag breaking changes for human review

## Why a skill, not a script

The update logic requires natural language understanding to map rendered docs (prose + examples) to SKILL.md instruction language. An agent skill is better suited than a regex script for this — it can rewrite instruction prose, not just substitute strings.

## Trigger

Activate after the installable package scaffold phase is complete and `docs/api/` is being auto-rendered on commit.
