---
created: 2026-04-21T00:00:00
title: SysML v2 formalisation and diagram auto-generation
area: general
files:
  - skills/refine-requirements/references/fret_grammar.md
---

## Problem

The agent currently formalises requirements using NASA FRET grammar (natural language → structured statement). FRET is strong for behavioural/temporal requirements but does not capture structural or architectural concerns that SysML v2 expresses natively:

- **Requirement diagrams**: first-class `requirement` elements with `satisfy`, `verify`, and `derive` relationships
- **Block definitions (BDD)**: component decomposition and interface contracts
- **Use case diagrams**: actor–system interaction boundaries
- **Activity diagrams**: flow-of-control for complex functional requirements

Without SysML, the agent cannot produce artefacts that systems engineers or model-based engineering (MBE) toolchains expect, limiting adoption in enterprise ML/AI projects that sit alongside hardware or embedded systems.

## Solution

TBD — likely a v3 feature. Possible approach:
- Extend `refine-requirements` skill with a SysML mode: after FRET refinement, optionally generate a SysML v2 textual representation (SysML v2 has a standardised textual syntax since 2024)
- Add an LLM-assisted NL → SysML v2 pipeline: given a refined requirement and project context, generate block/requirement/use-case stubs
- Store generated SysML as a `sysml_snippet` field on `RequirementRow`
- Export to `.sysml` files for import into Cameo/Papyrus or the official SysML v2 pilot implementation
- Consider a `diagram-generation` skill that aggregates requirements and produces a full requirement diagram per domain area
