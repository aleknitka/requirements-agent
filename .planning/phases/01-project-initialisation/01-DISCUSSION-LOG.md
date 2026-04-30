# Phase 1: Project Initialisation — Discussion Log

**Date:** 2026-04-30
**Status:** Complete

---

## Areas Discussed

### Structural Change: Single-Project Model
User initiated a significant scope change. Phase 1 pivots from multi-project management to single-project technical setup. Key revelation: the agent always operates on one project per instance — slugs, `.active`, and `--project` flags are unnecessary complexity.

### Project Path
- **Options presented:** Flat `project/` dir / Configurable via env var / Current working directory
- **Selected:** Flat `project/` dir at repo root, with `PROJECT_DIR` env var override
- **Notes:** Simple, no slug needed. `project/project.db`, `project/PROJECT.md`, `project/logs/`, `project/notes/`

### sqlite-vec Toggle
- **Options presented:** Skip silently / Disable at schema level / Separate install
- **Selected:** Skip silently — no vec0 table, no embeddings columns if user declines
- **Notes:** Keeps the codebase clean; semantic search returns empty rather than erroring

### Slug Removal Scope
- **Options presented:** Phase 1 — do it now / Separate cleanup phase / Keep as internal detail
- **Selected:** Phase 1 — rip out all slug/multi-project code as part of this phase
- **Notes:** CONSTANTS.py, project_session.py, init_project.py, all `--project` flags

### Setup CLI — Second Run Behaviour
- **Options presented:** Guard + abort / Re-run interactively / Silent no-op
- **Selected:** Guard + abort — print clear message, exit non-zero
- **Notes:** Message names `init-project reset` for discoverability (not implemented in Phase 1)

### .gitignore Scope
- **Options presented:** project/logs/ / project/notes/ / project/project.db / project/*.db
- **Selected:** project/logs/, project/notes/, project/*.db (broader glob preferred)

### OpenTelemetry in Phase 1
- **Options presented:** Ask + store flag / Skip entirely / Implement basic OTLP export
- **Selected:** Ask the question, store the flag in config/project.yaml. No implementation.

### Setup Config Format
- **Options presented:** project/setup.json / Settings table in DB / config/project.yaml
- **Selected:** config/project.yaml — consistent with existing config/default.yaml

### ROADMAP Plans
- **Options presented:** Let the planner rewrite / Update ROADMAP.md now
- **Selected:** Let the planner produce fresh plans from CONTEXT.md

### DB Schema
- User explicitly flagged this as a **research task** — re-evaluate all tables and columns for the single-project model before planning.

---

## Deferred Ideas
- `init-project reset` — named in guard message, implement later
- OpenTelemetry implementation — flag only in Phase 1
- `init-project update` — change setup config post-init

---

*Logged: 2026-04-30*
