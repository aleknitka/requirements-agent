---
title: Proactive skill contract testing
trigger_condition: After package scaffold phase — when requirements_agent package has enough surface area to validate against SKILL.md files
planted_date: 2026-04-22
---

# Seed: Proactive Skill Contract Testing

## Idea

A CI check (or pre-commit hook) that compares what SKILL.md files claim the tools do against what the installed `requirements_agent` package actually exposes. Catches drift before the agent hits a runtime error.

## Possible approach

- Parse `allowed-tools` and CLI invocation examples from each SKILL.md
- Introspect the package (argparse `--help` output or a `skills.toml` manifest) for current flags and commands
- Diff: flag any SKILL.md invocations that reference non-existent commands, removed flags, or changed argument names
- Run in CI on every push that touches `tools/src/` or any `SKILL.md`

## Trigger

Activate when the `requirements_agent` package is stable enough that its CLI surface can be treated as a contract (likely after Phase 1 or Phase 2 of the installable-package phase).
