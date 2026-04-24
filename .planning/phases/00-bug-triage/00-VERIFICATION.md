---
phase: "00-bug-triage"
verified: "2026-04-23T12:00:00Z"
status: human_needed
score: 5/5
overrides_applied: 0
deferred:
  - truth: "init.py cmd_new and cmd_list can be invoked without AttributeError"
    addressed_in: "Phase 1"
    evidence: "Phase 1 success criteria: 'init.py new runs end-to-end, creating a project DB and PROJECT.md'. Plan 00-03 explicitly states: 'Calls to db.list_all_projects() in cmd_new (line 49) and cmd_list (line 85) will become runtime errors, but --help does not execute those functions and the Phase 0 success criterion is --help exits 0. Those call sites will need fixing in Phase 1 (INIT-06).'"
  - truth: "BUG-06 fret_statement/fret_fields columns added to requirements table"
    addressed_in: "Phase 3"
    evidence: "D-05 decision deferred fret fields to Phase 3 (FRET Refinement). Fields were removed in Phase 0 rather than added; Phase 3 will add them back with proper FRET protocol. REQUIREMENTS.md BUG-06 description ('fret_statement + fret_fields columns added') is misaligned with the D-05 decision but the intent (unblock RequirementIn instantiation) is satisfied."
human_verification:
  - test: "Run skills/status-report/scripts/report.py generate --project <slug> after creating a project"
    expected: "Command produces a status report without AttributeError or NameError; verifies the full runtime path beyond --help"
    why_human: "BUG-09 smoke test only verified --help exit 0. The generate/save subcommands load project_session and db at runtime. Need a real project slug to verify."
---

# Phase 0: Bug Triage Verification Report

**Phase Goal:** Fix all 9 cascading runtime bugs so every skill script imports cleanly and can be invoked without AttributeError, NameError, or TypeError.
**Verified:** 2026-04-23T12:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `python -c "import shared.db"` runs without any error from repo root | VERIFIED | Smoke-tested: prints `import OK`, exits 0. `get_db` has no default arg; `C.DB_PATH` removed; `_make_req_id` uses `.value`. |
| 2 | `uv run python skills/new-project-initiation/scripts/init.py --help` exits 0 with usage output | VERIFIED | Smoke-tested: exits 0, prints `usage: init.py [-h] {new,list,update}`. Bare imports confirmed (no `shared.` prefix). |
| 3 | `uv run pytest` passes with real-SQLite tests (no MagicMock auto-attribute) | VERIFIED | 74 tests pass in 1.82s. Covers BUG-01/03/04/08 via real SQLite (test_db.py, test_slug_infrastructure.py), BUG-05/06 via model tests (test_models.py), BUG-02 via subprocess CLI tests (test_init.py). |
| 4 | `RequirementIn(title="x", description="y", req_type="FUN")` instantiates without NameError or AttributeError | VERIFIED | Smoke-tested. `RequirementType` is a `str` Enum with 34 codes. `RequirementArea` removed. `fret_statement`/`fret_fields` removed. `req_type` default is `RequirementType.FUN`. |
| 5 | `uv run python skills/status-report/scripts/report.py --help` exits 0 (imports clean) | VERIFIED | Smoke-tested: exits 0, prints `usage: report.py [-h] [--project PROJECT] {generate,save}`. `report.py.py` (double extension) confirmed absent; `report.py` is the only file present. |

**Score:** 5/5 roadmap success criteria verified

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | `init.py cmd_new` and `cmd_list` call `db.list_all_projects()` — will raise AttributeError at runtime | Phase 1 | Phase 1 goal: "`init.py new` runs end-to-end". Plan 00-03 explicitly deferred these caller paths; `--help` succeeds as the Phase 0 criterion. |
| 2 | BUG-06: `fret_statement`/`fret_fields` columns not added to `requirements` table | Phase 3 | D-05 decision: fret fields deferred to Phase 3 (FRET Refinement). Fields were removed in Phase 0 to unblock instantiation. Phase 3 will add them back with proper protocol. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `shared/db.py` | Core SQLite persistence layer with no C.DB_PATH default | VERIFIED | `def get_db(path: str)` — no default. `_make_req_id` uses `req_type.value`. `list_projects` present; `list_all_projects` absent. `get_project_by_slug` added. `slug` column in CREATE TABLE + ALTER TABLE migration. |
| `shared/models.py` | RequirementType str Enum, RequirementIn clean | VERIFIED | `class RequirementType(str, Enum)` with 34 codes. `RequirementTypeMeta(NamedTuple)` with 34-item `REQUIREMENT_TYPE_METADATA`. No `RequirementArea`, no `make_req_id`, no `fret_statement`/`fret_fields`. |
| `shared/project_session.py` | Clean imports, uses get_project_by_slug | VERIFIED | Bare imports (`import CONSTANTS as C; import db`). `resolve()` uses `db.get_project_by_slug(conn, slug)`. `refresh_md()` uses `db.get_project_by_slug(conn, slug)`. `getattr(r, 'fret_statement', None)` guard present. No `list_all_projects` call. |
| `skills/new-project-initiation/scripts/init.py` | Bare imports, --help exits 0 | VERIFIED (partial) | Bare imports confirmed. `--help` exits 0. **Known gap:** `cmd_new` line 49 and `cmd_list` line 85 still call `db.list_all_projects()`. These raise `AttributeError` when those subcommands are invoked (deferred to Phase 1). |
| `skills/refine-requirements/scripts/refine.py` | --help exits 0, correct db call signatures | VERIFIED | `--help` exits 0. `update_requirement(conn, args.id, slug, changes, ...)` — slug as interim project_id per D-14. All `search_requirements` calls pass `meta.project_id`. `fret_statement`/`fret_fields` references removed. |
| `skills/project-update/scripts/req_ops.py` | --help exits 0, RequirementType.FUN default, correct db arities | VERIFIED | `--help` exits 0. `RequirementType.FUN` as default. `db.insert_requirement(conn, meta.project_id, req_in, ...)` correct. `db.update_requirement(conn, args.id, meta.project_id, ...)` correct. `has_fret=` kwarg removed. |
| `skills/status-report/scripts/report.py` | --help exits 0 (BUG-09) | VERIFIED | `report.py` exists and `--help` exits 0. `report.py.py` (double extension) does not exist. |
| `tests/test_db.py` | Real-SQLite CRUD tests covering BUG-01/03/04/08 | VERIFIED | 14 tests, all pass. Covers `get_db` signature, slug column, `upsert_project` auto-derive, `list_projects`, `get_project_by_slug`. |
| `tests/test_models.py` | Model validation tests covering BUG-05/06 | VERIFIED | 23 tests, all pass. Covers `RequirementType` str Enum (34 codes), `RequirementTypeMeta` NamedTuple, `RequirementIn` instantiation, no fret fields, no `RequirementArea`, no `make_req_id`. |
| `tests/test_init.py` | Subprocess CLI tests replacing MagicMock | VERIFIED | 26 tests, all pass. Uses subprocess for `--help` exit-code verification. Uses importlib for parser/helper tests. Wrong `agents/project-initiation-assistant/` path is gone. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `shared/db.py` | `shared/CONSTANTS.py` | `import CONSTANTS as C` | WIRED | Line 47: `import CONSTANTS as C`. `C.slugify()` called in `upsert_project`. |
| `shared/db.py` | `shared/models.py` | `from models import RequirementType` | WIRED | Lines 48-53: imports `RequirementType`, `RequirementIn`, `RequirementRow`, etc. `RequirementType(d["req_type"])` usage compatible with str Enum. |
| `shared/project_session.py` | `shared/db.py` | `db.get_project_by_slug(conn, slug)` | WIRED | Lines 49, 57: `db.get_project_by_slug(conn, slug)` in both `resolve()` and `refresh_md()`. No stale `db.get_project(conn, slug)` or `db.list_all_projects()` calls. |
| `skills/new-project-initiation/scripts/init.py` | `shared/db.py` | bare import after sys.path insert | WIRED | Line 18: `sys.path.insert(0, str(_ROOT / "shared"))`. Line 21: `import db`. `--help` exercises import chain successfully. |
| `skills/refine-requirements/scripts/refine.py` | `shared/db.py` | `db.update_requirement(conn, args.id, slug, ...)` | WIRED | Line 79: `db.update_requirement(conn, args.id, slug, changes, ...)`. Six positional args matching db.py signature. |
| `skills/project-update/scripts/req_ops.py` | `shared/db.py` | `db.insert_requirement(conn, meta.project_id, req_in, ...)` | WIRED | Line 50: `db.insert_requirement(conn, meta.project_id, req_in, created_by=args.by)` — all 4 positional args present. |
| `tests/test_db.py` | `shared/db.py` | `db.get_db` via patched bootstrap | WIRED | Line 153: `c = db.get_db(str(tmp_path / "test.db"))` with patched sqlite_vec and bootstrap. All 14 CRUD tests execute against real SQLite. |
| `tests/test_init.py` | `skills/new-project-initiation/scripts/init.py` | `subprocess.run` | WIRED | `TestInitHelp` class uses subprocess with correct `INIT_PATH = REPO_ROOT / "skills" / "new-project-initiation" / "scripts" / "init.py"`. |

### Data-Flow Trace (Level 4)

Not applicable — Phase 0 is a bug-fix phase. No new data rendering components were added. All artifacts are persistence/CLI utilities, not components that render dynamic data to users.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `import shared.db` exits 0 (BUG-01) | `uv run python -c "import shared.db; print('import OK')"` | `import OK` | PASS |
| `init.py --help` exits 0 (BUG-02) | `uv run python skills/new-project-initiation/scripts/init.py --help` | Usage printed, exit 0 | PASS |
| `RequirementIn` instantiates without error (BUG-05) | `uv run python -c "from shared.models import RequirementIn; req = RequirementIn(title='x', description='y', req_type='FUN'); print('OK')"` | `OK` | PASS |
| `refine.py --help` exits 0 (BUG-07) | `uv run python skills/refine-requirements/scripts/refine.py --help` | Usage printed, exit 0 | PASS |
| `report.py --help` exits 0 (BUG-09) | `uv run python skills/status-report/scripts/report.py --help` | Usage printed, exit 0 | PASS |
| Full test suite passes | `uv run pytest tests/` | 74 passed in 1.82s | PASS |
| `req_ops.py --help` exits 0 | `uv run python skills/project-update/scripts/req_ops.py --help` | Usage printed, exit 0 | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| BUG-01 | 00-01, 00-06 | `db.py` imports cleanly — `C.DB_PATH` default removed | SATISFIED | `get_db(path: str)` has no default. `import shared.db` exits 0. |
| BUG-02 | 00-03, 00-06 | `init.py` uses bare imports | SATISFIED | `init.py` uses `import CONSTANTS as C; import db; import md_writer; import project_session as ps`. `--help` exits 0. |
| BUG-03 | 00-01, 00-03 | All callers use `db.list_projects(conn)` not `db.list_all_projects()` | PARTIAL | `db.py`, `project_session.py`, `refine.py`, `req_ops.py` all use correct API. `init.py` `cmd_new`/`cmd_list` still call `list_all_projects()` — deferred to Phase 1. |
| BUG-04 | 00-05, 00-03 | `get_project_by_slug(conn, slug)` used throughout | SATISFIED | `project_session.resolve()` and `refresh_md()` both use `db.get_project_by_slug(conn, slug)`. Function exists in db.py. |
| BUG-05 | 00-01, 00-02 | `RequirementArea` removed; `RequirementIn` instantiates without error | SATISFIED | `RequirementArea` absent from models.py. `RequirementIn(title='x', description='y', req_type='FUN')` succeeds. |
| BUG-06 | 00-01, 00-02 | `fret_statement`/`fret_fields` removed from `RequirementIn` (D-05 decision) | SATISFIED (scope change) | Fields removed per D-05. REQUIREMENTS.md description says "columns added" but D-05 decided to remove them instead, deferring FRET to Phase 3. Both `fret_statement` and `fret_fields` absent from models.py. |
| BUG-07 | 00-04 | `refine.py` `update_requirement` arity fixed | SATISFIED | `update_requirement(conn, args.id, slug, changes, changed_by=args.by, summary=...)` — 6 positional args. `search_requirements` calls pass `meta.project_id`. |
| BUG-08 | 00-05 | `projects` table has `slug` column; callers consistent | SATISFIED | `slug TEXT NOT NULL DEFAULT ''` in CREATE TABLE. ALTER TABLE migration present. `_row_to_project` reads slug. `upsert_project` auto-derives via `C.slugify`. `get_project_by_slug` function present. |
| BUG-09 | 00-04 (indirectly), 00-06 | `report.py.py` renamed to `report.py` | SATISFIED | `skills/status-report/scripts/report.py` exists. `report.py.py` does not exist. `report.py --help` exits 0. |

Note: REQUIREMENTS.md shows BUG-06 as unchecked (`[ ]`) — the requirement text says "columns added" but D-05 decided to remove them for Phase 0. The implementation (removal) satisfies the actual bug (NameError on instantiation) even though it diverges from the requirement text. This is a documentation alignment gap, not a functional gap.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `skills/new-project-initiation/scripts/init.py` | 49, 85 | `db.list_all_projects()` — function does not exist | Warning | `cmd_new` and `cmd_list` will raise `AttributeError` at runtime. `--help` unaffected. Explicitly deferred to Phase 1. |
| `skills/refine-requirements/scripts/refine.py` | 79 | `slug` passed as `project_id` to `update_requirement` | Warning | Semantically wrong (slug is human-readable, project_id is UUID). Documented as interim D-14 decision. No current data corruption because `update_requirement` does not validate project_id consistency. |
| `shared/project_session.py` | 77 | `md_writer.regenerate(slug, meta, ...)` called without None-guard on `meta` | Warning | If `get_project_by_slug` returns None (project not found), `meta` is None and `md_writer.regenerate` will raise AttributeError. Only reachable if a project is deleted between write and refresh. Documented in 00-REVIEW.md as WR-04. |
| `shared/db.py` | 316 | `now = _now()` assigned but unused in `upsert_project` | Info | Dead code. No correctness impact. |

### Human Verification Required

#### 1. Runtime invocation of report.py subcommands

**Test:** Create a test project then run `uv run python skills/status-report/scripts/report.py generate --project <slug>`
**Expected:** Command produces a status report JSON output without AttributeError or NameError; exits 0
**Why human:** BUG-09 verification only confirmed `--help` exits 0. The `generate` and `save` subcommands import `project_session` and invoke `ps.resolve()` which calls `db.get_db()` (requires sqlite-vec), making automated verification in this environment impractical. A human with a working sqlite-vec install can verify the full runtime path.

### Gaps Summary

No structural gaps block the phase goal. All 5 ROADMAP success criteria are met:

1. `import shared.db` — clean
2. `init.py --help` — exits 0
3. `uv run pytest` — 74 tests pass
4. `RequirementIn` instantiation — clean
5. `report.py --help` — exits 0

Two items that appear gap-like are confirmed deferred by the roadmap:
- `init.py cmd_new/cmd_list` calling `list_all_projects()` is explicitly in Phase 1 scope (INIT-01)
- FRET fields removal vs REQUIREMENTS.md "columns added" description is a D-05 design decision, with Phase 3 adding them back properly

One human verification item remains: confirming `report.py generate` works at runtime (beyond `--help`). This does not block Phase 1 but should be checked before Phase 4 (REPORT-01) work begins.

---

_Verified: 2026-04-23T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
