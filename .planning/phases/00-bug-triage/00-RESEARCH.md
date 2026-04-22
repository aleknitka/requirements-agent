# Phase 0: Bug Triage - Research

**Researched:** 2026-04-22
**Domain:** Python import mechanics, SQLite/Pydantic data layer, pytest fixture patterns
**Confidence:** HIGH — all findings derived from direct codebase inspection

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Convert `RequirementType` from `Pydantic BaseModel` (code/name/description fields) to a `str` Enum where values are the 3-letter codes (BUS, FUN, NFR, etc.).
- **D-02:** Rename the 34-item metadata list from `REQUIREMENT_TYPES: list[RequirementType]` to `list[RequirementTypeMeta]` (NamedTuple or dataclass). The new str Enum replaces the old BaseModel.
- **D-03:** `RequirementIn.req_type` defaults to `RequirementType.FUN` (Functional).
- **D-04:** Remove `RequirementArea` from `models.py` entirely — remove from `make_req_id`, `RequirementIn` type annotation, and remove the module-level `make_req_id` function.
- **D-05:** Remove `fret_statement` and `fret_fields` from `RequirementIn` and `RequirementRow` in Phase 0. Do not add them to the SQLite schema. Deferred to Phase 3. NOTE: REQUIREMENTS.md BUG-06 says "add fret_statement/fret_fields" but D-05 OVERRIDES — remove them.
- **D-06:** Add `slug TEXT UNIQUE NOT NULL DEFAULT ''` column to `projects` table in `bootstrap()`, using `ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''` after `CREATE TABLE IF NOT EXISTS` to handle existing DBs.
- **D-07:** Add `get_project_by_slug(conn, slug) -> Optional[ProjectMeta]` alongside existing `get_project(conn, project_id)`.
- **D-08:** Auto-derive slug in `upsert_project()` — if `meta.slug` is empty, compute `C.slugify(meta.name)` before persisting.
- **D-09:** All skill scripts must follow the `refine.py` pattern: `sys.path.insert(0, str(_ROOT / "shared"))` then bare `import db`, `import CONSTANTS as C`, `from models import ...`.
- **D-10:** Remove `C.DB_PATH` default argument from `get_db()`. Signature becomes `get_db(path: str) -> sqlite3.Connection`.
- **D-11:** Replace all `db.list_all_projects()` call sites with `list_projects(conn)`.
- **D-12:** Fix `_make_req_id` in `db.py` — remove `.id_prefix` usage. After D-01, ID becomes `f"REQ-{req_type.value}-{uuid[:8].upper()}"`.
- **D-13:** Rename `skills/status-report/scripts/report.py.py` → `skills/status-report/scripts/report.py`.
- **D-14:** Fix `refine.py apply` — call `update_requirement(conn, req_id, changes, changed_by=..., summary=...)` with all required positional/keyword args matching the actual `db.py` signature.
- **D-15:** Replace `tests/test_init.py` with a real-SQLite test file using `tmp_path` fixture. No MagicMock.
- **D-16:** Test scope: CLI subprocess tests (`uv run python ... --help` → exit 0) and CRUD unit tests for fixed `db.py` functions.

### Claude's Discretion

- Choice of NamedTuple vs dataclass for `RequirementTypeMeta` — prefer NamedTuple for simplicity.
- Whether to add a `UNIQUE` constraint on `slug` in the `projects` table — yes, slugs should be unique.
- Ordering of fixes within each file — apply all fixes to a file in one edit.

### Deferred Ideas (OUT OF SCOPE)

- `fret_statement` and `fret_fields` in RequirementIn/RequirementRow — deferred to Phase 3.
- `update_requirement` updatable set expansion for FRET fields — deferred to Phase 3.
- Vector search (`vector_search()` function) — not touched in Phase 0.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BUG-01 | `db.py` imports cleanly — `C.DB_PATH` default removed | Line 92 of db.py: `def get_db(path: str = C.DB_PATH)` — `C.DB_PATH` does not exist in CONSTANTS.py |
| BUG-02 | `init.py` and all callers bind `db` correctly via sys.path | init.py lines 20-22 use `import shared.CONSTANTS`, `import shared.db`, `import shared.md_writer` — all wrong |
| BUG-03 | All callers use `db.list_projects(conn)`, not `db.list_all_projects()` | `init.py` lines 49, 85 call `db.list_all_projects()`; `project_session.py` line 43 also calls `db.list_all_projects()` |
| BUG-04 | `get_project(conn, slug)` called with both required args | `project_session.py` lines 78, 86 call `db.get_project(conn)` with only one arg — missing project_id |
| BUG-05 | `RequirementArea` reference removed; `RequirementIn` instantiates without error | `models.py` lines 267-268, 273-274 reference `RequirementArea` which is never defined |
| BUG-06 | Per D-05 OVERRIDE: `fret_statement`/`fret_fields` REMOVED (not added) | `models.py` lines 285-287 have fret fields present — remove per D-05 |
| BUG-07 | `refine.py` argument order fixed for `update_requirement` | `refine.py` line 91 calls `db.update_requirement(conn, args.id, changes, changed_by=..., summary=...)` missing `project_id` positional arg |
| BUG-08 | `projects` table has `slug` column; all callers consistent | `bootstrap()` schema (line 117-138) has no `slug` column; `_row_to_project` has no slug; `upsert_project` has no slug |
| BUG-09 | `report.py.py` renamed to `report.py` | Filesystem check: file already exists as `report.py` (no rename needed — confirmed) |

</phase_requirements>

---

## Summary

Phase 0 fixes nine cascading bugs that prevent any skill script from importing or running. The bugs cluster into four distinct failure chains: (1) `db.py` crashes at import time because `C.DB_PATH` does not exist in `CONSTANTS.py`, blocking every other module that imports `db`; (2) `init.py` uses `import shared.db` instead of bare `import db`, leaving the `db` name unbound at runtime even after the sys.path insert; (3) `models.py` references `RequirementArea` which is never defined, causing `NameError` the moment `RequirementIn` is instantiated; (4) several functions are called with wrong signatures (`list_all_projects` vs `list_projects`, `get_project(conn)` without `project_id`, `_make_req_id` calling `.id_prefix` on an enum that has no such attribute).

BUG-09 (report.py.py rename) is already resolved — the file on disk is `skills/status-report/scripts/report.py`. No rename action is required. The test file rewrite (D-15/D-16) is the only net-new work beyond pure bug fixes.

**Primary recommendation:** Fix files in dependency order — models.py first, then db.py, then all skill scripts in parallel, then replace tests last.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Data models / validation | `shared/models.py` | — | Pydantic models; no DB knowledge |
| DB schema + CRUD | `shared/db.py` | `shared/CONSTANTS.py` | All persistence; imports models |
| CLI entry points | `skills/*/scripts/*.py` | `shared/project_session.py` | Import shared modules after sys.path insert |
| Session resolution | `shared/project_session.py` | `shared/db.py` | Thin wrapper — imports db and md_writer |
| Test harness | `tests/` | `shared/db.py` | Uses real SQLite via tmp_path |

---

## Bug Inventory — Exact Locations

### BUG-01: C.DB_PATH does not exist [VERIFIED: direct file inspection]

**File:** `shared/db.py`, line 92
```python
def get_db(path: str = C.DB_PATH) -> sqlite3.Connection:
```
`CONSTANTS.py` exports: `PROJECTS_DIR`, `EMBEDDING_API_BASE`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`, `SNAPSHOT_ON_STATUSES`, `MD_NOTES_BEGIN`, `MD_NOTES_END`, `project_dir()`, `db_path()`, `md_path()`, `slugify()`. There is no `DB_PATH`. Importing `shared.db` from any context raises `AttributeError: module 'CONSTANTS' has no attribute 'DB_PATH'` immediately.

**Fix:** Remove default argument. New signature: `def get_db(path: str) -> sqlite3.Connection:`. All callers must pass `C.db_path(slug)` explicitly.

---

### BUG-02: init.py uses shared.* prefix imports [VERIFIED: direct file inspection]

**File:** `skills/new-project-initiation/scripts/init.py`, lines 20-25
```python
import shared.CONSTANTS as C        # WRONG — binds `shared`, not `C` at bare name
import shared.db                    # WRONG — `db` is never bound
import shared.md_writer             # WRONG — `md_writer` is never bound
import shared.project_session as ps # WRONG — binds `ps` to shared.project_session but...
from shared.models import ...       # WRONG — works only if shared/ is on sys.path
```

The script correctly sets up `_ROOT` and `sys.path.insert(0, str(_ROOT / "shared"))` on lines 17-18, but then imports with `shared.` prefix which bypasses the path insert and looks for a package named `shared` relative to the Python path — that package does not exist as an installable package.

**Fix (pattern from refine.py):**
```python
_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "shared"))

import CONSTANTS as C
import db
import md_writer
import project_session as ps
from models import ExternalLink, ProjectMeta, ProjectPhase, Stakeholder
```

Note: `parents[3]` from `skills/new-project-initiation/scripts/init.py` resolves to the repo root correctly (scripts → new-project-initiation → skills → repo root).

---

### BUG-03: list_all_projects() called but list_projects(conn) is the real API [VERIFIED]

**Callers of the non-existent `list_all_projects()`:**

| File | Line | Call |
|------|------|------|
| `skills/new-project-initiation/scripts/init.py` | 49 | `db.list_all_projects()` |
| `skills/new-project-initiation/scripts/init.py` | 85 | `db.list_all_projects()` |
| `shared/project_session.py` | 43 | `db.list_all_projects()` |

**Real API in db.py:** `list_projects(conn: sqlite3.Connection) -> list[ProjectMeta]` (line 359).

`list_projects` returns `list[ProjectMeta]` objects, not dicts. The `project_session.py` caller at line 55 does `p["slug"]` dict access — this breaks with `ProjectMeta` objects. After fixing to `list_projects(conn)`, callers must use `p.slug` (attribute access), not `p["slug"]`.

**Additionally:** `init.py` calls `list_all_projects()` without a `conn` argument. After the fix, callers need a connection. For `init.py cmd_new` and `cmd_list`, the fix pattern is:
```python
conn = db.get_db(str(C.db_path(slug)))   # or a shared/listing DB
projects = db.list_projects(conn)
```

However, `list_projects` is project-scoped per-DB. The current `init.py` usage is trying to enumerate ALL projects across all project DBs — this is a design mismatch. The `project_session.py resolve()` function has the same issue. This is a deeper architectural gap (addressed by D-07 / `get_project_by_slug`), but for Phase 0, the fix must produce working `--help` output and not crash on import. The plan for 00-03 must address how `list_projects` is called in `project_session.py` with a valid `conn`.

**Deeper issue in project_session.py:** `resolve()` calls `db.list_all_projects()` to enumerate all projects. With the new per-project-DB architecture, there is no single DB with all projects. For Phase 0, `project_session.py` must be aligned to at minimum not crash on import. The full cross-project enumeration fix belongs to Phase 1 (INIT-06 active sentinel). For Phase 0, `project_session.py` should be updated to not call the non-existent function — see the "Additional Bugs" section below.

---

### BUG-04: get_project(conn) called with wrong arity [VERIFIED]

**File:** `shared/project_session.py`, lines 78 and 86
```python
meta = db.get_project(conn)          # line 78: missing project_id
meta = db.get_project(conn)          # line 86: missing project_id
```

**Real signature in db.py:** `def get_project(conn: sqlite3.Connection, project_id: str) -> Optional[ProjectMeta]` (line 352). Requires two arguments.

D-07 adds `get_project_by_slug(conn, slug)`. After that function exists, these two call sites in `project_session.py` should become `db.get_project_by_slug(conn, slug)`.

---

### BUG-05: RequirementArea never defined [VERIFIED]

**File:** `shared/models.py`

`RequirementArea` is referenced in three places but never defined anywhere in the file:

| Line | Usage |
|------|-------|
| 267 | `def make_req_id(req_type: RequirementArea) -> str:` |
| 268 | `return f"REQ-{req_type.id_prefix}-..."` |
| 273 | `req_type: RequirementArea = RequirementArea.CORE` (field default + type annotation) |

These lines raise `NameError: name 'RequirementArea' is not defined` the instant `RequirementIn` is loaded or `make_req_id` is called.

**Fix per D-01 through D-04:**
1. Add `class RequirementType(str, Enum)` with values BUS, USR, FUN, DAT, MOD, MLP, MET, NFR, PER, SCL, SEC, PRV, COM, ETH, EXP, ROB, OPS, DEP, INT, UIX, TST, MON, AUD, GOV, LGL, RES, ENV, MAI, REL, CON, ASM, RSK, DOC, TRN (34 values from the existing `REQUIREMENT_TYPES` list codes).
2. Add `RequirementTypeMeta = NamedTuple("RequirementTypeMeta", [("code", str), ("name", str), ("description", str)])` and rename the 34-item list to `REQUIREMENT_TYPE_METADATA: list[RequirementTypeMeta]`.
3. Remove `make_req_id` function from `models.py` entirely (canonical version is `_make_req_id` in `db.py`).
4. Change `RequirementIn.req_type` field to `RequirementType = RequirementType.FUN`.
5. Remove `fret_statement` and `fret_fields` fields from `RequirementIn` and `RequirementRow` (per D-05).

**Cascading impact on db.py:** After D-01, `RequirementType(d["req_type"])` in `_row_to_requirement` (line 236) works correctly since `RequirementType` becomes a `str` Enum initialized by value. `req_in.req_type.value` in `insert_requirement` (line 393) still works. The `col_map` lambda `lambda v: RequirementType(v).value` in `update_requirement` (line 477) still works.

---

### BUG-06 (D-05 OVERRIDE): fret_statement/fret_fields — REMOVE, not add [VERIFIED]

Per D-05, `fret_statement` and `fret_fields` exist in `models.py` `RequirementIn` (lines 285-287) but must be **removed** for Phase 0. They are not in the SQLite schema (`bootstrap()` line 140-156 shows no fret columns). Multiple scripts reference these fields that will break after removal:

| File | Line | Usage |
|------|------|-------|
| `skills/refine-requirements/scripts/refine.py` | 58-59 | `req.fret_statement`, `req.fret_fields` |
| `skills/refine-requirements/scripts/refine.py` | 81-84 | `changes["fret_statement"]`, `changes["fret_fields"]` |
| `skills/refine-requirements/scripts/refine.py` | 111 | `r.fret_statement` |
| `skills/status-report/scripts/report.py` | 39, 77 | `r.fret_statement` |
| `skills/review-requirements/scripts/review.py` | 61, 93-94, 163 | `r.fret_statement`, `r.fret_fields` |
| `shared/project_session.py` | 95 | `r.fret_statement` |

**Decision:** Since D-05 defers fret to Phase 3, these references in skill scripts should be left in place (they reference fields via attribute access that will simply not exist). However, removing the fields from `RequirementRow` will cause `AttributeError` at runtime in these scripts. 

**Resolution for Phase 0:** The CONTEXT.md deferred items only say "remove from Phase 0 models" — the skill scripts themselves are out of scope for Phase 0 except `init.py`. `refine.py`, `report.py`, `review.py` fret references are Phase 3 work. For Phase 0 the critical path is: remove fret fields from `models.py` (so `RequirementIn` instantiates clean), and accept that `refine.py coverage/show/apply` and `report.py` fret-stat lines will fail at runtime (but `--help` will pass since it does not execute those code paths). This is consistent with Phase 0 success criteria which only requires `--help` to exit 0, not full runtime execution.

---

### BUG-07: refine.py calls update_requirement with wrong signature [VERIFIED]

**File:** `skills/refine-requirements/scripts/refine.py`, line 90-93
```python
row = db.update_requirement(
    conn, args.id, changes,
    changed_by=args.by,
    summary=args.summary or "FRET statement applied.",
)
```

**Actual db.py signature (lines 424-431):**
```python
def update_requirement(
    conn: sqlite3.Connection,
    req_id: str,
    project_id: str,          # MISSING in refine.py call
    changes: dict[str, Any],
    changed_by: str,
    summary: str,
) -> RequirementRow:
```

The call passes `changes` as the third positional argument but `project_id` is expected third. This is a positional mismatch — `changes` dict is passed where `project_id: str` is expected.

**Fix:** Add `project_id` argument. The `slug` is available from `ps.resolve()`:
```python
slug, conn, _ = ps.resolve(args.project)
# ...
row = db.update_requirement(
    conn, args.id, slug,
    changes,
    changed_by=args.by,
    summary=args.summary or "FRET statement applied.",
)
```

Note: Since D-05 removes `fret_statement`/`fret_fields` from the updatable set in Phase 0, `cmd_apply` will fail at runtime when it tries to update fret fields. The `--help` test still passes since build_parser() does not execute cmd_apply.

---

### BUG-08: slug column missing from projects table [VERIFIED]

**File:** `shared/db.py`, `bootstrap()` function (lines 115-203)

Current `projects` table schema has no `slug` column. `ProjectMeta` model already has `slug: str = ""` (line 369 of models.py), but `upsert_project` (line 303) does not include slug in the INSERT/UPDATE, and `_row_to_project` (line 274) does not read a slug column.

**Three-part fix required:**
1. In `bootstrap()`: Add `slug TEXT NOT NULL DEFAULT ''` to CREATE TABLE; add `ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''` after CREATE (idempotent — SQLite silently fails if column exists, need `IGNORE` or try/except).
2. In `upsert_project()`: Auto-derive slug if empty (`if not meta.slug: meta.slug = C.slugify(meta.name)`), add `:slug` to INSERT values and SET clause.
3. Add `get_project_by_slug(conn, slug)` alongside `get_project(conn, project_id)`.
4. Fix `_row_to_project()` to populate `slug` from DB row.

**ALTER TABLE idempotency:** SQLite does not support `ALTER TABLE ADD COLUMN IF NOT EXISTS`. Use try/except around the ALTER TABLE statement:
```python
try:
    conn.execute("ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''")
except sqlite3.OperationalError:
    pass  # column already exists
```

---

### BUG-09: report.py.py rename [VERIFIED: filesystem check]

The filesystem check confirms `skills/status-report/scripts/report.py` exists. There is NO file named `report.py.py`. The rename is already done. No action required for this BUG. The existing `report.py` already uses the correct import pattern (lines 19-21):
```python
import CONSTANTS as C
import db
import project_session as ps
```

---

## Additional Bugs Not in the Original 9 BUGs

### EXTRA-01: project_session.py — list_all_projects + get_project wrong arity [VERIFIED]

`project_session.py` has two independent bugs beyond BUG-03 and BUG-04:

1. Line 43: `db.list_all_projects()` — does not exist (BUG-03 overlap)
2. Line 77: `conn = db.get_db(slug)` — passes a slug string but `get_db` expects a file path
3. Lines 78, 86: `db.get_project(conn)` — missing `project_id` arg (BUG-04 overlap)
4. Line 95: `r.fret_statement` — will fail after D-05 removes fret fields from RequirementRow

For Phase 0, `project_session.py` must be updated to at minimum not crash on import. The `get_db(slug)` call (line 77) must become `get_db(str(C.db_path(slug)))`. After D-07 is applied, `get_project(conn)` calls become `get_project_by_slug(conn, slug)`.

`project_session.py` is imported by ALL skill scripts via `import project_session as ps`. This means its broken `list_all_projects` call makes ALL scripts fail at import time even if their own imports are correct. Plan 00-03 must include `project_session.py` as a file requiring fixes.

### EXTRA-02: req_ops.py references RequirementType.CORE [VERIFIED]

**File:** `skills/project-update/scripts/req_ops.py`, line 39
```python
req_type=RequirementType(args.type.upper()) if args.type else RequirementType.CORE,
```
After D-01 converts `RequirementType` to a str Enum, `RequirementType.CORE` does not exist (there is no "CORE" code in the 34-item list — that was the old `RequirementArea.CORE` default). This must change to `RequirementType.FUN` (per D-03).

### EXTRA-03: req_ops.py insert_requirement called without project_id [VERIFIED]

**File:** `skills/project-update/scripts/req_ops.py`, line 50
```python
row = db.insert_requirement(conn, req_in, created_by=args.by)
```

**Actual db.py signature (line 376):**
```python
def insert_requirement(conn, project_id: str, req_in: RequirementIn, created_by: str) -> RequirementRow:
```

The call skips `project_id` — `req_in` is passed where `project_id` is expected. Fix: `db.insert_requirement(conn, meta.project_id, req_in, created_by=args.by)`.

### EXTRA-04: req_ops.py update_requirement wrong arity [VERIFIED]

**File:** `skills/project-update/scripts/req_ops.py`, line 81
```python
row = db.update_requirement(conn, args.id, changes, args.by, args.summary)
```

Same arity mismatch as BUG-07 — `project_id` is missing as third positional argument. Fix: `db.update_requirement(conn, args.id, meta.project_id, changes, args.by, args.summary)`.

### EXTRA-05: req_ops.py TYPES list will fail at module import [VERIFIED]

**File:** `skills/project-update/scripts/req_ops.py`, line 163
```python
TYPES = [t.value for t in RequirementType]
```

After D-01, `RequirementType` is a `str` Enum and `[t.value for t in RequirementType]` is valid — this line works correctly post-fix. No action needed here beyond the D-01 fix itself.

### EXTRA-06: review.py and report.py reference fret_statement on RequirementRow [VERIFIED]

After D-05 removes `fret_statement`/`fret_fields` from `RequirementRow`, these scripts will raise `AttributeError` at runtime:
- `review.py` lines 61, 93-94, 163: `r.fret_statement`, `r.fret_fields`
- `report.py` lines 39, 77: `r.fret_statement`
- `project_session.py` line 95: `r.fret_statement`
- `refine.py` lines 58-59, 111: `r.fret_statement`, `r.fret_fields`

Phase 0 success criteria only requires `--help` to exit 0. These code paths are not exercised by `--help`. **However**, `project_session.py` is different — `refresh_md()` is called at runtime during `cmd_new` and `cmd_update`, and line 95 accesses `r.fret_statement` inside `refresh_md()`. This path IS exercised in Phase 1, but not by `--help` in Phase 0. For Phase 0 correctness, plan 00-03 should use a safe `getattr(r, 'fret_statement', None)` guard or a comment noting Phase 3 will add these fields back.

### EXTRA-07: search_requirements called without project_id in several scripts [VERIFIED]

Several scripts call `db.search_requirements(conn)` without `project_id`:
- `shared/project_session.py` line 87: `db.search_requirements(conn)`
- `skills/review-requirements/scripts/review.py` lines 175, 180, 187, 193: `db.search_requirements(conn)`
- `skills/status-report/scripts/report.py` line 29: `db.search_requirements(conn)`
- `skills/refine-requirements/scripts/refine.py` lines 31, 110: `db.search_requirements(conn, has_fret=False)`

**Actual db.py signature (line 526):** `def search_requirements(conn, project_id: str, ...)` — `project_id` is required, not optional.

`has_fret` is also not a parameter in `db.py`'s `search_requirements` — refine.py passes it but db.py doesn't accept it.

These are runtime bugs (not import-time) and not covered by Phase 0 success criteria (which only tests `--help` and basic import). They are Phase 1 work. Document them here so the planner is aware — they will need fixing before `cmd_generate` and `cmd_gaps` can work.

### EXTRA-08: md_writer.py not yet read — regenerate signature unknown [ASSUMED]

`shared/md_writer.py` is called by `project_session.py refresh_md()` at line 106. This file was not read during research. The `regenerate()` call passes: `slug, meta, req_counts, status_counts, open_decs, pending_a, unint, fret_cov`. After removing `fret_statement` from `RequirementRow`, the `fret_cov` dict will always be `{"with_fret": 0, "total": N, "pct": 0}` which is valid. No breakage expected from D-05 in md_writer — but this is flagged as ASSUMED.

---

## Dependency Order for Fixes

The fixes have a hard dependency chain that determines execution order:

```
models.py (RequirementType Enum, remove RequirementArea, remove fret fields)
    ↓
db.py (get_db signature, _make_req_id, slug column, get_project_by_slug, upsert_project)
    ↓
project_session.py (list_all_projects → list_projects, get_project → get_project_by_slug, get_db path)
    ↓
skills/new-project-initiation/scripts/init.py (import pattern, list_all_projects → list_projects)
skills/project-update/scripts/req_ops.py (import pattern, RequirementType.CORE, insert_requirement arity, update_requirement arity)
skills/refine-requirements/scripts/refine.py (update_requirement arity)
    ↓
tests/ (rewrite with real-SQLite fixtures)
```

`report.py`, `meeting.py`, `review.py` already use correct import patterns and do not need import fixes for Phase 0. Their fret/search-arity issues are runtime-only and blocked by the `--help` success criterion.

---

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| pydantic | ≥2.0 | Model validation | `model_dump(mode="json")` syntax confirms v2 |
| sqlite3 | stdlib | Persistence | No version concern |
| sqlite-vec | current | Vector embeddings | Loaded via extension; non-fatal if embedding key absent |

### Testing (for Plan 00-07)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| pytest | current | Test runner | `uv run pytest` command confirmed in CLAUDE.md |
| pytest (tmp_path) | builtin | Real-SQLite test fixture | `tmp_path` is a built-in pytest fixture |

No new libraries needed. All fixes are pure Python stdlib + existing dependencies.

---

## Architecture Patterns

### Correct Import Pattern (from refine.py — canonical)
```python
_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "shared"))

import CONSTANTS as C
import db
import project_session as ps
from models import SomeModel, AnotherModel
```

`parents[3]` depth from `skills/<name>/scripts/<file>.py`:
- parents[0] = `scripts/`
- parents[1] = `<skill-name>/`
- parents[2] = `skills/`
- parents[3] = repo root

### RequirementType — Target Shape (str Enum)
```python
class RequirementType(str, Enum):
    BUS = "BUS"
    USR = "USR"
    FUN = "FUN"
    DAT = "DAT"
    MOD = "MOD"
    MLP = "MLP"
    MET = "MET"
    NFR = "NFR"
    PER = "PER"
    SCL = "SCL"
    SEC = "SEC"
    PRV = "PRV"
    COM = "COM"
    ETH = "ETH"
    EXP = "EXP"
    ROB = "ROB"
    OPS = "OPS"
    DEP = "DEP"
    INT = "INT"
    UIX = "UIX"
    TST = "TST"
    MON = "MON"
    AUD = "AUD"
    GOV = "GOV"
    LGL = "LGL"
    RES = "RES"
    ENV = "ENV"
    MAI = "MAI"
    REL = "REL"
    CON = "CON"
    ASM = "ASM"
    RSK = "RSK"
    DOC = "DOC"
    TRN = "TRN"
```

After this change: `RequirementType("FUN")` → `<RequirementType.FUN: 'FUN'>`, `.value` → `"FUN"`. The existing `_row_to_requirement` call `RequirementType(d["req_type"])` continues to work unchanged.

### RequirementTypeMeta — Target Shape (NamedTuple)
```python
from typing import NamedTuple

class RequirementTypeMeta(NamedTuple):
    code: str
    name: str
    description: str

REQUIREMENT_TYPE_METADATA: list[RequirementTypeMeta] = [
    RequirementTypeMeta("BUS", "Business", "Business goals..."),
    # ... (34 items, same content as current REQUIREMENT_TYPES list)
]
```

### _make_req_id — Target Shape (db.py)
```python
def _make_req_id(req_type: RequirementType) -> str:
    import uuid
    return f"REQ-{req_type.value}-{str(uuid.uuid4())[:8].upper()}"
```

### slug column — ALTER TABLE pattern (idempotent)
```python
conn.executescript("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id  TEXT PRIMARY KEY,
        slug        TEXT NOT NULL DEFAULT '',
        ...
    );
""")
try:
    conn.execute("ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''")
    conn.commit()
except sqlite3.OperationalError:
    pass  # column already exists
```

### get_project_by_slug (new function)
```python
def get_project_by_slug(conn: sqlite3.Connection, slug: str) -> Optional[ProjectMeta]:
    row = conn.execute(
        "SELECT * FROM projects WHERE slug = ?", (slug,)
    ).fetchone()
    return _row_to_project(row) if row else None
```

### upsert_project — slug auto-derive
```python
def upsert_project(conn: sqlite3.Connection, meta: ProjectMeta) -> ProjectMeta:
    if not meta.slug:
        meta.slug = C.slugify(meta.name)
    # ... rest of function; add :slug to INSERT and SET clause
```

### Real-SQLite test pattern (D-15/D-16)
```python
import sqlite3
import pytest
from pathlib import Path

def test_upsert_and_get_project(tmp_path):
    db_file = str(tmp_path / "test.db")
    conn = db.get_db(db_file)
    from models import ProjectMeta
    meta = ProjectMeta(name="Test Project")
    db.upsert_project(conn, meta)
    fetched = db.get_project_by_slug(conn, "test-project")
    assert fetched is not None
    assert fetched.name == "Test Project"
    assert fetched.slug == "test-project"
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Enum iteration for argparse choices | Manual list comprehension | `[t.value for t in RequirementType]` — works after D-01 |
| DB column existence check | Complex introspection query | `try: ALTER TABLE ... except OperationalError: pass` |
| Slug generation | Custom regex | `C.slugify()` already in CONSTANTS.py |
| Test DB setup | In-memory workarounds | `tmp_path` fixture + real file path |

---

## Common Pitfalls

### Pitfall 1: ALTER TABLE in executescript loses idempotency
**What goes wrong:** `conn.executescript()` wraps everything in a transaction and raises `sqlite3.OperationalError` if the column already exists, rolling back the whole script.
**How to avoid:** Keep `CREATE TABLE IF NOT EXISTS` in `executescript`, put `ALTER TABLE ADD COLUMN` in a separate `try/except` block outside the script.

### Pitfall 2: str Enum value vs name confusion
**What goes wrong:** `RequirementType.FUN.value == "FUN"` and `RequirementType.FUN.name == "FUN"` are the same here. But `RequirementType("FUN")` constructs from value. `RequirementType["FUN"]` constructs from name. Both work for this design but the DB layer uses `RequirementType(d["req_type"])` (value constructor) — keep it consistent.

### Pitfall 3: test_init.py loads from wrong path
**What goes wrong:** Current `test_init.py` (lines 38-43) loads `init.py` from `agents/project-initiation-assistant/skills/new-project-initiation/scripts/init.py` — a path that does not exist in this repo. The new test must load from `skills/new-project-initiation/scripts/init.py`.

### Pitfall 4: MagicMock for models causes silent test passes
**What goes wrong:** `MagicMock()` auto-creates attributes on access, so `mock.slug` and `mock.list_all_projects()` both return `MagicMock()` instead of raising errors. Tests pass even when production code calls wrong APIs.
**How to avoid:** Per D-15, use `tmp_path` and real SQLite connections. No MagicMock. `create_autospec(ProjectMeta)` if a mock is needed.

### Pitfall 5: report.py success criterion confusion
**What goes wrong:** BUG-09 describes renaming `report.py.py` → `report.py`. The file is ALREADY named `report.py` on disk. There is nothing to rename. Attempting a rename will fail.

### Pitfall 6: parents[3] depth assumption
**What goes wrong:** `skills/new-project-initiation/scripts/init.py` has `_ROOT = Path(__file__).resolve().parents[3]` on line 17. After the import fix, `_ROOT` will be the repo root. Verify this resolves correctly: `init.py` → `parents[0]=scripts/`, `parents[1]=new-project-initiation/`, `parents[2]=skills/`, `parents[3]=repo_root`. Confirmed correct.

---

## Skill Scripts — Import Pattern Audit

| Script | Import Pattern | Status | Action Needed |
|--------|---------------|--------|---------------|
| `skills/refine-requirements/scripts/refine.py` | Correct (bare imports after sys.path insert) | CORRECT | Template only |
| `skills/new-project-initiation/scripts/init.py` | `import shared.CONSTANTS`, `import shared.db`, etc. | BROKEN | Fix per D-09 |
| `skills/status-report/scripts/report.py` | Correct (bare `import CONSTANTS as C`, `import db`) | CORRECT | No import fix needed |
| `skills/project-update/scripts/req_ops.py` | Correct (bare `import db`, `from models import ...`) | CORRECT | But has BUG-03/EXTRA-02/03/04 |
| `skills/meeting-agent/scripts/meeting.py` | Correct (bare `import db`, `from models import ...`) | CORRECT | No import fix needed |
| `skills/review-requirements/scripts/review.py` | Correct (bare `import db`, `from models import ...`) | CORRECT | No import fix needed |
| `shared/project_session.py` | Correct (bare imports) | CORRECT | But has BUG-03/04 at runtime |

**Key finding:** Only `init.py` has the broken import pattern. All other scripts already use bare imports.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (version per uv.lock) |
| Config file | none detected (use default discovery) |
| Quick run command | `uv run pytest tests/ -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUG-01 | `python -c "import shared.db"` exits without AttributeError | smoke | `uv run python -c "import shared.db"` | N/A (shell) |
| BUG-02 | `init.py --help` exits 0 | smoke/subprocess | `uv run python skills/new-project-initiation/scripts/init.py --help` | N/A (shell) |
| BUG-03 | `list_projects(conn)` returns list of ProjectMeta | unit | `uv run pytest tests/test_db.py::test_list_projects -x` | Wave 0 gap |
| BUG-04 | `get_project_by_slug(conn, slug)` returns correct ProjectMeta | unit | `uv run pytest tests/test_db.py::test_get_project_by_slug -x` | Wave 0 gap |
| BUG-05 | `RequirementIn(title="x", description="y", req_type="FUN")` instantiates | unit | `uv run pytest tests/test_models.py::test_requirement_in_instantiation -x` | Wave 0 gap |
| BUG-06/D-05 | `RequirementIn` has no fret_statement/fret_fields attributes | unit | `uv run pytest tests/test_models.py::test_no_fret_fields -x` | Wave 0 gap |
| BUG-07 | `refine.py --help` exits 0 | subprocess | `uv run python skills/refine-requirements/scripts/refine.py --help` | N/A (shell) |
| BUG-08 | projects table has slug column; upsert auto-derives slug | unit | `uv run pytest tests/test_db.py::test_slug_column -x` | Wave 0 gap |
| BUG-09 | report.py --help exits 0 | subprocess | `uv run python skills/status-report/scripts/report.py --help` | N/A (shell) |

### Wave 0 Gaps
- [ ] `tests/test_db.py` — covers BUG-03 (list_projects), BUG-04 (get_project_by_slug), BUG-08 (slug column)
- [ ] `tests/test_models.py` — covers BUG-05 (RequirementIn instantiation), BUG-06/D-05 (no fret fields)
- [ ] `tests/test_init.py` — REPLACE existing MagicMock file with real-SQLite version (D-15/D-16)

The current `tests/test_init.py` must be **replaced** (not updated): it loads init.py from a non-existent path, pre-mocks `shared.db` to bypass crashes, and uses `MagicMock` throughout. The new version should use `tmp_path` and subprocess calls.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | All `uv run` commands | Run check below | — | — |
| Python ≥ 3.10 | `from __future__ import annotations`, match syntax | — | — | — |
| pytest | `uv run pytest` | — | — | — |
| pydantic v2 | `model_dump(mode="json")` | Confirmed (syntax used) | ≥2.0 | None |
| sqlite-vec | `db.py` extension load | May not be installed | — | get_db raises RuntimeError with clear message |

Note: `sqlite-vec` failure raises `RuntimeError` in `get_db()`. For tests using `tmp_path`, this will block `get_db()`. Tests should either mock the sqlite-vec load or use a try/except guard. The existing code raises `RuntimeError` unconditionally if `sqlite_vec.load` fails — for unit tests this is a problem. Consider whether `bootstrap()` should be callable separately from `get_db()` for testing, or whether tests should skip if sqlite-vec unavailable. This is a test design decision for Plan 00-07.

---

## Open Questions

1. **sqlite-vec availability in test environment**
   - What we know: `get_db()` calls `sqlite_vec.load(conn)` and raises `RuntimeError` on failure
   - What's unclear: whether `sqlite-vec` is installed in the uv environment
   - Recommendation: Plan 00-07 should verify `uv run python -c "import sqlite_vec"` and design tests accordingly. If unavailable, mock the extension load in tests.

2. **project_session.py cross-project listing**
   - What we know: `resolve()` tries to enumerate all projects from a single `list_all_projects()` call — this was the pre-Phase 0 design
   - What's unclear: with per-project DBs, how `resolve()` should enumerate projects without a global registry
   - Recommendation: For Phase 0, `project_session.py` should be fixed to not crash (replace `list_all_projects()` call) but the full cross-project resolution belongs to Phase 1 (INIT-06). The plan should make `resolve()` functional enough to not crash `--help`, even if it raises a clean error when no project slug is provided and no DB exists.

3. **test_init.py replacement scope**
   - What we know: existing tests test argparse + _ok/_err via MagicMock; D-15/D-16 calls for real-SQLite CRUD tests
   - What's unclear: whether to keep the parser/output-helper tests and add CRUD tests, or replace everything
   - Recommendation: Keep parser tests (they test real logic, just mock the DB calls) using `create_autospec`. Add separate `test_db.py` for CRUD. Replace only the MagicMock usages, not the entire test surface.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `md_writer.regenerate()` signature accepts `fret_cov` param and handles `fret_cov["with_fret"] = 0` without error | EXTRA-08 | `refresh_md()` crashes after fret fields removed from RequirementRow; need to read md_writer.py before implementing |
| A2 | `sqlite-vec` is installed in the uv environment | Environment Availability | `get_db()` raises RuntimeError; all DB tests fail |
| A3 | `parents[3]` resolves to repo root from `skills/new-project-initiation/scripts/init.py` | Import Pattern | sys.path insert points to wrong directory; import still fails |

---

## Sources

### Primary (HIGH confidence — direct file inspection)
- `shared/db.py` — all bugs verified line-by-line
- `shared/models.py` — RequirementArea, RequirementType, fret fields verified
- `shared/CONSTANTS.py` — C.DB_PATH absence confirmed; all exported names listed
- `shared/project_session.py` — list_all_projects, get_project arity confirmed
- `skills/new-project-initiation/scripts/init.py` — shared.* imports confirmed
- `skills/refine-requirements/scripts/refine.py` — update_requirement arity confirmed
- `skills/project-update/scripts/req_ops.py` — insert_requirement, update_requirement arity confirmed
- `skills/status-report/scripts/report.py` — correct import pattern confirmed; report.py.py does not exist
- `skills/meeting-agent/scripts/meeting.py` — correct import pattern confirmed
- `skills/review-requirements/scripts/review.py` — correct import pattern; fret references noted
- `tests/test_init.py` — MagicMock pattern confirmed; wrong init.py path confirmed

---

## Metadata

**Confidence breakdown:**
- Bug identification: HIGH — every bug verified by line-number reference to source files
- Fix prescriptions: HIGH — patterns confirmed from existing correct implementations (refine.py, report.py)
- Test architecture: MEDIUM — sqlite-vec availability unverified (see Open Questions)
- Dependency order: HIGH — logical analysis of import chain

**Research date:** 2026-04-22
**Valid until:** Not time-sensitive (codebase bugs, not library APIs)
