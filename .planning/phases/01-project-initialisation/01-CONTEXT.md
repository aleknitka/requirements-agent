# Phase 1: Project Initialisation - Context

**Gathered:** 2026-04-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Technical setup only: `init-project setup` creates the single-project directory structure, SQLite database, and `config/project.yaml`, then asks setup questions (sqlite-vec, .gitignore, OpenTelemetry flag). Simultaneously, all multi-project/slug infrastructure is removed from the codebase (CONSTANTS.py, project_session.py, init_project.py, all `--project` CLI flags).

This phase does NOT implement the user-facing onboarding interview or requirement collection — that belongs in Phase 2 (Elicitation Skill). The DB schema is re-evaluated from scratch for the single-project model as a research task before planning.

**What changes from the current codebase:**
- Multi-project model → single-project model
- Slug-based paths → single `project/` directory at repo root
- `--project <slug>` flag on every CLI → removed entirely
- `projects/` directory → `project/` (singular, flat)
- `cmd_new()` with metadata args → `cmd_setup()` with technical-setup questions

</domain>

<decisions>
## Implementation Decisions

### Single-Project Model
- **D-01:** One project per agent instance. No slugs, no `.active` sentinel, no multi-project selection. All code that references slugs, `PROJECTS_DIR/<slug>/`, or `--project <slug>` is removed in this phase.
- **D-02:** Single project directory: `project/` at the repo root. Structure: `project/project.db`, `project/PROJECT.md`, `project/logs/`, `project/notes/`. Override path via `PROJECT_DIR` env var (absolute path).
- **D-03:** `CONSTANTS.py` loses all slug-based helpers (`project_dir(slug)`, `db_path(slug)`, `md_path(slug)`, `slugify()`). Replaced with flat constants: `PROJECT_DIR`, `DB_PATH`, `MD_PATH`.
- **D-04:** `project_session.resolve(slug_or_name)` is replaced with a simple `get_project_conn()` helper that opens the single DB. No slug argument, no discovery loop.
- **D-05:** All CLIs (`refine`, `req-ops`, `review`, `report`, `meeting`, `db`) lose their `--project <slug>` global flag. They always operate on the single project.

### `init-project setup` Command
- **D-06:** Command: `uv run init-project setup`. Creates `project/` directory tree, bootstraps `project/project.db`, writes `config/project.yaml` with setup choices.
- **D-07:** On second run (project/ already exists): guard + abort. Print: `"Project already initialised. Use 'init-project reset' to start fresh."` Exit non-zero. Do NOT implement `reset` in this phase — just name it in the message.
- **D-08:** Setup questions asked interactively during `init-project setup`:
  1. **sqlite-vec?** — Enable vector embeddings (requires sqlite-vec extension). Default: no.
  2. **.gitignore entries?** — Offer to append `project/logs/`, `project/notes/`, `project/*.db` to `.gitignore`. Checkbox-style (any combination).
  3. **OpenTelemetry?** — Enable tracing (implementation deferred). Default: no. Stores flag only.
- **D-09:** sqlite-vec = no → skip silently. Do not create the vec0 virtual table or any embeddings columns/tables. All semantic search commands return empty results without error.
- **D-10:** sqlite-vec = yes → create the vec0 virtual table and embeddings table as part of `bootstrap()`.
- **D-11:** Setup choices persisted to `config/project.yaml` (YAML, next to existing `config/default.yaml`). Keys: `sqlite_vec: bool`, `otel_enabled: bool`. The `.gitignore` entries are written to `.gitignore` directly — no need to record them in config.

### DB Schema (Research Task)
- **D-12:** The current schema (requirements, projects, meeting_minutes, decisions, action_items, updates, embeddings) must be re-evaluated for the single-project model as a **research task before planning**. Key questions for the researcher:
  - Is a `projects` table still needed, or does the DB implicitly represent one project?
  - Can `project_id` foreign keys be dropped from all tables?
  - Are `meeting_minutes`, `decisions`, `action_items` still in scope for v1?
  - What columns are actually used vs. dead weight?
  - What indexes are needed?
- **D-13:** The researcher should produce a proposed schema (tables + columns) that the planner can implement. This is the primary research deliverable for this phase.

### Config Format
- **D-14:** Setup config file: `config/project.yaml`. Read at startup by any module that needs to check sqlite-vec or OTel status. Must be present after `init-project setup` completes.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current Code to Refactor
- `src/requirements_agent_tools/CONSTANTS.py` — slug-based path helpers to remove; replace with flat PROJECT_DIR constants
- `src/requirements_agent_tools/project_session.py` — resolve() stub; replace with single-project conn helper
- `src/requirements_agent_tools/init_project.py` — cmd_new() to rewrite as cmd_setup(); remove all metadata args
- `src/requirements_agent_tools/db/schema.py` — schema bootstrap; re-evaluate all tables for single-project model
- `src/requirements_agent_tools/models.py` — ProjectMeta and related models; audit for slug/project_id dependencies

### Config
- `config/default.yaml` — existing runtime defaults; `config/project.yaml` is a new sibling file
- `pyproject.toml` — entry points; `init-project` stays, subcommand changes from `new` to `setup`

### Tests to Update
- `tests/test_init.py` — all tests reference `cmd_new()` and `--project` flags; need rewrite for `cmd_setup()`
- `tests/test_db.py` — check for project_id FK references that become obsolete
- `tests/test_slug_infrastructure.py` — likely fully deleted (slug infra removed)

### ROADMAP
- `.planning/ROADMAP.md` — Phase 1 plans (01-01 through 01-04) are obsolete; planner rewrites them

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/requirements_agent_tools/db/connection.py` — `get_db(path)` and `bootstrap(conn)` are reusable; path arg changes from slug-derived to flat `DB_PATH` constant
- `src/requirements_agent_tools/db/schema.py` — `bootstrap()` function structure reusable; table DDL needs re-evaluation
- `config/default.yaml` — YAML loading pattern already established; `config/project.yaml` follows the same pattern

### Established Patterns
- `uv run <entry-point>` — all CLI commands follow this pattern (D-01 from Phase 0.5)
- JSON stdout / JSON stderr — `_ok()` / `_err()` output helpers in `_cli_io.py`; reuse for setup command output
- Google-style docstrings at 98.2% coverage — all new functions must follow (D-13 from Phase 0.5)
- Real-SQLite tests only — no MagicMock; use `tmp_path` fixture (established in Phase 0)

### Integration Points
- Every CLI module (`refine.py`, `req_ops.py`, `review.py`, `report.py`, `meeting.py`) imports `project_session.resolve()` — all need updating when resolve() is replaced
- `CONSTANTS.py` is imported everywhere — path constant changes ripple to all modules
- `.gitignore` — setup writes entries; must check for duplicates before appending

</code_context>

<specifics>
## Specific Ideas

- `init-project reset` is named in the guard message (D-07) but NOT implemented in Phase 1. The planner must not scope it in.
- OpenTelemetry is intentionally deferred — Phase 1 only stores the flag. The planner must not implement any OTel tracing.
- The `.gitignore` append should be idempotent — check if entries already exist before adding.
- `test_slug_infrastructure.py` is probably entirely obsolete after the slug removal — plan to delete it.

</specifics>

<deferred>
## Deferred Ideas

- `init-project reset` — named in D-07 guard message, implement in a later phase
- OpenTelemetry tracing implementation — flag captured in Phase 1 config, implementation is a future phase
- `init-project update` — update setup config (sqlite-vec, OTel) after initial setup; future phase
- Multi-project support — explicitly out of scope for v1; user confirmed single-project model

</deferred>

---

*Phase: 1-Project Initialisation*
*Context gathered: 2026-04-30*
