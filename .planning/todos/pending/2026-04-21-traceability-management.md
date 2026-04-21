---
created: 2026-04-21T00:00:00
title: Implement traceability management
area: general
files: []
---

## Problem

Requirements traceability is currently absent. There is no way to:
- Link a requirement to the decision(s) that produced it (bidirectional linking)
- Determine which other requirements or system components are affected when one requirement changes (impact analysis)
- Record *why* a requirement was created, modified, or removed — i.e., decision logging with rationale
- Produce a structured diff of requirement changes over time with the reasoning attached

Without this, the agent can store requirements but cannot answer "what breaks if I change REQ-42?" or "why was this requirement added in the first place?", which are core to requirements engineering value.

## Solution

TBD — likely a v2 feature. Possible approach:
- Add a `traces` table to the SQLite schema linking requirements to decisions, other requirements, or source artefacts (meeting minutes, documents)
- Add `UpdateRecord` entries with `rationale` field and link to the changed requirement
- Expose impact analysis via `db.get_impacted_by(req_id)` returning all linked items
- Surface in `status-report` skill as a traceability matrix
