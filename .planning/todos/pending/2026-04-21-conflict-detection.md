---
created: 2026-04-21T00:00:00
title: Implement conflict detection for requirements
area: general
files: []
---

## Problem

The agent currently stores requirements independently with no awareness of cross-requirement relationships. This means:
- Two requirements can directly contradict each other (e.g., "system SHALL respond in <100ms" vs "system SHALL process full dataset before responding") and the agent will accept both without flagging
- Completeness is never scored — there is no signal that a functional area has insufficient coverage
- Consistency checks (e.g., terminology drift, conflicting scope boundaries, overlapping FRET conditions) are not performed

Without conflict detection, a formally-structured requirement database can still be logically incoherent, which defeats the purpose of FRET formalisation.

## Solution

TBD — likely a v2 feature. Possible approach:
- At persistence time, run a lightweight consistency check against existing requirements in the same domain/component
- Use LLM-assisted contradiction detection: embed new requirement and compare against existing embeddings (sqlite-vec is already in place) — surface high-similarity pairs for human review
- Add a `completeness_score` field to `ProjectMeta` updated by `db.score_completeness(conn)` after each requirement write
- Flag contradictions as a `ConflictRecord` in the DB, surfaced in `status-report`
