---
name: status-report
description: >
  Generate a structured project status report from current DB state. Use this skill when the user asks for "project status", "status report", "how are we doing?", "give me a summary of the project", "what's the health of the project?", "generate a status update for stakeholders", or before a steering committee meeting. The report includes health signal (RED/AMBER/GREEN),requirement counts, open decisions, pending actions, and recent changes.
---

# Status Report Skill

Reads the live DB state and generates a structured status report with health signal.

## Health signals
- **GREEN** — no critical open items, few pending actions
- **AMBER** — some items need follow-up
- **RED** — significant open issues (>3 critical open, or >5 open decisions)

## Commands

```bash
# Print JSON report to stdout
python skills/status-report/scripts/report.py generate [--format json|md]

# Save timestamped STATUS-<timestamp>.md + .json alongside PROJECT.md
python skills/status-report/scripts/report.py save
```

## Typical workflow
1. Run `generate --format md` to review
2. Run `integrate` in meeting-agent if there are unintegrated meetings first
3. Run `save` to archive the point-in-time report
4. Share the .md file with stakeholders