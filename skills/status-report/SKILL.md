---
name: status-report
description: >
  Generate a project status report PDF from the requirements MCP. Pulls the
  full requirements + issues snapshot via the `get_full_report` MCP tool and
  renders it to a stakeholder-ready PDF via the bundled script.
license: MIT
allowed-tools: Read Grep Glob Bash
metadata:
  author: aleksander nitka
  version: "2.0.0"
  category: requirements
---

# Status Report Skill

The skill produces a PDF status report of the project. It does not
re-implement any data access — it consumes the `get_full_report` MCP
tool exposed by `requirements-mcp-server` and converts its JSON
payload into a PDF via the bundled `mcp_report_to_pdf.py` script.

## How it works

1. The MCP server's **`get_full_report`** tool returns one JSON
   document containing:
   - every requirement, with its audit history,
   - the issues attached to each requirement (with link metadata and
     their own update history),
   - the issues not linked to any requirement,
   - a `summary` block with pre-computed counts plus an echo of the
     two filter flags.
2. `scripts/mcp_report_to_pdf.py` reads that JSON, validates it,
   maps each requirement / issue into a section of a generic
   `{title, metadata, sections[…]}` document shape, and renders the
   PDF with ReportLab Platypus.

The two filter flags supported by `get_full_report` are forwarded
unchanged in the PDF's *Summary* table:

| Flag | Default | Effect |
|---|---|---|
| `include_issues` | `true` | When `false`, every issue list is empty; requirements + audit history still render. |
| `include_closed_requirements` | `true` | When `false`, requirements in a terminal status are omitted (issues linked only to them surface under *Unattached issues* so nothing is silently lost). |

The default `get_full_report({})` call returns everything.

## Generating a PDF

The script reads its JSON either from a file or from stdin.

```bash
# From a file written out of the MCP client
uv run python skills/status-report/scripts/mcp_report_to_pdf.py \
    --input report.json --output STATUS.pdf

# Piped directly from the MCP client
mcp-client call get_full_report | \
    uv run python skills/status-report/scripts/mcp_report_to_pdf.py \
        --output STATUS.pdf
```

When `--output` is omitted the script writes
`STATUS-<project>-<utc-timestamp>Z.pdf` to the current directory.
The project component is sanitised to a filename-safe slug.

## What's in the PDF

- **Cover metadata** — project name, generation timestamp (UTC),
  per-bucket counts.
- **Summary section** — totals and filter echoes pulled from the
  payload's `summary` block.
- **One section per requirement** — header line with id / type /
  status / version, full statement, optional extended description,
  bulleted structured fields (users, triggers, pre/postconditions,
  inputs, outputs, business logic, exception handling, acceptance
  criteria), an audit-history table, and a table of linked issues.
- **One section per unattached issue** — header, description, impact,
  risk, proposed resolution, and the action log.

Long change descriptions are clamped to 500 characters with an
ellipsis so a single oversize cell cannot blow up the ReportLab table
layout. Dynamic text is HTML-escaped before being placed into
Paragraph markup, so payloads containing `<`, `>`, or `&` render
safely.

## Failure modes

The script exits non-zero with a clear message when:

- stdin is a TTY and `--input` is omitted,
- the payload is not valid JSON,
- the payload is not a JSON object,
- a top-level field is missing (`project_name`, `summary`,
  `requirements`, `unattached_issues`) — for example, when a wrapping
  envelope like `{"data": {...}}` was piped in by mistake,
- a top-level field exists but carries the wrong type
  (`summary: []`, `requirements: {}`, …).

## Tests

End-to-end + adapter tests live at
`skills/tests/test_mcp_report_to_pdf.py` and run as part of the
project-wide `uv run pytest`. They cover the adapter shape, validation
errors, slug sanitisation, UTC stamping, XML-unsafe character
handling, long-cell truncation, and an integration test that builds
the payload from the live demo data and asserts the generated PDF
starts with `%PDF`.
