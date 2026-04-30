# Phase 1: Project Initialisation - Research

**Researched:** 2026-04-30
**Domain:** Python CLI scaffold, SQLite schema, single-project model
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** One project per agent instance. No slugs, no `.active` sentinel, no multi-project selection. All code that references slugs, `PROJECTS_DIR/<slug>/`, or `--project <slug>` is removed in this phase.
- **D-02:** Single project directory: `project/` at the repo root. Structure: `project/project.db`, `project/PROJECT.md`, `project/logs/`, `project/notes/`. Override path via `PROJECT_DIR` env var (absolute path only).
- **D-03:** `CONSTANTS.py` loses all slug-based helpers (`project_dir(slug)`, `db_path(slug)`, `md_path(slug)`, `slugify()`). Replaced with flat constants: `PROJECT_DIR`, `DB_PATH`, `MD_PATH`.
- **D-04:** `project_session.resolve(slug_or_name)` is replaced with a simple `get_project_conn()` helper that opens the single DB. No slug argument, no discovery loop.
- **D-05:** All CLIs (`refine`, `req-ops`, `review`, `report`, `meeting`, `db`) lose their `--project <slug>` global flag. They always operate on the single project.
- **D-06:** Command: `uv run init-project setup`. Creates `project/` directory tree, bootstraps `project/project.db`, writes `config/project.yaml` with setup choices.
- **D-07:** On second run (project/ already exists): guard + abort. Print: `"Project already initialised. Use 'init-project reset' to start fresh."` Exit non-zero. Do NOT implement `reset` in this phase.
- **D-08:** Setup questions asked interactively during `init-project setup`:
  1. sqlite-vec? — Enable vector embeddings. Default: no.
  2. .gitignore entries? — Offer to append `project/logs/`, `project/notes/`, `project/*.db` to `.gitignore`. Checkbox-style.
  3. OpenTelemetry? — Enable tracing (implementation deferred). Default: no. Stores flag only.
- **D-09:** sqlite-vec = no → skip silently. Do not create vec0 virtual table. All semantic search commands return empty results without error.
- **D-10:** sqlite-vec = yes → create vec0 virtual table and embeddings table as part of `bootstrap()`.
- **D-11:** Setup choices persisted to `config/project.yaml`. Keys: `sqlite_vec: bool`, `otel_enabled: bool`. `.gitignore` entries written directly — not recorded in config.
- **D-12:** DB schema re-evaluated as research task before planning (see Proposed Schema section below).
- **D-13:** Researcher must produce proposed schema — this is the primary research deliverable.
- **D-14:** Setup config file: `config/project.yaml`. Read at startup by any module that needs to check sqlite-vec or OTel status. Must be present after `init-project setup` completes.

### Claude's Discretion

None noted in CONTEXT.md.

### Deferred Ideas (OUT OF SCOPE)

- `init-project reset` — named in D-07 guard message, implement in a later phase
- OpenTelemetry tracing implementation — flag captured in Phase 1 config, implementation is a future phase
- `init-project update` — update setup config after initial setup; future phase
- Multi-project support — explicitly out of scope for v1
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INIT-01 | Single project directory `project/` created at repo root | D-02; directory scaffold pattern in existing `project_dir()` — adapt without slug |
| INIT-02 | `project/project.db` bootstrapped via `init-project setup` | D-06; existing `get_db()` + `bootstrap()` reused with flat `DB_PATH` |
| INIT-03 | `config/project.yaml` written with `sqlite_vec` and `otel_enabled` keys | D-11/D-14; PyYAML 6.0.3 available; write pattern from `config/default.yaml` |
| INIT-04 | Interactive setup questions (sqlite-vec, .gitignore, OTel) | D-08; click.confirm() and click.prompt() available in click 8.3.3 |
| INIT-05 | Guard: second run prints message and exits non-zero | D-07; check `PROJECT_DIR.exists()` before any work |
| INIT-06 | `--project` flag removed from all CLIs; `project_session.resolve()` replaced with `get_project_conn()` | D-04/D-05; 7 modules affected (see Scope of Change section) |
</phase_requirements>

---

## Summary

Phase 1 converts the requirements-agent from a multi-project, slug-based model to a single-project model. The two primary bodies of work are: (1) rewriting `CONSTANTS.py`, `project_session.py`, and `init_project.py` for flat paths, and (2) removing the `--project <slug>` global flag from all seven CLI modules that currently call `project_session.resolve()`.

The secondary work — and the primary *research* deliverable — is re-evaluating the SQLite schema. The current schema already has no `project_id` foreign keys in the operational tables (`requirements`, `updates`). The `minutes` table carries a `project_id` FK in the test bootstrap SQL but not in the canonical `schema.py`. The `projects` table is retained in simplified form. The proposed schema is documented below with explicit answers to each of D-12's five questions.

The interactive setup uses `click.confirm()` for yes/no questions — click 8.3.3 is already a declared dependency. PyYAML is available in the uv environment (6.0.3) but is not in `pyproject.toml` dependencies; it must be added. The setup command is a new `setup` subcommand replacing `new`/`list`/`update`.

**Primary recommendation:** Implement in four atomic plans: (1) CONSTANTS + project_session, (2) init_project setup command + config/project.yaml, (3) schema + bootstrap refactor, (4) remove --project from all seven CLI modules + delete slug infrastructure test file.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Directory scaffold (`project/`) | CLI / init layer | Filesystem | `init-project setup` is the sole creator; no other code should mkdir |
| DB bootstrap | `db/connection.py` `bootstrap()` | Schema DDL in `db/schema.py` | Pattern already established; keep the two-file split |
| Setup config (`config/project.yaml`) | `init_project.py` cmd_setup() | `CONSTANTS.py` (path) | Written once at setup; read by db/connection and any module checking sqlite-vec |
| Interactive prompts | `init_project.py` cmd_setup() | click.confirm/prompt | No other module should prompt interactively |
| Project connection | `project_session.py` (new `get_project_conn()`) | `CONSTANTS.py` `DB_PATH` | All CLI modules call this one function; replaces the 7-way `ps.resolve()` pattern |
| `.gitignore` patching | `init_project.py` cmd_setup() | — | Idempotent line-by-line append; no other code touches .gitignore |

---

## Proposed DB Schema (Research Deliverable — D-12/D-13)

This section answers all five schema questions from D-12.

### Question 1: Is a `projects` table still needed?

**Yes, retain it.** The `projects` table stores the project name, objective, phase, owner, and other metadata that downstream skills (FRET, reporting, audit) will read. The DB is not self-describing without it. However, the `singleton` structural guard (already present in the current schema) is sufficient to enforce the one-project invariant without any application-layer checks.

**Columns to retain:** `project_id`, `singleton`, `name`, `code`, `phase`, `objective`, `business_case`, `success_criteria`, `out_of_scope`, `project_owner`, `sponsor`, `stakeholders`, `start_date`, `target_date`, `actual_end_date`, `external_links`, `status_summary`, `status_updated_at`, `created_at`, `updated_at`.

**Columns to drop:** `slug` — the single-project model has no concept of slugs. The `slug` column was added specifically for multi-project path derivation (D-08 from Phase 00-05). In the single-project model the project name is used for display only; no filesystem slug is needed. Removing `slug` also removes the dependency on `C.slugify()` from `db/projects.py`.

### Question 2: Can `project_id` foreign keys be dropped from all tables?

**Yes. And they already are in the canonical schema.** Inspection of `db/schema.py` confirms:

- `requirements` table: no `project_id` column. [VERIFIED: src/requirements_agent_tools/db/schema.py lines 51–66]
- `updates` table: no `project_id` column. [VERIFIED: src/requirements_agent_tools/db/schema.py lines 79–94]
- `minutes` table: no `project_id` column. [VERIFIED: src/requirements_agent_tools/db/schema.py lines 97–113]

The only place `project_id` appears in `schema.py` is as the PRIMARY KEY of the `projects` table itself and in a comment. The per-DB singleton model already made FKs redundant — every row in the DB implicitly belongs to the single project.

**Exception:** `test_db.py` line 103 and `test_slug_infrastructure.py` lines 55 and 95 contain a `project_id TEXT NOT NULL REFERENCES projects(project_id)` column in their local bootstrap SQL. These test-local schema snippets are stale relative to the canonical schema and must be updated when the test files are rewritten.

### Question 3: Are `meeting_minutes`, `decisions`, `action_items` still in scope for v1?

**Deferred to the user for confirmation — but the current schema already collapses these.** The current `schema.py` has a single `minutes` table with `decisions` and `action_items` as JSON columns (not separate tables). There are no separate `decisions` or `action_items` tables in the canonical schema. [VERIFIED: src/requirements_agent_tools/db/schema.py]

The `meeting-agent` skill and its `meeting.py` CLI are already implemented. Dropping the `minutes` table would break the meeting skill. **Recommendation:** retain `minutes` as-is (no `project_id` FK needed — already absent). No schema change required here.

### Question 4: What columns are actually dead weight?

| Table | Dead-weight column | Reason | Action |
|-------|-------------------|--------|--------|
| `projects` | `slug` | Single-project model; no slug-based path derivation | **DROP** |
| `projects` | `code` | Not used by any skill in v1 scope (Phases 1–5) | **Retain** — lightweight, may be populated during elicitation |
| `projects` | `business_case`, `success_criteria`, `out_of_scope`, `stakeholders`, `external_links` | Not queried in Phases 1–5; populated during elicitation | **Retain** — schema forward-compatibility |
| `requirements` | `predecessors`, `dependencies`, `external_links` | Not queried in Phases 1–5 | **Retain** — schema forward-compatibility |
| `updates` | `full_snapshot` | Only used by SNAPSHOT_ON_STATUSES (Phase 5 audit) | **Retain** — Phase 5 depends on it |
| Reference tables (`requirement_types`, `requirement_statuses`, etc.) | — | Seeded on bootstrap; used for FK validation and UI | **Retain all** |

**Net schema change from this audit:** Drop `slug` column from `projects`.

### Question 5: What indexes are needed?

Current indexes in `schema.py` are appropriate. No additions needed for Phase 1. [VERIFIED: src/requirements_agent_tools/db/schema.py]

| Index | Table | Columns | Keep? |
|-------|-------|---------|-------|
| `idx_projects_singleton` | projects | singleton | YES — enforces one-project structural guard |
| `idx_req_status` | requirements | status | YES — queried by every listing |
| `idx_req_type` | requirements | req_type | YES — queried by type filters |
| `idx_req_priority` | requirements | priority | YES — queried by priority filters |
| `idx_upd_entity` | updates | (entity_type, entity_id) | YES — queried on every audit lookup |

No new indexes needed for Phase 1 scope.

### Proposed Schema (Canonical DDL for Phase 1)

```sql
-- ── Projects ──────────────────────────────────────────────────────────
-- One row per DB. singleton UNIQUE index enforces the structural guard.
-- slug column REMOVED (single-project model; no slug-based path derivation).
CREATE TABLE IF NOT EXISTS projects (
    project_id        TEXT PRIMARY KEY,
    singleton         INTEGER NOT NULL DEFAULT 1 CHECK (singleton = 1),
    name              TEXT NOT NULL,
    code              TEXT,
    phase             TEXT NOT NULL DEFAULT 'discovery',
    objective         TEXT NOT NULL DEFAULT '',
    business_case     TEXT NOT NULL DEFAULT '',
    success_criteria  TEXT NOT NULL DEFAULT '[]',
    out_of_scope      TEXT NOT NULL DEFAULT '[]',
    project_owner     TEXT,
    sponsor           TEXT,
    stakeholders      TEXT NOT NULL DEFAULT '[]',
    start_date        TEXT,
    target_date       TEXT,
    actual_end_date   TEXT,
    external_links    TEXT NOT NULL DEFAULT '[]',
    status_summary    TEXT NOT NULL DEFAULT '',
    status_updated_at TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_singleton ON projects(singleton);

-- ── Requirements ──────────────────────────────────────────────────────
-- Unchanged from current schema.
CREATE TABLE IF NOT EXISTS requirements (
    id             TEXT PRIMARY KEY,
    req_type       TEXT NOT NULL DEFAULT 'CORE',
    title          TEXT NOT NULL,
    description    TEXT NOT NULL DEFAULT '',
    status         TEXT NOT NULL DEFAULT 'open',
    priority       TEXT NOT NULL DEFAULT 'medium',
    owner          TEXT,
    stakeholders   TEXT NOT NULL DEFAULT '[]',
    predecessors   TEXT NOT NULL DEFAULT '[]',
    dependencies   TEXT NOT NULL DEFAULT '[]',
    external_links TEXT NOT NULL DEFAULT '[]',
    tags           TEXT NOT NULL DEFAULT '[]',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_req_status   ON requirements(status);
CREATE INDEX IF NOT EXISTS idx_req_type     ON requirements(req_type);
CREATE INDEX IF NOT EXISTS idx_req_priority ON requirements(priority);

-- ── Vec virtual table — conditional on sqlite_vec setup choice ────────
-- Created in bootstrap() only when config/project.yaml sqlite_vec = true.
-- When sqlite_vec = false, this block is skipped entirely.
CREATE VIRTUAL TABLE IF NOT EXISTS req_embeddings
USING vec0(
    requirement_id TEXT PRIMARY KEY,
    embedding      FLOAT[{EMBEDDING_DIM}]
);

-- ── Updates (change log) ──────────────────────────────────────────────
-- Unchanged from current schema.
CREATE TABLE IF NOT EXISTS updates (
    id             TEXT PRIMARY KEY,
    entity_type    TEXT NOT NULL CHECK (entity_type IN ('requirement', 'project_md')),
    entity_id      TEXT NOT NULL,
    changed_at     TEXT NOT NULL,
    changed_by     TEXT NOT NULL,
    summary        TEXT NOT NULL DEFAULT '',
    diffs          TEXT NOT NULL DEFAULT '[]',
    full_snapshot  TEXT
);

CREATE INDEX IF NOT EXISTS idx_upd_entity ON updates(entity_type, entity_id);

-- ── Minutes ───────────────────────────────────────────────────────────
-- Unchanged from current schema (no project_id FK — already absent).
CREATE TABLE IF NOT EXISTS minutes (
    id                      TEXT PRIMARY KEY,
    title                   TEXT NOT NULL,
    source                  TEXT NOT NULL DEFAULT 'other',
    source_url              TEXT,
    occurred_at             TEXT NOT NULL,
    logged_at               TEXT NOT NULL,
    logged_by               TEXT NOT NULL,
    attendees               TEXT NOT NULL DEFAULT '[]',
    summary                 TEXT NOT NULL DEFAULT '',
    raw_notes               TEXT NOT NULL DEFAULT '',
    decisions               TEXT NOT NULL DEFAULT '[]',
    action_items            TEXT NOT NULL DEFAULT '[]',
    integrated_into_status  INTEGER NOT NULL DEFAULT 0,
    integrated_at           TEXT
);

-- ── Reference / lookup tables (enum catalogues) ───────────────────────
-- Unchanged from current schema.
CREATE TABLE IF NOT EXISTS requirement_types (
    code TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS requirement_statuses (value TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS requirement_priorities (value TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS project_phases (value TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS meeting_sources (value TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS decision_statuses (value TEXT PRIMARY KEY);
```

**Key changes from current `schema.py`:**
- `projects.slug` column removed
- `req_embeddings` virtual table creation made conditional (split SCHEMA_SQL into two parts: base + vec extension)
- All `project_id` FKs in other tables: already absent in canonical schema; no change needed

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| argparse | stdlib | CLI argument parsing | Already used in `init_project.py`; consistent with rest of package |
| click | 8.3.3 | Interactive prompts (`click.confirm`, `click.prompt`) | Already declared dependency; provides clean yes/no and checkbox prompts |
| PyYAML | 6.0.3 (in venv) | Read/write `config/project.yaml` | Already loadable in uv env; must be added to `pyproject.toml` |
| sqlite3 | stdlib | DB persistence | Core of existing data layer |
| loguru | 0.7.3 | Structured logging | Already used throughout package |
| pydantic | 2.13.3 | Model validation | `ProjectMeta` and all models |

**Version verification:** [VERIFIED: pyproject.toml + `uv run python -c "import yaml; print(yaml.__version__)"` → 6.0.3]

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib.Path | stdlib | Path manipulation | All path operations use Path, not string concatenation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `click.confirm` | `input()` + manual parsing | click.confirm handles edge cases (Ctrl-C, default display, stderr-vs-stdout); prefer click |
| PyYAML `yaml.safe_load/safe_dump` | `tomllib` (stdlib 3.11+) | YAML matches existing `config/default.yaml` pattern; TOML would be inconsistent |

**Installation (PyYAML addition to pyproject.toml):**
```bash
uv add pyyaml
```

---

## Scope of Change

### Files Being Deleted / Fully Rewritten

| File | Action | Reason |
|------|--------|--------|
| `tests/test_slug_infrastructure.py` | **DELETE** | Tests slug column, `get_project_by_slug`, `slugify` — all removed |
| `src/requirements_agent_tools/CONSTANTS.py` | **REWRITE** | Replace slug helpers with flat `PROJECT_DIR`, `DB_PATH`, `MD_PATH` |
| `src/requirements_agent_tools/project_session.py` | **REWRITE** | Replace `resolve(slug_or_name)` with `get_project_conn()` |
| `src/requirements_agent_tools/init_project.py` | **REWRITE** | Replace `cmd_new/cmd_list/cmd_update` with `cmd_setup()`; remove all metadata args |
| `tests/test_init.py` | **REWRITE** | All tests reference `cmd_new`, `--project`, `update` subcommand — entirely obsolete |

### Files Updated (Surgical Changes)

| File | Change | Scope |
|------|--------|-------|
| `src/requirements_agent_tools/db/schema.py` | Remove `slug` column from `projects`; split `SCHEMA_SQL` into `BASE_SCHEMA_SQL` + `VEC_SCHEMA_SQL` | 5–10 lines |
| `src/requirements_agent_tools/db/connection.py` | Make `bootstrap()` accept a `sqlite_vec_enabled: bool` param; skip vec table creation when false | ~10 lines |
| `src/requirements_agent_tools/db/projects.py` | Remove `discover_projects()`; remove `get_project_by_slug()`; remove slug derivation from `upsert_project()` | ~30 lines removed |
| `src/requirements_agent_tools/db/_serialization.py` | Remove `slug` mapping in `row_to_project()` | 1–2 lines |
| `src/requirements_agent_tools/project_md.py` | Replace `slug` parameter with flat `MD_PATH` constant | ~5 lines |
| `src/requirements_agent_tools/project_md_cli.py` | Remove `--project` flag; call `get_project_conn()` directly | ~10 lines |
| `src/requirements_agent_tools/refine.py` | Remove `--project` flag; replace `ps.resolve(args.project)` with `get_project_conn()` | 3–5 lines per call site (4 call sites) |
| `src/requirements_agent_tools/req_ops.py` | Remove `--project` flag; replace 6 `ps.resolve()` call sites | ~15 lines |
| `src/requirements_agent_tools/review.py` | Remove `--project` flag; replace 4 `ps.resolve()` call sites | ~12 lines |
| `src/requirements_agent_tools/report.py` | Remove `--project` flag; replace 2 `ps.resolve()` call sites; remove `C.project_dir(slug)` call | ~10 lines |
| `src/requirements_agent_tools/meeting.py` | Remove `--project` flag; replace 7 `ps.resolve()` call sites | ~20 lines |
| `src/requirements_agent_tools/db/cli.py` | Remove `--project` option; replace `C.db_path(slug)` with `C.DB_PATH` | ~10 lines |
| `src/requirements_agent_tools/models.py` | Remove `slug` field from `ProjectMeta` | 2–3 lines |
| `tests/test_db.py` | Update bootstrap SQL to remove `slug` column and stale `project_id` FK in minutes; remove `test_upsert_project_auto_derives_slug`, `test_upsert_project_preserves_explicit_slug`, `test_upsert_project_stores_slug_in_db`, `test_get_project_by_slug_*` tests | ~80 lines removed |
| `pyproject.toml` | Add `pyyaml` to dependencies | 1 line |
| `config/project.yaml` | New file created by `cmd_setup()` | new |

**New files to create:**

| File | Purpose |
|------|---------|
| `config/project.yaml` | Written by `cmd_setup()` at first-run time |
| `tests/test_setup.py` | New test file covering `cmd_setup()`, guard behavior, config write, directory creation |

---

## Architecture Patterns

### Pattern 1: Flat CONSTANTS Replacement

**What:** Replace slug-parameterized helpers with flat path constants derived from `_AGENT_ROOT`.
**When to use:** Any code that needs DB or MD path.

```python
# Source: current CONSTANTS.py (adapted per D-02/D-03) [VERIFIED: existing code]
import os
from pathlib import Path

_AGENT_ROOT: Path = Path(__file__).resolve().parents[2]

PROJECT_DIR: Path = (
    Path(os.environ["PROJECT_DIR"])
    if "PROJECT_DIR" in os.environ
    else _AGENT_ROOT / "project"
)

DB_PATH: Path = PROJECT_DIR / "project.db"
MD_PATH: Path = PROJECT_DIR / "PROJECT.md"
```

### Pattern 2: `get_project_conn()` Helper

**What:** Single function that opens (but does not bootstrap) the project DB, checking that `DB_PATH` exists first.
**When to use:** Every CLI module entry point replaces `ps.resolve(args.project)` with this.

```python
# Source: project_session.py (new implementation per D-04) [ASSUMED — no existing equivalent]
import sqlite3
from . import CONSTANTS as C
from .db.connection import get_db
from ._cli_io import err as _err

def get_project_conn() -> sqlite3.Connection:
    """Open the single project DB. Exits with error if not initialised."""
    if not C.DB_PATH.exists():
        _err("No project found. Run 'uv run init-project setup' first.")
    return get_db(str(C.DB_PATH))
```

### Pattern 3: Conditional Vector Bootstrap

**What:** `bootstrap()` accepts a `sqlite_vec_enabled` flag; the vec virtual table is only created when the flag is true.
**When to use:** Called from `cmd_setup()` (first run) and from `get_project_conn()` on every open.

```python
# Source: db/connection.py (adapted per D-09/D-10) [ASSUMED — pattern derived from existing bootstrap]
def bootstrap(conn: sqlite3.Connection, sqlite_vec_enabled: bool = False) -> None:
    conn.executescript(schema.BASE_SCHEMA_SQL)
    if sqlite_vec_enabled:
        conn.executescript(schema.VEC_SCHEMA_SQL)
    conn.commit()
    schema.seed_reference_tables(conn)
```

### Pattern 4: `config/project.yaml` Read Helper

**What:** Thin function that loads `config/project.yaml` and returns a typed dict.
**When to use:** Called by `db/connection.py` `get_db()` before deciding whether to load sqlite-vec.

```python
# Source: design per D-14 [ASSUMED — no existing equivalent]
import yaml
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "project.yaml"

def load_project_config() -> dict:
    """Load config/project.yaml. Returns defaults if file not found."""
    if not _CONFIG_PATH.exists():
        return {"sqlite_vec": False, "otel_enabled": False}
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}
```

### Pattern 5: Interactive Setup Prompts (click)

**What:** `click.confirm()` for yes/no; `click.prompt()` with `type=click.Choice` for multi-select simulation.
**When to use:** `cmd_setup()` only.

```python
# Source: click 8.3.3 stdlib pattern [VERIFIED: click.confirm/click.prompt APIs inspected]
import click

sqlite_vec = click.confirm("Enable vector embeddings (requires sqlite-vec)?", default=False)
otel = click.confirm("Enable OpenTelemetry tracing (stores flag only)?", default=False)

# .gitignore entries — present all three options as individual confirms
for entry, description in [
    ("project/logs/", "project/logs/ (log files)"),
    ("project/notes/", "project/notes/ (notes directory)"),
    ("project/*.db", "project/*.db (database file)"),
]:
    if click.confirm(f"  Add {description} to .gitignore?", default=True):
        gitignore_entries.append(entry)
```

### Anti-Patterns to Avoid

- **Calling `bootstrap()` without checking `sqlite_vec` config first:** The current `get_db()` unconditionally attempts to load sqlite-vec. After Phase 1, `get_db()` must read `config/project.yaml` before deciding whether to call `sqlite_vec.load()`. Do not skip this check.
- **Using `sys.exit()` directly in module code:** Always use `_err()` from `_cli_io.py` so the JSON error contract is maintained.
- **Creating `project/` inside `get_db()`:** Directory creation belongs in `cmd_setup()` only. `get_db()` should not auto-create the directory on every open — only the setup command creates the structure.
- **Writing `.gitignore` entries without duplicate check:** Read existing content first and filter out entries already present.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Interactive yes/no prompts | Custom `input()` loop | `click.confirm()` | Handles Ctrl-C, default display, test patching via `input=StringIO` |
| YAML config serialization | Custom dict-to-string | `yaml.safe_dump()` | Handles escaping, ordering, encoding edge cases |
| SQLite schema migration | Custom migration runner | `ALTER TABLE ... ADD COLUMN` guarded by `try/except OperationalError` (already established) | Already proven pattern in `connection.py bootstrap()` |

---

## Common Pitfalls

### Pitfall 1: sqlite-vec Load in `get_db()` is Unconditional Today

**What goes wrong:** The current `connection.py` `get_db()` unconditionally calls `sqlite_vec.load(conn)` and raises `RuntimeError` if it fails. After Phase 1, when most environments will have `sqlite_vec = false` in config, this will fail for every `get_project_conn()` call.

**Why it happens:** The multi-project design assumed sqlite-vec was always required (it was the default).

**How to avoid:** `get_db()` must read `config/project.yaml` (or accept a `sqlite_vec_enabled` parameter) before attempting to load the extension. The `try/except` block must become conditional, not a fallback.

**Warning signs:** `RuntimeError: Could not load sqlite-vec extension` on any CLI call after setup with sqlite-vec=no.

### Pitfall 2: Test Suite Uses Stale Bootstrap SQL with `project_id` FK

**What goes wrong:** `test_db.py` lines 100–118 define a `minutes` table with `project_id TEXT NOT NULL REFERENCES projects(project_id)`. After schema change (slug removed), this test-local DDL will create a different schema than production, causing FK violations or missed column errors.

**Why it happens:** The test bootstrap SQL was written to mirror an older schema version and has not been kept in sync.

**How to avoid:** The test bootstrap SQL in `test_db.py` must be updated to match the new production schema exactly. The new test file for Phase 1 should import `schema.BASE_SCHEMA_SQL` directly rather than duplicating DDL.

**Warning signs:** Tests pass against test schema but `uv run req-ops add` fails against production DB.

### Pitfall 3: `project_md.py` Takes `slug` as Parameter

**What goes wrong:** `project_md.save(conn, slug, ...)` and `project_md.append_section(conn, slug, ...)` use `C.md_path(slug)` to derive the file path. After `md_path(slug)` is removed from CONSTANTS, every call site will break.

**Why it happens:** The function signature was designed for multi-project use.

**How to avoid:** Remove `slug` parameter from `project_md.save()` and `append_section()`; use `C.MD_PATH` directly. Update `project_md_cli.py` accordingly.

**Warning signs:** `AttributeError: module 'CONSTANTS' has no attribute 'md_path'` at runtime.

### Pitfall 4: `models.py` `ProjectMeta` Has `slug` Field

**What goes wrong:** `upsert_project()` in `db/projects.py` reads `meta.slug` and inserts it. After the `slug` column is dropped from the schema, this insert will fail with `table projects has no column named slug`.

**Why it happens:** `ProjectMeta.slug` field and `db/projects.py` upsert were built together for multi-project.

**How to avoid:** Remove `slug` from `ProjectMeta` model and from the `upsert_project()` SQL in the same plan.

**Warning signs:** `sqlite3.OperationalError: table projects has no column named slug`.

### Pitfall 5: `discover_projects()` Referenced from `cmd_new()` / `cmd_list()`

**What goes wrong:** The new `cmd_setup()` must not call `discover_projects()` — that function scans `PROJECTS_DIR/<slug>/` which no longer exists.

**Why it happens:** Old `cmd_new()` guard checked for slug collisions via `discover_projects()`.

**How to avoid:** The `cmd_setup()` guard is a simple `PROJECT_DIR.exists()` check (D-07). `discover_projects()` is deleted in this phase.

---

## Runtime State Inventory

> Phase 1 is not a rename/rebrand — it is a structural migration. The inventory covers runtime systems that store the old string patterns or directory conventions.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | No `project/` or `projects/` directories exist on disk (verified: `ls project/ projects/` — both NOT EXISTS) | None — greenfield |
| Live service config | No external services configured | None |
| OS-registered state | No Task Scheduler, pm2, or launchd entries found for this project | None |
| Secrets/env vars | `PROJECTS_DIR` env var in current CONSTANTS.py — replaced by `PROJECT_DIR` env var. Any existing `PROJECTS_DIR` setting in `.env` or shell will be ignored after the rename | Document in migration notes; user must update if using env override |
| Build artifacts | `src/requirements_agent_tools/__pycache__/` — will auto-invalidate on next import after source changes | Auto-handled by Python bytecode invalidation |

**Migration note:** If any user has `PROJECTS_DIR` set as an environment variable, they must rename it to `PROJECT_DIR` after Phase 1. The old variable name will be silently ignored.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (uv) | All CLIs | ✓ | 3.13 (pyproject.toml requires-python) | — |
| sqlite3 | DB layer | ✓ | stdlib | — |
| click | Interactive prompts | ✓ | 8.3.3 | — |
| PyYAML | `config/project.yaml` read/write | ✓ (in venv) | 6.0.3 | Must add to pyproject.toml |
| sqlite-vec | Vector embeddings | Conditional | 0.1.9 (declared dep) | Skip entirely when `sqlite_vec: false` in config |
| loguru | Logging | ✓ | 0.7.3 | — |
| pydantic | Model validation | ✓ | 2.13.3 | — |

**Missing dependencies with no fallback:**
- PyYAML must be added to `pyproject.toml` dependencies. It is already installed in the venv (pulled in transitively) but is not a declared dependency. `uv add pyyaml` is required.

**Missing dependencies with fallback:**
- sqlite-vec: if not installed or `sqlite_vec: false` — skip vec table creation entirely.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_setup.py tests/test_db.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INIT-01 | `project/` directory created by `cmd_setup()` | unit | `uv run pytest tests/test_setup.py::test_setup_creates_project_dir -x` | ❌ Wave 0 |
| INIT-01 | `project/logs/` and `project/notes/` created | unit | `uv run pytest tests/test_setup.py::test_setup_creates_subdirs -x` | ❌ Wave 0 |
| INIT-02 | `project/project.db` bootstrapped with correct schema | unit | `uv run pytest tests/test_setup.py::test_setup_bootstraps_db -x` | ❌ Wave 0 |
| INIT-02 | `projects` table has no `slug` column | unit | `uv run pytest tests/test_db.py::test_projects_table_no_slug_column -x` | ❌ Wave 0 |
| INIT-03 | `config/project.yaml` written with `sqlite_vec` and `otel_enabled` keys | unit | `uv run pytest tests/test_setup.py::test_setup_writes_config_yaml -x` | ❌ Wave 0 |
| INIT-04 | Interactive prompts accept yes/no inputs correctly | unit | `uv run pytest tests/test_setup.py::test_setup_interactive_prompts -x` | ❌ Wave 0 |
| INIT-05 | Second run exits non-zero with guard message | unit | `uv run pytest tests/test_setup.py::test_setup_guard_on_second_run -x` | ❌ Wave 0 |
| INIT-06 | All CLIs work without `--project` flag | smoke | `uv run refine --help && uv run req-ops --help && uv run review --help && uv run report --help && uv run meeting --help` | ❌ Wave 0 |
| INIT-06 | `get_project_conn()` returns connection when DB exists | unit | `uv run pytest tests/test_setup.py::test_get_project_conn_opens_db -x` | ❌ Wave 0 |
| INIT-06 | `get_project_conn()` exits with error when DB absent | unit | `uv run pytest tests/test_setup.py::test_get_project_conn_no_db -x` | ❌ Wave 0 |
| Full suite | All 104 existing tests still pass after slug removal | regression | `uv run pytest` | ✓ exists (will shrink as slug tests deleted) |

### Validation CLI Invocations (for VALIDATION.md)

```bash
# INIT-01: directory structure
uv run init-project setup  # answer prompts non-interactively (see below)
test -d project/logs && test -d project/notes && echo "PASS: dirs exist"

# INIT-02: DB exists with correct schema
test -f project/project.db && echo "PASS: db exists"
uv run python -c "
import sqlite3, sys
conn = sqlite3.connect('project/project.db')
cols = [r[1] for r in conn.execute('PRAGMA table_info(projects)')]
assert 'slug' not in cols, f'FAIL: slug column present: {cols}'
assert 'singleton' in cols
print('PASS: schema correct')
"

# INIT-03: config written
python3 -c "
import yaml
c = yaml.safe_load(open('config/project.yaml'))
assert 'sqlite_vec' in c and 'otel_enabled' in c
print('PASS: config/project.yaml valid')
"

# INIT-05: guard message
uv run init-project setup && echo "FAIL: should have exited non-zero" || echo "PASS: second run exits non-zero"

# INIT-06: all CLI help exits 0
uv run refine --help > /dev/null && echo "PASS: refine --help"
uv run req-ops --help > /dev/null && echo "PASS: req-ops --help"
uv run review --help > /dev/null && echo "PASS: review --help"
uv run report --help > /dev/null && echo "PASS: report --help"
uv run meeting --help > /dev/null && echo "PASS: meeting --help"

# Full regression
uv run pytest
```

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_setup.py tests/test_db.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green + all CLI help exits 0 before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_setup.py` — covers INIT-01 through INIT-06 (new file)
- [ ] `tests/test_db.py` lines ~100–118 — update stale `minutes` bootstrap SQL
- [ ] `tests/test_db.py` — remove slug-specific test cases (`test_upsert_project_auto_derives_slug`, `test_upsert_project_preserves_explicit_slug`, `test_upsert_project_stores_slug_in_db`, `test_get_project_by_slug_*`, `test_slug_column_exists`)
- [ ] `tests/test_slug_infrastructure.py` — DELETE entirely
- [ ] `tests/test_init.py` — REWRITE entirely for `cmd_setup()`
- [ ] `pyproject.toml` — add `pyyaml` dependency before any YAML write is tested

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Phase 1 is local CLI setup only |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | Local filesystem only |
| V5 Input Validation | Yes (low risk) | PyYAML `safe_load()` only (not `yaml.load()`) — prevents arbitrary code execution via YAML deserialization |
| V6 Cryptography | No | No secrets stored in Phase 1 |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML deserialization attack | Tampering | Use `yaml.safe_load()` exclusively — never `yaml.load()` without Loader |
| Path traversal via `PROJECT_DIR` env var | Tampering | Validate that `PROJECT_DIR` is an absolute path (already in current CONSTANTS env var pattern) |
| `.gitignore` injection | Tampering | Only append known static strings; never interpolate user input into `.gitignore` entries |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `get_project_conn()` should exit with `_err()` when DB absent (rather than raising an exception) | Pattern 2 | If callers expect an exception, the exit-on-error approach breaks their try/except; planner should confirm error handling contract |
| A2 | The `notes/` subdirectory should be created by `cmd_setup()` even though no Phase 1 feature writes to it | INIT-01 description | If notes/ is not needed until a later phase, creating it eagerly is harmless but unnecessary |
| A3 | PyYAML should be used for `config/project.yaml` (consistent with `config/default.yaml`) rather than TOML | Standard Stack | If project wants to standardize on TOML (stdlib in Python 3.11+), TOML write requires `tomllib` (stdlib, read-only) + `tomli_w` (write); YAML is the safer choice given existing pattern |
| A4 | `project_md.py` `save()` and `append_section()` should use `C.MD_PATH` directly after slug removal | Pitfall 3 | If project_md is used with non-standard paths in tests, this breaks test isolation — may need a path parameter retained |

---

## Open Questions

1. **How should `get_db()` know whether to load sqlite-vec?**
   - What we know: `config/project.yaml` contains `sqlite_vec: bool` after setup
   - What's unclear: Should `get_db()` read the config file itself, or should callers read it first and pass a flag?
   - Recommendation: Add an optional `sqlite_vec_enabled: bool = False` parameter to `get_db()`. Callers that know the config (like CLIs) pass it in. Default false is safe for tests.

2. **Should `cmd_setup()` also write a minimal project row to the DB?**
   - What we know: D-06 says setup creates the directory, bootstraps the DB, and writes config.yaml. It does not mention inserting a `projects` row.
   - What's unclear: The FRET and reporting skills need a `projects` row. When does the first `projects` row get inserted?
   - Recommendation: Phase 1 setup does NOT insert the projects row (that belongs to Phase 2 elicitation where the user provides project name etc.). The `projects` table is bootstrapped but empty after setup. Document this as a known state.

3. **`--project` flag on `db` CLI is a `--project` option before the subcommand, not after it** (click global option pattern). Does removing it change the CLI surface for the `db` tool in a way that breaks any documented workflow?
   - What we know: `db/cli.py` lines 84+ shows `--project` as a click option on the root command group.
   - What's unclear: Whether any external scripts or SKILL.md files reference `db --project <slug>` invocations.
   - Recommendation: Grep SKILL.md files for `db --project` before deleting; update any references found.

---

## Sources

### Primary (HIGH confidence)
- `src/requirements_agent_tools/db/schema.py` — VERIFIED current schema DDL, confirmed no `project_id` FKs in requirements/updates/minutes
- `src/requirements_agent_tools/CONSTANTS.py` — VERIFIED current slug-based helpers
- `src/requirements_agent_tools/db/connection.py` — VERIFIED `get_db()` and `bootstrap()` behavior
- `src/requirements_agent_tools/db/projects.py` — VERIFIED `upsert_project`, `discover_projects`, `get_project_by_slug`
- `src/requirements_agent_tools/project_session.py` — VERIFIED `resolve()` call sites
- `tests/test_db.py`, `tests/test_slug_infrastructure.py`, `tests/test_init.py` — VERIFIED test coverage and stale bootstrap SQL
- `pyproject.toml` — VERIFIED dependencies, entry points
- `config/default.yaml` — VERIFIED YAML loading pattern

### Secondary (MEDIUM confidence)
- click 8.3.3 `click.confirm` / `click.prompt` APIs — VERIFIED by introspection (`help(click.confirm)`)
- PyYAML 6.0.3 availability — VERIFIED by `uv run python -c "import yaml; print(yaml.__version__)"`

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in uv env
- Architecture: HIGH — full codebase read; all call sites counted
- Schema proposal: HIGH — verified against canonical schema.py; no assumptions
- Pitfalls: HIGH — derived from actual code reading, not training knowledge
- Test coverage gaps: HIGH — verified by listing existing test files

**Research date:** 2026-04-30
**Valid until:** 2026-05-30 (stable stack; no external service dependencies)

---

## RESEARCH COMPLETE
