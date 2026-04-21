---
created: 2026-04-21T00:00:00
title: Full FRET formalisation pipeline
area: general
files:
  - skills/refine-requirements/references/fret_grammar.md
  - skills/refine-requirements/scripts/refine.py
  - shared/models.py
---

## Problem

The FRET grammar reference exists and `fret_statement` is a field on `RequirementRow`, but the pipeline that takes a natural language requirement and produces a well-formed FRET statement across all five structured fields is not fully implemented or validated:

- **scope**: when does the requirement apply (e.g., "while system is initialised")
- **condition**: triggering event or state (e.g., "when user submits input")
- **component**: the system element responsible (e.g., "the data pipeline")
- **timing**: temporal constraint on the response (e.g., "within 100ms", "immediately", "eventually")
- **response**: what the component must do

The `refine.py` CLI exists but the interactive elicitation loop that walks the user through each FRET field — resolving ambiguities and producing a machine-checkable statement — is not confirmed to be end-to-end working.

## Solution

For v1: ensure `refine.py` can take a raw NL requirement and produce a complete, parseable FRET statement stored in `RequirementRow.fret_statement`. Fields may be populated interactively (agent asks per field) or in one LLM pass with validation.

For v2+: validate the output FRET statement against a grammar checker; support all FRET timing keywords (immediately, next, until, before, after, within); export FRET statements in the format expected by NASA FRET tooling.
