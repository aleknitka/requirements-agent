# Phase 0: Bug Triage - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix all 9 cascading runtime bugs so every skill script imports cleanly and can be invoked without AttributeError, NameError, or TypeError. This phase is purely corrective — no new features, no new capabilities. The codebase should reach a state where `python -c "import shared.db"` runs clean and `uv run pytest` passes.

</domain>

<decisions>
## Implementation Decisions

### RequirementType — Model to str Enum Conversion (BUG-05)
- **D-01:** Convert `RequirementType` from `Pydantic BaseModel` (with `code`, `name`, `description` fields) to a `str` Enum where values are the 3-letter codes (BUS, FUN, NFR, etc.). This fixes `db.py` which treats it as a str Enum (`RequirementType(d["req_type"])`, `.value`, etc.).
- **D-02:** Keep the 34-item metadata list but rename it — currently `REQUIREMENT_TYPES: list[RequirementType]` becomes a list of `RequirementTypeMeta` (NamedTuple or dataclass with `code`, `name`, `description`). The new str Enum replaces the old BaseModel; `RequirementTypeMeta` is a separate metadata structure for future reporting/UI use.
- **D-03:** `RequirementIn.req_type` defaults to `RequirementType.FUN` (Functional). The previous default was `RequirementArea.CORE` which doesn't exist.

### RequirementArea — Remove Undefined Symbol (BUG-05)
- **D-04:** `RequirementArea` is referenced in `models.py` (`make_req_id`, `RequirementIn` type annotation) but never defined. Remove all references. `make_req_id` in `models.py` (module-level function) should also be removed — `_make_req_id` in `db.py` is the canonical version (and will be simplified to not use `.id_prefix`).

### fret_statement / fret_fields — Remove from Phase 0 (BUG-06)
- **D-05:** Remove `fret_statement: Optional[str]` and `fret_fields: Optional[dict]` from `RequirementIn` and `RequirementRow` entirely in Phase 0. Do not add them to the SQLite schema. Phase 3 (FRET Refinement) will introduce these fields properly alongside the FRET validator, `refine.py apply`, and the full formalisation protocol. Keeping dead fields with no consumer in Phase 0 is premature.

### slug Column and Project Lookup API (BUG-08)
- **D-06:** Add `slug TEXT UNIQUE NOT NULL DEFAULT ''` column to `projects` table in `bootstrap()`. Use `ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''` after the `CREATE TABLE IF NOT EXISTS` to handle existing DBs.
- **D-07:** Add `get_project_by_slug(conn: sqlite3.Connection, slug: str) -> Optional[ProjectMeta]` alongside existing `get_project(conn, project_id)`. Callers (especially `init.py`) should use `get_project_by_slug`.
- **D-08:** Slug is auto-derived in `upsert_project()` — if `meta.slug` is empty, compute `C.slugify(meta.name)` before persisting. Callers do not need to set slug manually.

### Import Pattern — Standardise Across All Skills (BUG-02, BUG-03)
- **D-09:** All skill scripts must follow the `refine.py` pattern: `sys.path.insert(0, str(_ROOT / "shared"))` then `import db`, `import CONSTANTS as C`, `from models import ...` (no `shared.` prefix). `init.py` currently uses `import shared.CONSTANTS as C` and `import shared.db` — these break with the sys.path approach and must be corrected to `import CONSTANTS as C` and `import db`.

### db.py Public API Alignment (BUG-01, BUG-03, BUG-04)
- **D-10:** Remove `C.DB_PATH` as the default argument in `get_db()`. Signature becomes `get_db(path: str) -> sqlite3.Connection` — caller always provides the path. `C.DB_PATH` does not exist in `CONSTANTS.py` and should not be added (each project has its own DB via `C.db_path(slug)`).
- **D-11:** `init.py` calls `db.list_all_projects()` — the actual function is `list_projects(conn)`. All callers must be aligned to the real API.
- **D-12:** `_make_req_id` in `db.py` calls `req_type.id_prefix` — remove `.id_prefix` usage. After D-01, `RequirementType` is a str Enum so ID generation becomes `f"REQ-{req_type.value}-{uuid[:8].upper()}"`.

### report.py Rename (BUG-09)
- **D-13:** Rename `skills/status-report/scripts/report.py.py` → `skills/status-report/scripts/report.py`. The double extension was a filesystem error. No logic changes needed.

### refine.py Argument Order (BUG-07)
- **D-14:** Fix `refine.py apply` which calls `update_requirement(conn, req_id, changes)` — the actual signature is `update_requirement(conn, req_id, project_id, changes, changed_by, summary)`. Must align call site to pass all required args.

### Tests
- **D-15:** Replace `tests/test_init.py` with a new real-SQLite test file. No MagicMock. Use `tmp_path` fixture from pytest + real `sqlite3` connections.
- **D-16:** Test scope: full end-to-end CLI tests using subprocess invocations — `uv run python skills/new-project-initiation/scripts/init.py --help`, `uv run python skills/refine-requirements/scripts/refine.py --help`, `uv run python skills/status-report/scripts/report.py --help` — each must exit 0. Also include CRUD unit tests for the fixed `db.py` functions.

### Claude's Discretion
- Choice of NamedTuple vs dataclass for `RequirementTypeMeta` — either works; prefer NamedTuple for simplicity.
- Whether to add a `UNIQUE` constraint on `slug` in the `projects` table — yes, slugs should be unique since they're used as identifiers.
- Ordering of fixes within each file — apply all fixes to a file in one edit to minimise churn.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core shared modules (files being fixed)
- `shared/models.py` — RequirementType, RequirementIn, RequirementRow; RequirementArea undefined here
- `shared/db.py` — get_db, bootstrap, upsert_project, get_project, list_projects, insert_requirement, update_requirement; all bugs live here
- `shared/CONSTANTS.py` — slugify(), db_path(), project_dir(); C.DB_PATH does NOT exist

### Skill scripts (import pattern examples and callers)
- `skills/refine-requirements/scripts/refine.py` — CORRECT import pattern (use as template)
- `skills/new-project-initiation/scripts/init.py` — BROKEN import pattern (needs fixing); calls list_all_projects(), uses shared.db prefix
- `skills/status-report/scripts/report.py` — needs rename from report.py.py; check imports

### Tests
- `tests/test_init.py` — existing test file to be replaced

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `C.slugify(name)` in CONSTANTS.py — already implemented, use in `upsert_project()` for auto-slug
- `C.db_path(slug)` — returns `projects/<slug>/<slug>.db`, use as the argument to `get_db()`
- `refine.py` import block — correct pattern, copy for all other skill scripts

### Established Patterns
- All skill scripts resolve `_ROOT = Path(__file__).resolve().parents[3]` then `sys.path.insert(0, str(_ROOT / "shared"))` — this is the standard import bootstrap
- JSON serialisation in db.py uses `_j()` helper for lists/models — keep this pattern
- `conn.row_factory = sqlite3.Row` + WAL mode + foreign keys are set in `get_db()` — maintain

### Integration Points
- `bootstrap()` must handle both new and existing DBs safely (use `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ADD COLUMN` for new columns)
- All callers of `insert_requirement` pass `req_in.req_type` which after D-01 will be a str Enum — `req_type.value` still works as before

</code_context>

<specifics>
## Specific Ideas

- The ROADMAP already specifies exactly 7 fix plans (00-01 through 00-07) with clear file targets. Planner should map each plan to one or more decisions above.
- BUG-06 is now scoped to just adding the `slug` column + migration (not fret_statement/fret_fields — those are removed per D-05).
- The rename of report.py.py is a one-liner fix; plan 00-07 should bundle it with the test additions since they're both in the status-report skill.

</specifics>

<deferred>
## Deferred Ideas

- `fret_statement` and `fret_fields` in RequirementIn/RequirementRow — deferred to Phase 3 (FRET formalisation), where they will be introduced alongside the validator and refine.py apply fix.
- `update_requirement` updatable set expansion for FRET fields — deferred to Phase 3.
- Vector search (`vector_search()` function) — foundation in place, not exercised in v1. Not a bug, not touched in Phase 0.

</deferred>

---

*Phase: 00-bug-triage*
*Context gathered: 2026-04-22*
