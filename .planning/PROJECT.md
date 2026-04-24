# Requirements Agent

## What This Is

A semi-autonomous requirements engineering agent built on the gitagent architecture. It elicits, classifies, and formalises requirements through conversation, applies formalisation (such as NASA FRET grammar) to make them unambiguous and machine-checkable, then persists them to a structured SQLite database. It is designed to be loaded by Claude Code (or any compatible CLI harness) and operated with minimal human supervision.

## Core Value

An agent that can take fuzzy stakeholder input — via conversation, meetings, or documents — and produce a formally structured, persistently stored, machine-checkable requirement.

## Requirements

### Validated

<!-- Established foundations in current prototype. -->

- ✓ Pydantic data models for requirements, projects, meetings, decisions, and action items — `shared/models.py`
- ✓ Gitagent skill structure (SKILL.md + scripts/ + references/) with `allowed-tools` frontmatter — `skills/`, `agents/`
- ✓ FRET grammar reference integrated into refine-requirements skill — `skills/refine-requirements/references/fret_grammar.md`
- ✓ SQLite schema with sqlite-vec bootstrap for vector search — `shared/db.py`
- ✓ Shared library (CONSTANTS, db, md_writer, project_session) — `shared/`
- ✓ `agent.yaml` top-level spec with model preferences and skill registry

### Active

<!-- v1 goal: agent loads → interviews → creates one FRET-refined requirement → persists to DB. -->

- [ ] **INIT-01**: Project initialisation works end-to-end — `init.py` callable, creates DB + PROJECT.md in `projects`, no errors. Initialisation runs only where there are no projects in specified path or user explicityly requests new project.
- [ ] **INIT-02**: Through an project onboarding skill all required information about the enterprise, tech stack are gathered.
- [ ] **INIT-03**: `db.py` API is consistent — `list_all_projects()`, `get_db(slug)`, and `C.DB_PATH` are resolved
- [ ] **INIT-04**: all db ops have unittests passing - db interactions via cli are sound and working.
- [ ] **INIT-05**: Creation of `PROJECT.md` file alongside the db with information gathered during the project initiation is succesfull - agent is able to create and endit this file, when needed.
- [ ] **ELICIT-01**: Agent interviews user about project background via conversation and captures context
- [ ] **ELICIT-02**: Agent elicits at least one requirement from the interview with the user
- [ ] **ELICIT-03**: Agent refines and spacifies the requirement so that ambiguities are resolved, particurarly agent is able to classify the requirements into types (functional and non-functional + see `RequirementType`)
- [ ] **PERSIST-01**: Refined requirement is written to the project DB and readable back
- [ ] **REPORT-01**: Status report outputs the stored requirements - database export as JSON and/or TOON file.

### Out of Scope

- Meeting transcription / audio processing — v2, needs separate integration
- Document ingestion (PDFs, specs, PRDs) — v2, starts with conversation
- Git / codebase analysis for requirement impact — v3
- Multi-agent orchestration (parallel elicitation) — future
- Vector semantic search — foundation in place but not needed for v1 flow
- Web UI or API layer — CLI-first

## Context

**Architecture:** Gitagent framework — skills are directories with `SKILL.md` + `scripts/` + optional `references/`. Each skill declares `allowed-tools` in frontmatter. The `agent.yaml` at root registers all skills and sets model preferences (`anthropic/claude-opus-4.6`).

**Persistence:** SQLite via `sqlite-vec`. Each project gets its own DB at `projects/<slug>/<slug>.db`. `shared/db.py` handles all CRUD and vector operations. `shared/CONSTANTS.py` is the single source of truth for paths.

**Known bugs to fix before v1:**
1. `db.py` line 92: `get_db(path: str = C.DB_PATH)` — `C.DB_PATH` does not exist in CONSTANTS
2. `init.py`: `import shared.db` binds `shared`, not `db` — should be `import shared.db as db`
3. `init.py`: calls `db.list_all_projects()` but `db.py` exposes `list_projects(conn)` — API mismatch


**Domain:** Data science, ML, and AI projects where requirements are complex, probabilistic, and often under-specified. FRET grammar (NASA) provides the formalisation layer.

**Primary harness:** Claude Code CLI. Agent should also be compatible with other gitagent-compatible harnesses.

## Constraints

- **Tech stack**: Python 3.13+, uv, Pydantic v2, SQLite + sqlite-vec — already established, do not change
- **Architecture**: Gitagent skill pattern — new capabilities go in skills, not monolithic scripts
- **Model**: `anthropic/claude-opus-4.6` as preferred — configured in `agent.yaml`
- **Scope**: CLI-first, no server or API layer in v1
- **Compatibility**: All skill scripts must run standalone via `uv run python <script>` from repo root

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Gitagent architecture | Framework-agnostic, skills are portable, harness-independent | — Pending |
| FRET grammar for formalisation | NASA standard, machine-checkable, unambiguous — better than free-text requirements | — Pending |
| SQLite + sqlite-vec | Local-first, no infra dependency, vector search built in for future semantic queries | — Pending |
| `shared/` as single import boundary | All skills import from one place — schema and path changes propagate everywhere | — Pending |
| Start with conversation, add docs/meetings later | Conversation is the fastest path to v1 end-to-end; other input types are parallel channels | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-21 after initialization*
