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

## PDF rendering

The MCP server exposes `get_full_report`, which returns one JSON
snapshot of every requirement, audit row, and attached / unattached
issue. The PDF renderer is a thin script that consumes that payload:

```bash
# From a file
uv run python skills/status-report/scripts/mcp_report_to_pdf.py \
    --input report.json --output STATUS.pdf

# From stdin (chain with curl, jq, or any MCP client that prints the
# get_full_report response)
get_full_report_output | uv run python \
    skills/status-report/scripts/mcp_report_to_pdf.py --output STATUS.pdf
```

When `--output` is omitted the script writes
`STATUS-<project>-<timestamp>.pdf` to the current directory.

`mcp_report_to_pdf.py` is a single self-contained script: it maps the
MCP payload onto an internal `{title, metadata, sections}` document
shape and feeds it to ReportLab Platypus. Tests live at
`skills/tests/test_mcp_report_to_pdf.py` and are picked up by the
project-wide `pytest` run.

## Typical workflow
1. Run `generate --format md` to review
2. Run `integrate` in meeting-agent if there are unintegrated meetings first
3. Run `save` to archive the point-in-time report
4. Share the .md file with stakeholders
5. For an executive-facing artefact, dump `get_full_report` and run
   `mcp_report_to_pdf.py` to attach a PDF.
