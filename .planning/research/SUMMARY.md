# Project Research Summary

**Project:** requirements-agent
**Domain:** Conversational requirements engineering agent for data science / ML / AI projects
**Researched:** 2026-04-21
**Confidence:** HIGH

---

## Key Findings

### Stack

- The stack is complete for v1. No new runtime dependencies are needed.
- `pytest-cov` is the only recommended dev-dependency addition. `python-dotenv` is optional.
- `prek` is miscategorised as a runtime dependency — it is a git-hook runner. Move to dev or remove.
- The gitagent pattern is a file convention (SKILL.md + agent.yaml), not a Python package. No `pip install gitagent` exists.
- NASA FRET has no Python port. Use LLM + `fret_grammar.md` + lightweight regex validator. Do not attempt a custom parser or JS bridge.
- LLM-in-context classification outperforms any NLP library for the 34-type RequirementType taxonomy. Do not add spaCy, transformers, or NLTK.
- The JSON stdout/stderr pattern in existing skill scripts is correct. Keep `argparse`; do not add Typer or Click.

### Features

- The data model is already at parity with or ahead of commercial RE tools (DOORS NG, Jama, Polarion) on most fields. The v1 gap is entirely in agent behaviour — elicitation flow and FRET workflow — not in schema.
- Table stakes for v1: structured project interview, one-at-a-time requirement capture, interactive type and priority assignment, FRET refinement loop with field-by-field confirmation, persistence behind a user confirmation gate, status report with RAG signal and FRET coverage percentage.
- Primary differentiator: ML-specific elicitation probes for model performance contracts, data quality requirements, fairness criteria, and drift/retraining policies. Triggered by domain keywords, not a fixed checklist.
- Defer to v2+: multi-stakeholder sessions, cross-requirement conflict detection, batch import, EARS notation, traceability matrix, vector-similarity deduplication, meeting integration in reports.
- Anti-features: accepting TBD requirements, bulk requirement dumps without formalisation, silent priority acceptance when all requirements are marked critical.

### Architecture

- Two-tier state model: Claude's context window holds conversation state within a session; SQLite holds only confirmed, complete artefacts. No session state files.
- Three confirmation gates govern all DB writes: (1) project confirmed → `upsert_project`, (2) requirement text confirmed → `insert_requirement`, (3) FRET statement confirmed → `update_requirement fret_statement`. Between gates, all work stays in-context.
- A `projects/.active` sentinel file is needed to enable auto-selection of the last-used project when multiple projects exist. Without it, every multi-project invocation exits with code 1 and forces a mechanical re-invocation loop.
- A new `elicit-requirements` skill is required for v1. `project-update` is a CRUD skill; elicitation is a multi-turn interview skill. They have different responsibilities and must not be merged.
- FRET refinement must be field-by-field, not a single LLM call. Walk fields: COMPONENT → SCOPE → CONDITION → TIMING → RESPONSE. Assemble the complete statement in-context and write it atomically with a single `refine.py apply` call.

### Pitfalls

Seven bugs must be fixed before any v1 flow can run end-to-end. They cascade — a passing test suite today masks all of them through over-permissive MagicMock patching.

1. `C.DB_PATH` does not exist — every `db.py` import raises `AttributeError` at module load time.
2. `import shared.db` binds `shared`, not `db` — every `db.` call in `init.py` raises `NameError`.
3. `db.list_all_projects()` called but only `list_projects(conn)` exists — `AttributeError` at every project resolution.
4. `db.get_project(conn)` called with one argument but signature requires `(conn, project_id)` — `TypeError` on every `ps.resolve()`.
5. `RequirementType` is a Pydantic model not an Enum; `RequirementArea` is referenced but undefined; `req_type.id_prefix` does not exist.
6. `fret_statement` and `fret_fields` exist in `RequirementIn` but are absent from the SQLite schema — `refine apply` writes nothing.
7. `update_requirement` called with wrong argument order in `refine.py` — `project_id` position receives a `dict`.

---

## Stack Recommendations

**Use:**
- Python 3.13, uv, Pydantic 2.x — keep exactly as-is
- stdlib `sqlite3` + `sqlite-vec 0.1.9` — correct choice; do not replace with FAISS, Chroma, or pgvector
- `openai>=2.32.0` with `text-embedding-3-small` — correct; offline fallback via `EMBEDDING_API_BASE` already wired
- `argparse` + JSON stdout/stderr pattern — correct for agent-facing CLI scripts
- LLM-in-context for requirement classification and FRET drafting
- Lightweight regex validator for FRET structure checks (stdlib `re` only)
- `pytest-cov` (dev) — add for DB unit test coverage
- `fret_grammar.md` as LLM prompt context — already correct; do not duplicate inline in SKILL.md

**Do not add:**
- Typer, Click, Rich — human-facing; agent reads stdout programmatically
- spaCy, transformers, NLTK — LLM handles classification; no NLP library needed for v1
- doorstop, strictdoc, reqif — competing architectures; inferior to existing Pydantic + SQLite design
- Custom FRET Python parser or JS bridge — LLM + regex is sufficient for v1
- SQLAlchemy / SQLModel — adds complexity with no benefit for this schema
- A session state file (`.session.json`) — creates a third source of truth; use DB-backed DRAFT status instead

---

## Table Stakes Features for v1

1. **Project interview flow** — structured 5-10 question interview, confirm before saving (INIT-01/02)
2. **Active project auto-selection** — `projects/.active` sentinel so agent does not ask "which project?" on every turn
3. **Requirement elicitation skill** — open narrative → classify type → assign priority → confirm → write (ELICIT-01/02)
4. **FRET refinement loop** — field-by-field, one question per turn, assemble and confirm before `apply` (ELICIT-03)
5. **Persistence confirmation gate** — write to DB only on explicit user confirmation; DRAFT status for resumable partial elicitation
6. **Status report** — project header + RAG signal + requirement counts by status/type + FRET coverage % + critical open list (REPORT-01)
7. **FRET grammar validator** — lightweight regex check on `fret_statement` before accepting (blocks "should", vague components, non-measurable responses)
8. **Standardised `_ok`/`_err` helpers in `shared/`** — imported by all skill scripts; `_err` always writes to stderr

---

## Architecture Decisions

1. **Skill layer** — each skill has a single responsibility and its own `allowed-tools` constraint; skills never import from each other
2. **Shared library** (`shared/`) — all DB writes through `db.py`; all validation through `models.py`; all path resolution through `CONSTANTS.py`; only file that reads env vars
3. **Per-project SQLite** (`projects/<slug>/<slug>.db`) — one DB per project; `projects/.active` tracks last-used slug; `PROJECT.md` is a derived read-only view
4. **Two-tier state** — Claude context = ephemeral conversation state; SQLite = confirmed durable artefacts only
5. **Three-gate persistence model** — project, requirement, and FRET statement each require explicit user confirmation before DB write; no speculative or partial rows
6. **New `elicit-requirements` skill** — separate from `project-update` (CRUD); handles multi-turn interview, type classification, and confirmation before writing
7. **Field-by-field FRET assembly** — multi-turn in-context; single atomic `refine.py apply` call at the end; no eager per-field DB writes
8. **`DRAFT` status on `RequirementStatus`** — enables resumable elicitation without a session file; only confirmed requirements reach `OPEN`

---

## Critical Pitfalls to Avoid

Ordered by blast radius — fixing earlier pitfalls unblocks fixing later ones.

1. **`C.DB_PATH` AttributeError (db.py)** — crashes every `db.py` import. Remove the default; require `C.db_path(slug)` at every call site. (Phase 0)

2. **`import shared.db` NameError (init.py and other skill scripts)** — change to `import shared.db as db`. Audit all `import shared.*` across all skill scripts in one pass. (Phase 0)

3. **Five `db.py` call-site API mismatches** — `list_all_projects()`, `get_project(conn)`, `search_requirements(conn)`, `list_decisions(conn)`, `list_minutes(conn)` all have wrong name or missing arguments. Fix all call sites in a single `db.py` API alignment pass before writing any new code. (Phase 0)

4. **`RequirementType` / `RequirementArea` model inconsistency** — `NameError` on any `RequirementIn` construction; `req_type.id_prefix` AttributeError on every `insert_requirement`. Convert to a `str` Enum using the three-letter code as value; remove all `RequirementArea` references. (Phase 0)

5. **`fret_statement` / `fret_fields` absent from SQLite schema** — `refine apply` writes nothing. Add columns to `bootstrap()`, `insert_requirement`, `update_requirement`, `_row_to_requirement`, and the `updatable` set. (Phase 0 / Phase 2)

6. **Over-permissive test mocks hiding all of the above** — `MagicMock()` auto-creates any attribute. Replace with `create_autospec(db_module)`. Add `test_db.py` using real SQLite via `tmp_path`. (Phase 0)

7. **Single-turn FRET field dump overwhelming the user** — enforce one field per conversational turn; lead with COMPONENT and RESPONSE (required fields); treat SCOPE/CONDITION/TIMING as optional refinements. (Phase 2)

---

## Roadmap Implications

The research implies a 5-phase sequence with a mandatory Phase 0 prerequisite.

### Phase 0: Bug triage (hard prerequisite)
**Rationale:** Seven bugs prevent any skill from running end-to-end. All cascade from `db.py` API inconsistencies and the `RequirementType` model divergence. This is not optional polish — it is a runtime blocker. Do this before writing a single line of new feature code.
**Delivers:** A codebase where `init.py`, `project_session.py`, `req_ops.py`, `refine.py`, and `report.py` all import cleanly and can be invoked without NameError or AttributeError. Tests use `create_autospec` and reflect real API behaviour.
**Fixes:** All 7 critical pitfalls listed above plus Pitfalls 9, 10, 11, 17 (schema and model consistency).
**Research flag:** No research needed — bugs are fully specified in PITFALLS.md with line numbers.

### Phase 1: Project init end-to-end (INIT-01 through INIT-05)
**Rationale:** Project creation is the root dependency for every other skill. The `project-init` skill script exists but has import bugs (fixed in Phase 0); the multi-project flow still needs the `.active` sentinel.
**Delivers:** `init.py new` creates a project, writes `PROJECT.md`, and auto-selects via `.active`. `ps.resolve()` works in single- and multi-project environments. DB unit tests cover all CRUD functions.
**Pitfalls avoided:** Slug collision guard (Pitfall 16), slug not persisted (Pitfall 10).
**Research flag:** Standard patterns — no additional research needed.

### Phase 2: Requirement elicitation and FRET refinement (ELICIT-01 through ELICIT-03, PERSIST-01)
**Rationale:** This is the core v1 value delivery. The `elicit-requirements` skill does not yet exist and must be authored. FRET schema columns must be added. `refine-requirements` SKILL.md needs field-by-field protocol instructions.
**Delivers:** Agent interviews user, extracts one structured requirement, classifies by type and priority, walks FRET fields one at a time, writes confirmed requirement + FRET statement to DB. DRAFT status enables resumable sessions.
**Pitfalls avoided:** Pitfall 21 (single-turn FRET dump), Pitfall 22 (context loss), Pitfall 23 (vague FRET acceptance).
**Research flag:** The `elicit-requirements` SKILL.md content (interview protocol, ML probe triggers, type classification guidance) benefits from deeper research during planning.

### Phase 3: Status report output (REPORT-01)
**Rationale:** Depends on Phase 2 (requirements must exist). `report.py.py` double-extension bug blocks invocation. Several `project_id` call-site bugs in `report.py` are already fixed in Phase 0.
**Delivers:** `report.py generate` produces markdown report with project header, RAG signal, requirement counts, FRET coverage %, critical open list, open decisions, pending actions.
**Research flag:** Standard patterns — SQL aggregation; no additional research needed.

### Phase 4: Hardening and integration test
**Rationale:** Integration test of complete flow: init → elicit → persist → FRET refine → report. Validates all DB writes, `PROJECT.md` regeneration, and two-tier state model under realistic conditions.
**Delivers:** One passing integration test exercising every confirmation gate. FRET grammar validator in `cmd_apply`. `_ok`/`_err` standardised in `shared/`.
**Research flag:** Standard patterns — no additional research needed.

### Phase 5: ML-specific differentiators (v1.5)
**Rationale:** Once the core loop is solid, add ML-specific elicitation probes. These are SKILL.md and agent behaviour changes, not schema changes (schema already supports them).
**Delivers:** Domain-triggered ML probes (accuracy contracts, data quality SLAs, fairness criteria, drift/retraining policies) activated when project domain involves model, prediction, or regulatory context.
**Research flag:** May benefit from `/gsd-research-phase` to source specific elicitation question patterns against NIST AI RMF 1.0 and EU AI Act technical documentation requirements.

### Phase Ordering Rationale

- Phase 0 before everything: the bug cascade means any feature work on top of the current codebase is built on a foundation that cannot run.
- Phase 1 before Phase 2: project creation is the dependency root for elicitation and persistence.
- Phase 2 before Phase 3: the status report is only meaningful when requirements exist.
- Phase 4 after Phases 1-3: integration testing requires all prior phases to be complete.
- Phase 5 last: ML probe behaviour requires a working elicitation loop to augment.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | pyproject.toml and uv.lock read directly; sqlite-vec and OpenAI APIs verified via Context7 |
| Features | HIGH | Schema cross-checked against IEEE 830, IREB CPRE, NIST AI RMF, EU AI Act; commercial tool comparison from training knowledge |
| Architecture | HIGH | All findings from direct codebase analysis; gitagent pattern verified via Context7 |
| Pitfalls | HIGH | All 7 critical bugs confirmed in source code with line numbers |

**Overall confidence:** HIGH

### Gaps to Address

- **`elicit-requirements` SKILL.md content** — the interview protocol needs to be designed during Phase 2 planning. Research identifies what the skill must do but does not draft the SKILL.md.
- **`RequirementType` Enum migration** — converting from Pydantic `BaseModel` to `str` Enum requires auditing all call sites. The correct approach needs a decision during Phase 0 scoping.
- **`fret_grammar.md` type name alignment** — the grammar reference uses category names (`CORE`, `DATA`, `MODEL`, `INFRA`) that do not match actual `RequirementType` codes (`FUN`, `DAT`, `MOD`, `BUS`). Must be corrected before `elicit-requirements` skill is authored.
- **cosine distance for sqlite-vec** — current schema uses default L2 distance; cosine is preferable for semantic text similarity. Schema migration concern for v2, not a v1 blocker.

---

## Sources

### Primary (HIGH confidence)
- `shared/models.py`, `shared/db.py`, `shared/CONSTANTS.py`, `shared/project_session.py` — direct codebase analysis
- Skill scripts: `init.py`, `refine.py`, `req_ops.py`, `report.py.py` — direct codebase analysis
- `skills/refine-requirements/references/fret_grammar.md` — FRET grammar reference
- Context7 `/asg017/sqlite-vec` — vec0 API, KNN query syntax
- Context7 `/openai/openai-python` — embeddings v1.x API
- Context7 `/nasa-sw-vnv/fret` — confirmed JavaScript-only parser, no Python port
- Context7 `/open-gitagent/gitagent` — confirmed convention pattern, not a pip package

### Secondary (MEDIUM confidence)
- IEEE 830-1998 — "shall" statement discipline
- EARS notation (Hull, Jackson & Dick, Springer 2011)
- IREB CPRE Foundation Level Syllabus v1.1 (2022)
- NIST AI RMF 1.0 (2023)
- EU AI Act (2024)
- Zowghi & Coulin (2005) — elicitation technique survey

### Tertiary (MEDIUM-LOW confidence)
- Commercial tool feature set (DOORS NG, Jama Connect, Polarion, Azure DevOps) — training knowledge, no live API verification

---
*Research completed: 2026-04-21*
*Ready for roadmap: yes*
