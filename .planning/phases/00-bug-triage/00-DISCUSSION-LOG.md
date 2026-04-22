# Phase 0: Bug Triage - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 0 - Bug Triage
**Areas discussed:** RequirementType overhaul, fret_statement/fret_fields schema, slug lookup API, Test scope

---

## RequirementType overhaul

| Option | Description | Selected |
|--------|-------------|----------|
| Keep metadata list (Recommended) | Rename REQUIREMENT_TYPES to RequirementTypeMeta. str Enum uses 3-letter codes. Future reporting/UI can look up names. | ✓ |
| Drop metadata now | Remove REQUIREMENT_TYPES entirely in Phase 0. | |
| You decide | Claude picks cleanest approach. | |

**User's choice:** Keep metadata list — rename to RequirementTypeMeta (NamedTuple or dataclass)
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Required — no default (Recommended) | Caller must always specify type. | |
| Default to FUN (Functional) | Most requirements will be functional. | ✓ |
| Default to NFR (Non-Functional) | Conservative default. | |

**User's choice:** Default to FUN (Functional)
**Notes:** —

---

## fret_statement/fret_fields schema

| Option | Description | Selected |
|--------|-------------|----------|
| ALTER TABLE ADD COLUMN (Recommended) | Safe for existing DBs, no data loss. | |
| Just fix the schema string | New-DB only fix. | |
| Remove from model now, re-add in Phase 3 | Clean slate — Phase 3 owns FRET formalisation end-to-end. | ✓ |

**User's choice:** Remove fret_statement/fret_fields from RequirementIn/RequirementRow and SQLite schema in Phase 0. Phase 3 introduces them properly.
**Notes:** User clarified: "phase 3 is where we will introduce formalisation methods and fret is one of them"

---

## slug lookup API

| Option | Description | Selected |
|--------|-------------|----------|
| Add slug column, add get_project_by_slug() (Recommended) | UUID remains PK, slug is secondary UNIQUE column. | ✓ |
| Make slug the primary key | Simpler for CLI but breaks if slug changes. | |
| Add slug column, rename get_project parameter | UUID internal only. | |

**User's choice:** Add slug column + get_project_by_slug() alongside existing get_project()
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-derived from name (Recommended) | slugify(name) computed in upsert_project() if slug is empty. | ✓ |
| Always passed explicitly | More boilerplate for callers. | |

**User's choice:** Auto-derived from name using C.slugify()
**Notes:** —

---

## Test scope

| Option | Description | Selected |
|--------|-------------|----------|
| DB CRUD functions only (Recommended) | Fast, focused data layer tests. | |
| DB CRUD + import chain verification | CRUD + subprocess import smoke tests. | |
| Full end-to-end CLI test | subprocess CLI invocations (--help exits 0, init.py new creates files). | ✓ |

**User's choice:** Full end-to-end CLI tests
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Replace with real-SQLite tests (Recommended) | Fresh start, tmp_path, no MagicMock. | ✓ |
| Fix in place (remove bad mocks) | Keep test_init.py structure, strip bad patches. | |

**User's choice:** Replace test_init.py with new real-SQLite tests
**Notes:** —

---

## Claude's Discretion

- NamedTuple vs dataclass for RequirementTypeMeta
- UNIQUE constraint on slug column in projects table

## Deferred Ideas

- fret_statement/fret_fields — Phase 3 (FRET formalisation)
- update_requirement updatable set for FRET fields — Phase 3
