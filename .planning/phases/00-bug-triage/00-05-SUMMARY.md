---
phase: "00-bug-triage"
plan: "05"
subsystem: "data-layer"
tags: ["bug-fix", "slug", "db", "project-session", "tdd"]
dependency_graph:
  requires: ["00-01", "00-03"]
  provides: ["slug-lookup", "get_project_by_slug"]
  affects: ["shared/db.py", "shared/project_session.py"]
tech_stack:
  added: []
  patterns: ["idempotent-alter-table-migration", "slug-auto-derive"]
key_files:
  created: ["tests/test_slug_infrastructure.py"]
  modified: ["shared/db.py", "shared/project_session.py"]
decisions:
  - "D-06: slug column added as TEXT NOT NULL DEFAULT '' to projects table in bootstrap()"
  - "D-07: get_project_by_slug added using parameterized WHERE slug = ? query (T-00-05-01 mitigated)"
  - "D-08: upsert_project auto-derives slug via C.slugify(meta.name) when meta.slug is empty"
metrics:
  duration: "5 minutes"
  completed: "2026-04-24"
  tasks_completed: 2
  files_modified: 3
---

# Phase 0 Plan 05: Slug Infrastructure Summary

**One-liner:** Added `slug TEXT NOT NULL DEFAULT ''` column to projects table with idempotent ALTER TABLE migration, auto-derive in `upsert_project`, `get_project_by_slug` lookup function, and `project_session` wired to use slug-based lookup.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| RED  | Failing tests for slug infrastructure | af1f260 | tests/test_slug_infrastructure.py |
| 1    | Add slug column, upsert_project, get_project_by_slug, _row_to_project | 10fe4f5 | shared/db.py, tests/test_slug_infrastructure.py |
| 2    | Update project_session.resolve() and refresh_md() to use get_project_by_slug | f1b641e | shared/project_session.py |

## What Was Done

### Task 1: db.py slug infrastructure (BUG-08)

Five changes made to `shared/db.py`:

1. **bootstrap() CREATE TABLE**: Added `slug TEXT NOT NULL DEFAULT ''` as second column (after `project_id`) in the `projects` CREATE TABLE statement.

2. **bootstrap() ALTER TABLE migration**: Added idempotent `ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''` after `executescript()`. Catches `sqlite3.OperationalError` silently for existing DBs that already have the column.

3. **_row_to_project()**: Added `slug=d.get("slug", "")` to the `ProjectMeta(...)` constructor so slug is read from DB rows.

4. **upsert_project()**: Added `if not meta.slug: meta.slug = C.slugify(meta.name)` auto-derive at the top. Added `:slug` to INSERT VALUES list (position 2, matching CREATE TABLE column order) and `slug=excluded.slug` to ON CONFLICT DO UPDATE SET. Added `"slug": meta.slug` to params dict.

5. **get_project_by_slug()**: New function added after `get_project()`. Uses parameterized query `WHERE slug = ?` (T-00-05-01 mitigated per threat model).

6. **Module docstring**: Updated Projects API section to include `get_project_by_slug(conn, slug) → ProjectMeta | None`.

### Task 2: project_session.py (BUG-04/EXTRA-01)

- `resolve()`: replaced `db.get_project(conn, slug)` with `db.get_project_by_slug(conn, slug)`
- `refresh_md()`: replaced `db.get_project(conn, slug)` with `db.get_project_by_slug(conn, slug)`

No stale `get_project(conn, slug)` calls remain.

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test) | af1f260 | PASS — all 5 tests failed for the right reasons |
| GREEN (feat) | 10fe4f5 | PASS — all 5 tests pass |
| REFACTOR | n/a | No refactor needed |

## Verification Results

```
grep -c "def get_project_by_slug" shared/db.py  → 1  ✓
grep -c "C.slugify" shared/db.py                → 1  ✓
grep -c "db.get_project_by_slug" shared/project_session.py  → 2  ✓
grep -c "db.get_project(conn, slug)" shared/project_session.py  → 0  ✓
grep -c "slug" shared/db.py                     → 13  ✓ (>6)
uv run pytest tests/test_slug_infrastructure.py → 5 passed  ✓
project_session import OK  ✓
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] sqlite-vec unavailable in WSL test environment**
- **Found during:** Task 1 TDD RED phase
- **Issue:** `db.get_db()` requires sqlite-vec extension (not authorized in WSL sandbox). Tests could not use `get_db()` fixture.
- **Fix:** Rewrote test fixture to use plain `sqlite3.connect(":memory:")` with manually crafted DDL matching the updated schema. Test 1 (bootstrap) exercises the ALTER TABLE idempotent migration path directly instead of calling `db.bootstrap()` end-to-end.
- **Files modified:** tests/test_slug_infrastructure.py
- **Commit:** 10fe4f5

## Known Stubs

None.

## Threat Flags

None — `get_project_by_slug` uses parameterized query `WHERE slug = ?` (T-00-05-01 mitigated). `C.slugify()` normalizes slugs to `[a-z0-9-]` only (T-00-05-02 accepted).

## Self-Check: PASSED
