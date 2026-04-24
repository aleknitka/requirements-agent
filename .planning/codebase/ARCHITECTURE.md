# Architecture

**Analysis Date:** 2026-04-21

## Pattern Overview

**Overall:** Skill-based CLI agent (gitagent pattern)

**Key Characteristics:**
- Each capability is a self-contained "skill" — a directory with `SKILL.md` (instructions + frontmatter) and `scripts/` (CLI executables)
- All skills share a common library (`shared/`) imported via `sys.path.insert`; no packaging, no imports between skills
- Every skill script is an independent Python CLI that outputs structured JSON to stdout and errors to stderr with non-zero exit
- The LLM agent (driven by `prek` + `agent.yaml`) invokes skills by calling CLI scripts; it does not import Python code directly
- Data is persisted in per-project SQLite files; no shared state between project sessions
- Two agent scopes exist: the root agent (`agent.yaml`) and a specialized sub-agent (`agents/project-initiation-assistant/agent.yaml`)

## Layers

**Agent Specification Layer:**
- Purpose: Defines agent identity, model preferences, skill registry, compliance settings, and runtime parameters
- Location: `agent.yaml` (root agent), `agents/project-initiation-assistant/agent.yaml` (sub-agent)
- Contains: YAML configuration consumed by the `prek` framework
- Depends on: `prek` runtime, skill definitions
- Used by: `prek` framework at runtime

**Skill Layer:**
- Purpose: Domain capability implementations, each with its own instructions and CLI entry points
- Location: `skills/` (5 skills), `agents/project-initiation-assistant/skills/` (1 skill)
- Contains: `SKILL.md` (LLM instructions + allowed-tools), `scripts/*.py` (CLI executables), `references/` (domain reference docs)
- Depends on: `shared/` library (imported via sys.path)
- Used by: LLM agent via CLI invocation

**Shared Library Layer:**
- Purpose: Common persistence, validation, path configuration, and project session management
- Location: `shared/`
- Contains: `CONSTANTS.py`, `models.py`, `db.py`, `md_writer.py`, `project_session.py`
- Depends on: `sqlite3` (stdlib), `pydantic`, `openai`, `sqlite_vec`
- Used by: all skill scripts via `sys.path.insert(0, str(_ROOT / "shared"))`

**Data Layer:**
- Purpose: Per-project SQLite databases with vector search capability
- Location: `projects/<slug>/<slug>.db` and `projects/<slug>/PROJECT.md`
- Contains: requirements, updates log, meeting minutes, decisions, action items, embeddings
- Depends on: `sqlite3`, `sqlite-vec` extension
- Used by: `shared/db.py` exclusively

**Configuration Layer:**
- Purpose: Runtime defaults, session lifecycle hooks, compliance templates, memory management
- Location: `config/default.yaml`, `hooks/hooks.yaml`, `hooks/scripts/`, `compliance/`, `memory/memory.yaml`, `knowledge/index.yaml`
- Contains: YAML config, shell scripts, Markdown compliance templates
- Depends on: Nothing
- Used by: `prek` runtime, agent session lifecycle

## Data Flow

**New Project Creation:**

1. LLM agent interviews user (guided by `project-init` `SKILL.md`)
2. Agent calls `agents/project-initiation-assistant/skills/new-project-initiation/scripts/init.py new --name "..." [options]`
3. `init.py` validates args → builds `ProjectMeta` Pydantic model → calls `db.upsert_project(conn, meta)`
4. `db.py` serializes to SQLite; `project_session.refresh_md(slug, conn)` regenerates `PROJECT.md`
5. Script outputs `{"ok": true, "slug": "...", "db": "...", "md": "..."}` to stdout

**Requirement CRUD:**

1. Agent calls `skills/project-update/scripts/req_ops.py` with subcommand (`add`, `update`, `list`, `show`, `search`)
2. Script validates input → builds `RequirementIn` Pydantic model → calls `db.insert_requirement()` or `db.update_requirement()`
3. `db.py` writes requirement row + `UpdateRecord` diff log; optionally calls `embed()` for vector embedding
4. `project_session.refresh_md()` regenerates `PROJECT.md` with updated stats
5. Script outputs structured JSON result

**FRET Refinement:**

1. Agent calls `skills/refine-requirements/scripts/refine.py pending` to find requirements without FRET statements
2. Agent interacts with user, proposes FRET statement (`[SCOPE] [CONDITION] the COMPONENT shall [TIMING] RESPONSE`)
3. After confirmation, agent calls `refine.py apply --id REQ-X --fret-statement "..." --fret-fields '{...}'`
4. `refine.py` calls `db.update_requirement()` setting `fret_statement` and `fret_fields` fields
5. FRET coverage tracked in `PROJECT.md` stats via `refresh_md()`

**Meeting Logging:**

1. Agent calls `skills/meeting-agent/scripts/meeting.py log` with meeting data as JSON args
2. Script validates via `MinuteIn` Pydantic model → `db.insert_minute()`
3. Decisions extracted as `Decision` objects linked to requirement IDs; action items as `ActionItem` objects
4. `meeting.py integrate` marks a meeting as integrated and updates project status summary

**State Management:**
- Per-project state in SQLite; no in-memory shared state between script invocations
- `PROJECT.md` is a derived read-only view, regenerated on every write via `md_writer.regenerate()`
- The `<!-- NOTES:BEGIN/END -->` block in `PROJECT.md` is the only human-editable section — preserved on regeneration

## Key Abstractions

**RequirementRow / RequirementIn (`shared/models.py`):**
- Purpose: Validated representation of a single requirement
- Examples: `shared/models.py` lines for `RequirementIn`, `RequirementRow`
- Pattern: `RequirementIn` is the write DTO; `RequirementRow` extends it with `id`, `created_at`, `updated_at`, `has_embedding`

**ProjectMeta (`shared/models.py`):**
- Purpose: All project-level metadata (name, phase, objectives, stakeholders, dates, links)
- Pattern: Single row per SQLite DB; updated via `db.upsert_project(conn, meta)`

**UpdateRecord / FieldDiff (`shared/models.py`):**
- Purpose: Immutable audit trail of every requirement change
- Pattern: Written automatically by `db.update_requirement()`; never deleted; `full_snapshot` stored for statuses in `SNAPSHOT_ON_STATUSES`

**Skill (`skills/<name>/` or `agents/<name>/skills/<name>/`):**
- Purpose: Self-contained capability unit — instructions + CLI
- Pattern: `SKILL.md` frontmatter declares `name`, `description`, `allowed-tools`; scripts output JSON

**project_session.resolve() (`shared/project_session.py`):**
- Purpose: Auto-selects active project; all skill scripts call this first
- Pattern: Returns `(slug, conn, meta)` tuple; errors to JSON on stderr + exit 1 if ambiguous

## Entry Points

**Root Agent:**
- Location: `agent.yaml`
- Triggers: Invoked by `prek` framework / gitagent runner
- Responsibilities: Routes user intent to appropriate skill; maintains conversation; enforces compliance settings

**Project Initiation Sub-Agent:**
- Location: `agents/project-initiation-assistant/agent.yaml`
- Triggers: `no_project_detected` or `new_project_requested` delegation triggers from root agent
- Responsibilities: Interviews user for project metadata; calls `init.py new`; hands back to root agent

**Skill CLI Scripts (all entry points below accept `--project <slug>` unless noted):**
- `agents/project-initiation-assistant/skills/new-project-initiation/scripts/init.py` — create/update/list projects
- `skills/project-update/scripts/req_ops.py` — requirement CRUD + history
- `skills/refine-requirements/scripts/refine.py` — FRET grammar application
- `skills/review-requirements/scripts/review.py` — gap/conflict/coverage analysis
- `skills/status-report/scripts/report.py` — health signal + stats report
- `skills/meeting-agent/scripts/meeting.py` — meeting logging and integration

**Minimal Application Entry:**
- Location: `main.py`
- Currently: stub (`print("Hello from requirements-agent!")`)

## Error Handling

**Strategy:** Fail fast with structured JSON output; non-zero exit codes for all errors

**Patterns:**
- All skill scripts define `_err(msg)` → writes `{"ok": false, "error": "<msg>"}` to stderr + `sys.exit(1)`
- All skill scripts define `_ok(data)` → writes `{"ok": true, ...data}` to stdout
- `project_session.resolve()` calls `_err()` for missing/ambiguous project
- Pydantic validation errors bubble up as unhandled exceptions (not yet caught uniformly)
- `db.py` embed failures are caught and logged but do not block requirement saves

## Cross-Cutting Concerns

**Logging:** Structured JSON stdout/stderr per script invocation; no persistent application log file; audit logging by `prek` runtime per `agent.yaml` spec

**Validation:** All writes go through Pydantic models in `shared/models.py` before reaching `db.py`; no raw dict writes to SQLite

**Authentication:** None at the application level; OpenAI API key via environment variable for embeddings

**FRET Grammar:** Domain constraint applied by `refine-requirements` skill; full grammar reference at `skills/refine-requirements/references/fret_grammar.md`; structure: `[SCOPE] [CONDITION] the COMPONENT shall [TIMING] RESPONSE`

**Compliance:** `agent.yaml` declares `risk_tier: standard`; `compliance/risk-assessment.md` documents risk assessment; PII handling set to `redact`; `RULES.md` defines behavioral constraints for the LLM

---

*Architecture analysis: 2026-04-21*
