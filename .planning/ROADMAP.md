# Roadmap: Requirements Agent

## Overview

The requirements-agent delivers a conversational requirements engineering loop: load agent → interview user → elicit and classify requirements → refine to FRET grammar field-by-field → persist to SQLite → report. Seven cascading runtime bugs block every skill from running today, so Phase 0 is a hard prerequisite. Phases 1 through 5 build upward from a clean foundation through project initialisation, elicitation, persistence, reporting, and audit governance, delivering a complete v1 end-to-end flow.

## Phases

**Phase Numbering:**
- Integer phases (0, 1, 2, 3, 4, 5): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 0: Bug Triage** - Fix all 9 cascading runtime bugs so every skill can import and run without error
- [ ] **Phase 0.5: Package Scaffold** - Move skill scripts into installable `requirements_agent` package; set up lazydocs + pre-commit doc rendering; establish agent fallback pattern
- [ ] **Phase 1: Project Initialisation** - `init.py new` runs end-to-end, writes DB + PROJECT.md, auto-selects via .active sentinel
- [ ] **Phase 2: Elicitation Skill** - New `elicit-requirements` skill interviews user, captures context, elicits and classifies requirements
- [ ] **Phase 3: FRET Refinement** - Field-by-field FRET protocol resolves ambiguities and produces a confirmed, typed requirement
- [ ] **Phase 4: Persistence and Reporting** - Confirmed requirements write to DB; `report.py` outputs FRET coverage and counts
- [ ] **Phase 5: Audit and Governance** - Change log, soft-delete, HITL confirmation gates, and PostToolUse hook protect all DB writes

## Phase Details

### Phase 0: Bug Triage
**Goal**: Fix all 9 cascading runtime bugs so every skill script imports cleanly and can be invoked without AttributeError, NameError, or TypeError.
**Depends on**: Nothing (first phase)
**Requirements**: BUG-01, BUG-02, BUG-03, BUG-04, BUG-05, BUG-06, BUG-07, BUG-08, BUG-09
**Success Criteria** (what must be TRUE):
  1. `python -c "import shared.db"` runs without any error from repo root
  2. `uv run python skills/new-project-initiation/scripts/init.py --help` exits 0 with usage output
  3. `uv run pytest` passes with real-SQLite tests (no MagicMock auto-attribute creation)
  4. `RequirementIn(title="x", description="y", req_type="FUN")` instantiates without NameError or AttributeError
  5. `uv run python skills/status-report/scripts/report.py --help` exits 0 (imports clean)
**Plans**: 6 plans

Plans:
- [x] 00-01-PLAN.md — Fix `shared/db.py` core: remove `C.DB_PATH` default, fix `_make_req_id` to use `.value`
- [x] 00-02-PLAN.md — Fix `shared/models.py`: `RequirementType` str Enum, `RequirementTypeMeta` NamedTuple, remove `RequirementArea` and fret fields
- [x] 00-03-PLAN.md — Fix import chain: `init.py` bare imports (D-09), `project_session.py` API alignment
- [x] 00-04-PLAN.md — Fix callers: `req_ops.py` (EXTRA-02/03/04), `refine.py` (BUG-07)
- [x] 00-05-PLAN.md — Add `slug` column to `projects` table; `get_project_by_slug`; align `project_session`
- [x] 00-06-PLAN.md — Write tests: `test_db.py` (real-SQLite), `test_models.py`, replace `test_init.py` with subprocess tests

### Phase 0.5: Package Scaffold
**Goal**: Solidify `requirements_agent_tools` as the canonical CLI package: update all 6 skill command surfaces to use installed entry points, remove dead `scripts/` directories, add a documentation toolchain (lazydocs + committed `docs/`), configure a comprehensive pre-commit pipeline, verify the agent.yaml fallback pattern, and update CLAUDE.md to reflect the new package structure.
**Depends on**: Phase 0
**Requirements**: PKG-01, PKG-02, PKG-03, PKG-04, PKG-05, PKG-06
**Success Criteria** (what must be TRUE):
  1. `uv run init-project --help`, `uv run refine --help`, `uv run req-ops --help`, `uv run review --help`, `uv run report --help`, `uv run meeting --help` all exit 0
  2. `find skills -name 'scripts' -type d` returns nothing (all `skills/*/scripts/` directories removed)
  3. `docs/requirements_agent_tools.md` exists (lazydocs Markdown API reference committed, 21 files)
  4. `.pre-commit-config.yaml` exists with hooks for ruff-format, ruff-check, ty, bandit, detect-private-key, interrogate (≥90%), lazydocs, pytest
  5. `CLAUDE.md` references `src/requirements_agent_tools/` (not `shared/`) and uses `uv run <entry-point>` invocations; Known Issues section cleaned of fixed items
  6. `uv run interrogate -v --fail-under 90 src/requirements_agent_tools/` exits 0
**Plans**: 4 plans

Plans:
- [x] 00.5-01: Update all 6 SKILL.md files to use `uv run <entry-point>` and document all sub-commands; remove `skills/*/scripts/` directories — DONE 2026-04-28
- [x] 00.5-02: Add lazydocs as dev dep; generate `docs/` (21 Markdown files) from full package; commit output — DONE 2026-04-28
- [x] 00.5-03: Configure `.pre-commit-config.yaml` with 8 hooks (ruff, ty, bandit, interrogate, lazydocs, pytest, detect-private-key); add dev deps — DONE 2026-04-29
- [x] 00.5-04: Update CLAUDE.md — new package structure, entry-point commands, agent fallback pattern, clean Known Issues — DONE 2026-04-29

### Phase 1: Project Initialisation
**Goal**: `init.py new` runs end-to-end, creating a project DB and PROJECT.md in `projects/<slug>/`, and the `.active` sentinel enables auto-selection in multi-project environments.
**Depends on**: Phase 0
**Requirements**: INIT-01, INIT-02, INIT-03, INIT-04, INIT-05, INIT-06
**Success Criteria** (what must be TRUE):
  1. `uv run python skills/new-project-initiation/scripts/init.py new --name "Test Project"` creates `projects/test-project/test-project.db` and `projects/test-project/PROJECT.md`, exits 0
  2. Running `init.py new` a second time with the same slug prints a message and does not overwrite the existing project
  3. `projects/.active` contains the slug of the most recently created or selected project
  4. `project_session.resolve()` returns the active project without prompting when `.active` exists
  5. All DB CRUD unit tests pass against a real in-memory SQLite instance (no MagicMock)
**Plans**: TBD

Plans:
- [x] 01-01: TDD RED phase — delete slug-infra tests, update test_db.py, create test_setup.py — DONE 2026-04-30
- [x] 01-02: Rewrite CONSTANTS/models/schema/connection — flat constants, slug removed, conditional sqlite-vec — DONE 2026-04-30
- [x] 01-03: Remove slug from db/projects.py, _serialization.py, project_md.py — verified (pre-applied in 01-02 cascade) — DONE 2026-04-30
- [x] 01-04: Implement cmd_setup() in init_project.py — interactive setup questions, project dir creation, config.yaml write — DONE 2026-04-30
- [ ] 01-05: Clean up remaining slug references (db/cli.py, init_project.py, refine/req_ops/review/report/meeting CLIs)
**UI hint**: no

### Phase 2: Elicitation Skill
**Goal**: A new `elicit-requirements` skill interviews the user about project background, captures context, elicits at least one raw requirement, and classifies it by type and priority before formalisation.
**Depends on**: Phase 1
**Requirements**: ELICIT-01, ELICIT-02, ELICIT-03
**Success Criteria** (what must be TRUE):
  1. `skills/elicit-requirements/SKILL.md` exists with `allowed-tools` frontmatter and a structured interview protocol
  2. Agent asks 5-8 scoped questions about project background before proposing any requirement
  3. Agent captures at least one raw requirement text confirmed by the user, assigns a `RequirementType` value, and assigns priority — all before writing to DB
  4. Agent distinguishes functional from non-functional requirements and names the correct `RequirementType` code from the Enum
  5. Partial elicitation sessions are resumable — in-progress requirement stays in-context (DRAFT status) until user confirmation
**Plans**: TBD

Plans:
- [ ] 02-01: Scaffold `skills/elicit-requirements/` directory — `SKILL.md`, `scripts/`, `references/`
- [ ] 02-02: Write `SKILL.md` interview protocol — project background questions, ML probe trigger conditions, type classification guidance
- [ ] 02-03: Implement `elicit.py` — capture context to DB, write raw requirement with DRAFT status after user confirms text
- [ ] 02-04: Add `_ok` / `_err` shared helpers to `shared/` and import them in all skill scripts
- [ ] 02-05: Register `elicit-requirements` skill in `agent.yaml`

### Phase 3: FRET Refinement
**Goal**: The `elicit-requirements` skill walks FRET fields one at a time (COMPONENT → SCOPE → CONDITION → TIMING → RESPONSE), assembles the complete statement in-context, and writes it atomically to the DB on user confirmation.
**Depends on**: Phase 2
**Requirements**: ELICIT-04
**Success Criteria** (what must be TRUE):
  1. Agent asks exactly one FRET field question per conversational turn, in the canonical order
  2. Agent does not write any FRET data to DB until the user confirms the complete assembled statement
  3. A confirmed requirement row in the DB has non-null `fret_statement` and `fret_fields` JSON
  4. A lightweight regex validator rejects `fret_statement` values containing "should", vague components, or non-measurable responses before the row is written
  5. `refine.py apply` can be called standalone and updates `fret_statement` + `fret_fields` without error
**Plans**: TBD

Plans:
- [ ] 03-01: Update `skills/elicit-requirements/SKILL.md` with field-by-field FRET protocol and one-field-per-turn constraint
- [ ] 03-02: Implement FRET validator in `shared/fret_validator.py` — regex checks for vague language and missing required fields
- [ ] 03-03: Wire `refine.py apply` call into elicitation confirmation gate — atomic write of `fret_statement` + `fret_fields`
- [ ] 03-04: Align `fret_grammar.md` type names with actual `RequirementType` Enum codes; update `refine-requirements` SKILL.md references

### Phase 4: Persistence and Reporting
**Goal**: Confirmed requirements are durably written to the project DB behind a user confirmation gate, and `report.py` outputs FRET coverage percentage, requirement counts by type and status, and a critical-open list.
**Depends on**: Phase 3
**Requirements**: PERSIST-01, REPORT-01
**Success Criteria** (what must be TRUE):
  1. A confirmed requirement written in the elicitation skill is retrievable via `db.search_requirements(conn, project_id)` and has `status = "open"`
  2. `uv run python skills/status-report/scripts/report.py generate --project <slug>` exits 0 and prints a markdown report to stdout
  3. The report includes: project name, total requirement count, counts by `RequirementType`, counts by status, FRET coverage percentage (requirements with non-null `fret_statement` / total), and a list of open requirements with priority `critical`
  4. Requirements with `status = "draft"` do not appear in the report as confirmed/open
**Plans**: TBD

Plans:
- [ ] 04-01: Implement three-gate persistence model — project gate (upsert_project), requirement gate (insert_requirement on confirm), FRET gate (update_requirement fret_statement on confirm)
- [ ] 04-02: Implement `report.py generate` — SQL aggregation for counts, FRET coverage, RAG signal, critical-open list
- [ ] 04-03: Add `DRAFT` to `RequirementStatus` Enum if not present; ensure only confirmed requirements reach `open`
- [ ] 04-04: Write integration test — full flow: create project → elicit → confirm requirement → confirm FRET → generate report

### Phase 5: Audit and Governance
**Goal**: Every DB write appends to a `changes` table, soft-delete enforces HITL confirmation, destructive project operations require stated reason and token, and a PostToolUse hook captures direct PROJECT.md edits.
**Depends on**: Phase 4
**Requirements**: AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04, AUDIT-05, AUDIT-06
**Success Criteria** (what must be TRUE):
  1. After any `upsert_requirement` or `update_requirement` call, a row exists in `changes` with correct `action`, `entity_type`, `entity_id`, `before_json`, and `after_json`
  2. Calling soft-delete without a non-empty `reason` raises an error and writes nothing to the DB; calling with reason sets `status = "removed"` and the requirement row still exists
  3. A phase-transition-to-closed or bulk status change displays a confirmation prompt; executing without confirmation writes nothing
  4. `md_writer.regenerate()` logs a `PROJECT.md regenerated` event to `changes` with trigger context
  5. Editing `projects/**/PROJECT.md` directly via the Write/Edit tool triggers `hooks/scripts/log_change.py` and writes an audit entry
**Plans**: TBD

Plans:
- [ ] 05-01: Create `changes` table in `db.py` `bootstrap()` — schema: `id`, `timestamp`, `action`, `entity_type`, `entity_id`, `before_json`, `after_json`, `reason`, `confirmation_token`
- [ ] 05-02: Wrap all `db.py` write functions to auto-append to `changes`; enforce non-empty `reason` on destructive ops
- [ ] 05-03: Implement soft-delete in `db.py` — set `status = "removed"`, no physical DELETE; require reason + HITL confirmation
- [ ] 05-04: Add `md_writer.regenerate()` audit event — log to `changes` with trigger context
- [ ] 05-05: Implement HITL confirmation gate for destructive project operations — phase close, archive, bulk status change
- [ ] 05-06: Update `hooks/hooks.yaml` with `PostToolUse` hook on Write/Edit targeting `projects/**/PROJECT.md`; implement `hooks/scripts/log_change.py`

## Progress

**Execution Order:**
Phases execute in numeric order: 0 → 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 0. Bug Triage | 6/6 | Complete | 2026-04-24 |
| 0.5. Package Scaffold | 4/4 | Complete | 2026-04-29 |
| 1. Project Initialisation | 4/5 | In Progress|  |
| 2. Elicitation Skill | 0/5 | Not started | - |
| 3. FRET Refinement | 0/4 | Not started | - |
| 4. Persistence and Reporting | 0/4 | Not started | - |
| 5. Audit and Governance | 0/6 | Not started | - |
