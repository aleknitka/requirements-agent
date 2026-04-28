---
name: status-report
description: >
  Generate a project status report — total counts, requirement-type breakdown, FRET
  coverage percentage, and critical-open list. Use this skill when the user asks for a
  project summary, status snapshot, or coverage report.
license: MIT
allowed-tools: Read Grep Glob
metadata:
  author: aleksander nitka
  version: "1.0.0"
  category: requirements
---

# Status Report Skill

Reads the live DB state and generates a structured status report with health signal.

## Health signals
- **GREEN** — no critical open items, few pending actions
- **AMBER** — some items need follow-up
- **RED** — significant open issues (>3 critical open, or >5 open decisions)

## Commands

```bash
# Print report to stdout
uv run report generate [--project <slug>] [--format json|md]

# Save timestamped STATUS-<timestamp>.md + .json alongside PROJECT.md
uv run report save [--project <slug>]
```

## Typical workflow
1. Run `generate --format md` to review
2. Run `integrate` in meeting-agent if there are unintegrated meetings first
3. Run `save` to archive the point-in-time report
4. Share the .md file with stakeholders
