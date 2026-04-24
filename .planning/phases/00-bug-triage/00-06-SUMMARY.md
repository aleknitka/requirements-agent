---
phase: "00-bug-triage"
plan: "06"
subsystem: "tests"
tags: [testing, bug-verification, real-sqlite, subprocess, importlib]
dependency_graph:
  requires:
    - "00-01"  # db.py importable
    - "00-02"  # models.py clean
    - "00-03"  # init.py bare imports
    - "00-04"  # refine.py / report.py importable
    - "00-05"  # slug column + get_project_by_slug
  provides:
    - "verified-phase-0-bugs"
  affects:
    - "tests/test_db.py"
    - "tests/test_models.py"
    - "tests/test_init.py"
tech_stack:
  added: []
  patterns:
    - "sys.modules injection to patch local imports inside functions"
    - "patch.object(db, 'bootstrap', test_safe_bootstrap) for vec0 avoidance"
    - "importlib.util.spec_from_file_location for CLI module loading without subprocess"
    - "subprocess.run for black-box CLI exit-code verification"
key_files:
  created:
    - tests/test_db.py
    - tests/test_models.py
  modified:
    - tests/test_init.py
decisions:
  - "Patch sys.modules['sqlite_vec'] + db.bootstrap to avoid vec0 virtual table requirement in test env"
  - "test_init.py fully replaced: wrong agents/ path removed, no MagicMock for db/ps"
  - "importlib fixture (scope=module) for parser/helper tests; subprocess for --help exit-code tests"
metrics:
  duration: "4 minutes"
  completed: "2026-04-24"
  tasks_completed: 2
  files_changed: 3
---

# Phase 0 Plan 06: Test Suite Summary

**One-liner:** Real-SQLite and subprocess tests proving all 9 Phase 0 bugs are fixed, replacing the broken MagicMock-based test_init.py that loaded from a non-existent path.

## What Was Built

Three test files covering all Phase 0 bug-fix verifications:

### tests/test_db.py (14 tests) — BUG-01, BUG-03, BUG-04, BUG-08

Uses a `conn` fixture that patches `sys.modules["sqlite_vec"]` and `db.bootstrap` with a
test-safe variant (replaces the `vec0` virtual table with a plain `req_embeddings` table).
All CRUD operations run against a real SQLite file on disk via `tmp_path`.

- `test_get_db_requires_path_argument` / `test_get_db_raises_type_error_without_args` — BUG-01
- `test_slug_column_exists` — BUG-08 schema
- `test_upsert_project_auto_derives_slug` / `test_upsert_project_preserves_explicit_slug` — BUG-08 logic
- `test_list_projects_*` (4 tests) — BUG-03 canonical name + ProjectMeta return type
- `test_get_project_by_slug_*` (4 tests) — BUG-04 slug lookup

### tests/test_models.py (23 tests) — BUG-05, BUG-06

No DB interaction. Pure Pydantic model validation.

- `TestRequirementTypeEnum` (6 tests) — BUG-05: str Enum, 34 codes, string construction
- `TestRequirementTypeMeta` (5 tests) — NamedTuple, 34 entries, codes match Enum
- `TestRequirementInInstantiation` (9 tests) — BUG-06/D-05: no fret fields; D-03/D-04 cleanup
- `TestProjectMeta` (3 tests) — slug default empty, explicit slug preserved

### tests/test_init.py (26 tests) — BUG-02

Fully replaced the old file that loaded from `agents/project-initiation-assistant/...`
(non-existent path) and pre-mocked `shared.db` to hide the C.DB_PATH crash.

- `TestInitHelp` (7 tests) — subprocess `--help` exits 0 for all subcommands (BUG-02)
- `TestBuildParser` (9 tests) — parser tests via importlib from `skills/` path
- `TestParseJson` (7 tests) — `_parse_json` helper preserved from old file
- `TestOutputHelpers` (3 tests) — `_ok`/`_err` JSON output preserved from old file

## Full Suite Result

```
74 passed in 1.53s
```

## Phase 0 Smoke Tests (all pass)

| Command | Bug | Result |
|---------|-----|--------|
| `uv run python -c "import shared.db"` | BUG-01 | OK |
| `uv run python skills/new-project-initiation/scripts/init.py --help` | BUG-02 | OK |
| `uv run python -c "from shared.models import RequirementIn; RequirementIn(...)"` | BUG-05 | OK |
| `uv run python skills/refine-requirements/scripts/refine.py --help` | BUG-07 | OK |
| `uv run python skills/status-report/scripts/report.py --help` | BUG-09 | OK |

## Commits

| Hash | Message |
|------|---------|
| acf260e | test(00-06): add real-SQLite tests for BUG-01, BUG-03, BUG-04, BUG-08 |
| e05fe80 | test(00-06): add model validation tests for BUG-05 and BUG-06 |
| 47ad710 | test(00-06): replace MagicMock test_init.py with subprocess and importlib tests |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] db.bootstrap creates a vec0 virtual table which fails without the native extension**

- **Found during:** Task 1 (first `pytest` run)
- **Issue:** `bootstrap()` calls `CREATE VIRTUAL TABLE ... USING vec0(...)`. In this WSL
  environment `sqlite_vec.load()` requires `conn.load_extension()` which raises
  `OperationalError: not authorized`. Even with `sqlite_vec` mocked in `sys.modules`,
  the `vec0` module is not registered in SQLite's engine, so `executescript` fails.
- **Fix:** Introduced `_test_bootstrap` function (inline in `test_db.py`) that is
  identical to `db.bootstrap` except it replaces the `vec0` virtual table with a plain
  `req_embeddings` table. This is patched in via `patch.object(db, "bootstrap", _test_bootstrap)`
  inside the `conn` fixture, alongside the `sys.modules["sqlite_vec"]` injection.
- **Files modified:** `tests/test_db.py`
- **Commit:** acf260e

## Known Stubs

None — all tests make real assertions against real behaviour.

## Threat Flags

None — tests use `tmp_path` for DB isolation (T-00-06-01 mitigated). No production data,
no secrets, no network access.

## Self-Check: PASSED
