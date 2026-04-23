---
phase: "00-bug-triage"
plan: "02"
subsystem: "shared/models.py"
tags: ["bug-fix", "models", "enum", "requirements"]
dependency_graph:
  requires: ["00-01"]
  provides: ["RequirementType str Enum", "RequirementTypeMeta NamedTuple", "RequirementIn clean instantiation"]
  affects: ["all skill scripts that use RequirementIn", "plan 00-03 (import chain)", "plan 00-04 (req_ops.py callers)"]
tech_stack:
  added: []
  patterns: ["str Enum for requirement types", "NamedTuple for metadata list"]
key_files:
  created: []
  modified:
    - shared/models.py
decisions:
  - "models.py changes applied in plan 00-01 (Rule 3 deviation) rather than 00-02 — the RequirementArea NameError cascades through db.py import, which was 00-01's acceptance criterion"
  - "fret_statement and fret_fields removed from RequirementIn and RequirementRow (D-05) — deferred to Phase 3 where FRET fields will be added back with proper protocol"
  - "make_req_id module-level function removed (D-04) — canonical version is _make_req_id in db.py; models.py version was dead code referencing undefined RequirementArea"
metrics:
  duration: "2 minutes"
  completed: "2026-04-23"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 0
  files_created: 1
---

# Phase 0 Plan 02: Fix shared/models.py — Summary

**One-liner:** Verified RequirementType str Enum (34 codes), RequirementTypeMeta NamedTuple, and clean RequirementIn (no RequirementArea, no fret fields) — all changes applied by plan 00-01 as a Rule 3 deviation; no additional code changes required.

## What Was Built

All models.py changes required by this plan were already in place — applied in plan 00-01 as a blocking cascade fix (Rule 3). This plan's execution consisted of:

1. Verifying every must-have truth against the actual `shared/models.py`
2. Running all verification checks from the plan's `<verification>` section
3. Confirming 6/6 test_db_bugs.py tests still pass

### models.py Changes (applied in 00-01, verified here)

| Change | Before (broken) | After (correct) |
|--------|-----------------|-----------------|
| `RequirementType` class | `class RequirementType(BaseModel)` with `code`, `name`, `description` fields | `class RequirementType(str, Enum)` with 34 code values |
| Metadata list | `REQUIREMENT_TYPES: list[RequirementType]` | `REQUIREMENT_TYPE_METADATA: list[RequirementTypeMeta]` (34 NamedTuples) |
| `RequirementTypeMeta` | Not defined | `class RequirementTypeMeta(NamedTuple): code, name, description` |
| `make_req_id` | Module-level function referencing undefined `RequirementArea` | Removed |
| `RequirementIn.req_type` | `req_type: RequirementArea = RequirementArea.CORE` | `req_type: RequirementType = RequirementType.FUN` |
| fret fields | `fret_statement: Optional[str] = None`, `fret_fields: Optional[dict] = None` on `RequirementIn` | Removed (D-05) |

## Verification Results

| Check | Result |
|-------|--------|
| `RequirementType` is `str` Enum with 34 values | PASS |
| `RequirementType("FUN").value == "FUN"` | PASS |
| `RequirementTypeMeta` is a NamedTuple (tuple subclass) | PASS |
| `len(REQUIREMENT_TYPE_METADATA) == 34` | PASS |
| `RequirementIn(title="x", description="y", req_type="FUN")` instantiates | PASS |
| `hasattr(req, "fret_statement")` is False | PASS |
| `hasattr(req, "fret_fields")` is False | PASS |
| `req.req_type == RequirementType.FUN` | PASS |
| `grep -c "RequirementArea" shared/models.py` outputs `0` | PASS |
| `grep -c "make_req_id" shared/models.py` outputs `0` | PASS |
| `grep -c "fret_statement" shared/models.py` outputs `0` | PASS |
| `grep -c "fret_fields" shared/models.py` outputs `0` | PASS |
| `uv run pytest tests/test_db_bugs.py` | 6 passed |

## Deviations from Plan

### Pre-applied by Plan 00-01 (Rule 3 — blocking cascade)

All changes in this plan were applied during plan 00-01 execution as a Rule 3 (blocking) deviation. The `RequirementArea` NameError in `models.py` cascades through the `db.py` import chain, which was the acceptance criterion for plan 00-01 (`import shared.db` exits 0). Plan 00-01 applied decisions D-01 through D-05 to satisfy that criterion.

This plan's role was to verify the correct state and document completion. No additional code changes were needed.

### No Tasks Required Code Changes

Both tasks (Task 1: RequirementType Enum + RequirementTypeMeta; Task 2: remove RequirementArea/make_req_id/fret fields) found all their required changes already in place. All acceptance criteria met on first read.

## Known Stubs

None — no placeholder data or stub functions. All models are fully functional.

## Threat Flags

None — no new network endpoints, auth paths, or trust boundaries. This plan only verified/documented existing type model changes.

## Commits

No new code commits — all changes were committed in plan 00-01 (commit `0af0671`). This summary and state update are committed as the plan's documentation commit.

## Self-Check: PASSED

- FOUND: shared/models.py
- FOUND: tests/test_db_bugs.py
- FOUND commit: 0af0671 (models.py changes applied in 00-01)
- All 8 behavioral tests PASSED
- All 13 verification checks PASSED
- pytest 6/6 PASSED
