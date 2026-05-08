---
name: review-requirements
description: >
  Review requirements for quality issues — gaps in success-criteria coverage, conflicting
  statements, and missing FRET fields. Use this skill when the user asks to audit, review,
  or validate the current requirement set.
license: MIT
allowed-tools: Read Grep Glob
metadata:
  author: aleksander nitka
  version: "1.0.0"
  category: requirements
---

# Review Requirements Skill

Runs automated checks across the full requirements set and reports issues.

## Checks performed

- **Gaps:** Missing requirement types, requirements without descriptions/owners/FRET, open critical items
- **Conflicts:** Contradictory timing constraints on the same component, circular predecessor chains
- **Coverage:** Cross-references success criteria against requirement content

## Commands

```bash
uv run review report    [--project <slug>]   # full review (recommended)
uv run review gaps      [--project <slug>]   # gaps only
uv run review conflicts [--project <slug>]   # conflicts only
uv run review coverage  [--project <slug>]   # success criteria coverage
```

## After review
For each flagged issue, use `project-update` skill to fix requirements or
`project-init` skill to add missing success criteria.
