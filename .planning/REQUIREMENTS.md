# Requirements — Requirements Agent v1

## v1 Requirements

### Bug Fixes (BUG) — Phase 0 prerequisite

- [ ] **BUG-01**: `db.py` imports cleanly — `C.DB_PATH` default removed or constant added to `CONSTANTS.py`
- [ ] **BUG-02**: `init.py` and all callers bind `db` correctly — `import db` via `sys.path`, not `import shared.db`
- [ ] **BUG-03**: API aligned — all callers use `db.list_projects(conn)`, not `db.list_all_projects()`
- [ ] **BUG-04**: `get_project(conn, slug)` called with both required args throughout all skills
- [ ] **BUG-05**: `RequirementArea` reference removed from `models.py`; `RequirementIn` instantiates without error
- [ ] **BUG-06**: `fret_statement` + `fret_fields` columns added to `requirements` table and included in `update_requirement` updatable set
- [ ] **BUG-07**: `refine.py` argument order fixed for `update_requirement(conn, req_id, changes)`
- [ ] **BUG-08**: `projects` table has `slug` column; all callers consistent
- [ ] **BUG-09**: `report.py.py` renamed to `report.py`

### Project Initialisation (INIT)

- [ ] **INIT-01**: `init.py new` runs end-to-end — creates DB + `PROJECT.md` in `projects/<slug>/`, exits 0, no errors
- [ ] **INIT-02**: Project onboarding skill gathers enterprise context, tech stack, and project background through conversation
- [ ] **INIT-03**: `db.py` public API is consistent — `list_projects(conn)`, `get_db(path)`, `get_project(conn, slug)` used uniformly
- [ ] **INIT-04**: All DB operations have unit tests passing against real SQLite (not `MagicMock`; uses `create_autospec`)
- [ ] **INIT-05**: `PROJECT.md` generated and written to `projects/<slug>/` via `md_writer`
- [ ] **INIT-06**: `projects/.active` sentinel file written on project creation/selection; `project_session.resolve()` reads it for auto-selection in multi-project environments

### Elicitation (ELICIT)

- [ ] **ELICIT-01**: Agent interviews user about project background via conversation and captures context to DB
- [ ] **ELICIT-02**: Agent elicits at least one raw requirement from the interview
- [ ] **ELICIT-03**: Agent classifies requirement into type (functional/non-functional + `RequirementType`) and resolves ambiguities before formalisation
- [ ] **ELICIT-04**: `elicit-requirements` skill exists with field-by-field FRET conversation protocol (COMPONENT → SCOPE → CONDITION → TIMING → RESPONSE)

### Persistence (PERSIST)

- [ ] **PERSIST-01**: Refined requirement is written to the project DB and readable back via `db.search_requirements(conn, project_id)`

### Reporting (REPORT)

- [ ] **REPORT-01**: `report.py` outputs stored requirements with FRET statements, requirement count by type/status, and FRET coverage %

### Audit & Governance (AUDIT)

- [ ] **AUDIT-01**: `changes` table exists per project DB with schema: `id`, `timestamp`, `action` (insert/update/soft-delete/project-op), `entity_type` (requirement/project/md), `entity_id`, `before_json`, `after_json`, `reason` (non-empty for destructive ops), `confirmation_token`
- [ ] **AUDIT-02**: All `db.py` write operations (`upsert_project`, `upsert_requirement`, `update_requirement`) append to the change log automatically; deletions and destructive ops require non-empty `reason` and store `before_json`
- [ ] **AUDIT-03**: `md_writer.regenerate()` calls log a `PROJECT.md regenerated` event with trigger context
- [ ] **AUDIT-04**: Claude Code hook in `hooks.yaml` on `PostToolUse` (Write/Edit) targeting `projects/**/PROJECT.md` calls `hooks/scripts/log_change.py` to capture direct file edits outside `md_writer`
- [ ] **AUDIT-05**: Requirement removal is soft-delete only — sets `status = "removed"`, row never physically deleted; requires HITL confirmation and non-empty reason before executing; confirmation token logged
- [ ] **AUDIT-06**: Destructive project operations (phase transition to `closed`, project archive, bulk status changes) require HITL confirmation and stated reason before executing; each logged with operation type, reason, and confirmation token

---

## v2 Requirements (deferred)

- Traceability management — bidirectional req linking, impact analysis, decision logging, change diff with rationale
- Conflict detection — cross-requirement consistency checks, contradiction flagging, completeness scoring
- SysML v2 formalisation — requirement diagrams, block definitions, use case / activity diagrams; auto-generation from NL
- Full FRET pipeline — FRET grammar validator, export to NASA FRET tooling format
- Gherkin/BDD generation — Given/When/Then auto-generated from req text; linked back to parent req IDs
- Requirement-level external links — Jira, GitHub issues, Confluence, MLflow experiments, data catalog entries
- ML lifecycle domain knowledge — data quality, labeling, model card reqs, drift monitoring, retraining triggers
- AI governance elicitation — fairness, XAI, bias auditing, EU AI Act risk tiers, model registry compliance
- VCS/CI bidirectional linkage — GitHub/GitLab issues ↔ req IDs; PR descriptions auto-linked; test results fed back

---

## Out of Scope (v1)

- Hard delete of any requirement row — soft-delete only, always
- Meeting transcription / audio processing — v2, needs separate integration
- Document ingestion (PDFs, specs, PRDs) — v2, starts with conversation
- Git / codebase analysis for requirement impact — v3
- Multi-agent parallel elicitation — future
- Vector semantic search — foundation in place, not needed for v1 flow
- Web UI or API layer — CLI-first
- MoSCoW voting, traceability matrices, baseline management — over-engineered for v1

---

## Traceability

| REQ-ID | Phase | Roadmap Phase |
|--------|-------|---------------|
| BUG-01 | Phase 0: Bug Triage | Phase 0 |
| BUG-02 | Phase 0: Bug Triage | Phase 0 |
| BUG-03 | Phase 0: Bug Triage | Phase 0 |
| BUG-04 | Phase 0: Bug Triage | Phase 0 |
| BUG-05 | Phase 0: Bug Triage | Phase 0 |
| BUG-06 | Phase 0: Bug Triage | Phase 0 |
| BUG-07 | Phase 0: Bug Triage | Phase 0 |
| BUG-08 | Phase 0: Bug Triage | Phase 0 |
| BUG-09 | Phase 0: Bug Triage | Phase 0 |
| INIT-01 | Phase 1: Project Initialisation | Phase 1 |
| INIT-02 | Phase 1: Project Initialisation | Phase 1 |
| INIT-03 | Phase 1: Project Initialisation | Phase 1 |
| INIT-04 | Phase 1: Project Initialisation | Phase 1 |
| INIT-05 | Phase 1: Project Initialisation | Phase 1 |
| INIT-06 | Phase 1: Project Initialisation | Phase 1 |
| ELICIT-01 | Phase 2: Elicitation Skill | Phase 2 |
| ELICIT-02 | Phase 2: Elicitation Skill | Phase 2 |
| ELICIT-03 | Phase 2: Elicitation Skill | Phase 2 |
| ELICIT-04 | Phase 3: FRET Refinement | Phase 3 |
| PERSIST-01 | Phase 4: Persistence and Reporting | Phase 4 |
| REPORT-01 | Phase 4: Persistence and Reporting | Phase 4 |
| AUDIT-01 | Phase 5: Audit and Governance | Phase 5 |
| AUDIT-02 | Phase 5: Audit and Governance | Phase 5 |
| AUDIT-03 | Phase 5: Audit and Governance | Phase 5 |
| AUDIT-04 | Phase 5: Audit and Governance | Phase 5 |
| AUDIT-05 | Phase 5: Audit and Governance | Phase 5 |
| AUDIT-06 | Phase 5: Audit and Governance | Phase 5 |

*Traceability updated 2026-04-21 by roadmapper. All 25 v1 requirements mapped.*
