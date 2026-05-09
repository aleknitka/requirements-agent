# Requirements Agent

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

An AI agent for **requirements engineering** — interviewing stakeholders,
formulating structured requirements, and tracking the open questions, risks,
and follow-ups that arise along the way — backed by a local, audit-friendly
SQLite store exposed through the Model Context Protocol (MCP).

The agent reasons and decides; the MCP layer validates, persists, and audits.
Every meaningful change to a requirement or issue is paired with a structured
diff so the database is always its own complete history of how the project
got to where it is.

---

## What it gives you

- **A relentless interviewer** that turns vague stakeholder input
  ("the system should be fast and secure") into testable, formally-shaped
  requirements with explicit users, triggers, preconditions, postconditions,
  inputs, outputs, business logic, exception handling, and acceptance
  criteria.
- **An issue tracker that is also the agent's todo list.** Ambiguities,
  missing information, risks, blockers, decisions awaiting input, and
  follow-up actions are first-class records, each linked back to the
  requirements they affect.
- **A complete audit trail.** Every requirement edit produces a JSON diff in
  `requirements_changes`; every issue transition produces a row in
  `issue_updates`. There is no supported path that mutates a record without
  also recording why and how.
- **A safe boundary for autonomous work.** The agent never executes raw SQL,
  never opens its own database connection, and never imports ORM models
  directly. It can only reach the data through validated MCP tools, so an
  errant LLM call cannot silently corrupt the system of record.
- **A local, file-based deployment.** A single SQLite file under `data/`
  contains everything; daily log files under `logs/`. Nothing needs to leave
  the machine.

---

## Architecture at a glance

```
┌──────────────────────────┐        MCP (stdio)         ┌──────────────────────────┐
│                          │ ─────────────────────────► │                          │
│       agent_runtime      │                            │     requirements_mcp     │
│                          │ ◄───────────────────────── │                          │
│  identity, skills, model │      validated tools       │  Pydantic + SQLAlchemy   │
│  selection, hooks        │                            │  audit trail, seeds, CLI │
│                          │                            │  Gradio frontend         │
└──────────────────────────┘                            └─────────────┬────────────┘
                                                                      │
                                                         ┌────────────▼────────────┐
                                                         │  data/requirements.db   │
                                                         │  (SQLite, FK-enforced)  │
                                                         └─────────────────────────┘
```

The repository is a single Git repo and a `uv` workspace with two packages:

- **`packages/agent_runtime/`** — agent identity, skill loading, MCP tool
  registration, runtime hooks. Owns *how* the agent thinks; owns nothing
  about persistence.
- **`packages/requirements_mcp/`** — the system of record. Owns the
  SQLAlchemy ORM, Pydantic seed models, idempotent database initialiser,
  audit-trail logic, MCP tool implementations, and the Gradio frontend.
  Everything that touches the database lives here.

Root-level files (`agent.yaml`, `SOUL.md`, `RULES.md`, `skills/`, `tools/`,
`hooks/`, `compliance/`, `memory/`) configure the agent itself.

---

## Persistence model

The schema is split between three concerns: the requirements themselves,
their audit log, and an issue subsystem that doubles as the agent's
operational memory.

| Table | Purpose |
|---|---|
| `requirements` | Current state of every requirement: title, statement, version, author, list-shaped fields (users, triggers, pre/postconditions, inputs, outputs, business logic, exception handling, acceptance criteria) stored as JSON. |
| `requirements_changes` | Append-only audit log. One row per update with a structured `{"field": {"from": ..., "to": ...}}` diff. |
| `requirement_statuses`, `requirement_types` | Controlled vocabularies (11 statuses, 19 types) seeded idempotently from versioned Python lists. |
| `issues` | Open items: ambiguities, missing information, conflicts, risks, blockers, stakeholder questions, decisions, evidence gaps, follow-up tasks. |
| `issue_updates` | Append-only audit + action log: status transitions, emails sent/received, evidence attached, resolutions proposed. |
| `issue_statuses`, `issue_types`, `issue_priorities` | Controlled vocabularies (10 statuses, 11 types, 4 priorities). |
| `requirement_issues` | Typed many-to-many link between issues and the requirements they affect (`related`, `blocks`, `clarifies`, `conflicts_with`, `risk_for`, `caused_by`, `resolved_by`). |

SQLite foreign-key enforcement is turned on for every connection, so invalid
status codes or dangling links are rejected at write time rather than
discovered later. The schema uses a deterministic constraint-naming
convention so a future move to PostgreSQL is a configuration change rather
than a migration project.

Primary keys are short, prefixed slugs rather than opaque UUIDs so an id
in a log line, a tool response, or a UI cell is immediately recognisable:

| Table | Format | Example |
|---|---|---|
| `requirements` | `REQ-<TYPE>-<6>` | `REQ-USR-g4bD84` |
| `requirements_changes` | `REQ-UPDATE-<6>` | `REQ-UPDATE-fg3dcf` |
| `issues` | `ISSUE-<TYPE>-<6>` | `ISSUE-BLK-14gH7d` |
| `issue_updates` | `ISSUE-UPDATE-<6>` | `ISSUE-UPDATE-45hgb3` |

`<TYPE>` is the row's three-letter type code (`USR`, `FUN`, `BLK`, ...);
`<6>` is a 6-character base62 suffix from `secrets.choice`. ID generation
lives in `requirements_mcp.ids`.

---

## Design principles

1. **MCP owns persistence.** The agent never executes SQL, never opens a
   SQLite connection, never imports an ORM model. Every read and write
   crosses a validated tool boundary.
2. **The audit trail is mandatory.** No silent state changes: every
   requirement update produces a `requirements_changes` row, every issue
   action produces an `issue_updates` row, in the same transaction.
3. **Issues are operational memory.** They are not just bugs. They are how
   the agent remembers what it does not yet know, what it is waiting on,
   and what it owes someone.
4. **Local-first, migration-friendly.** SQLite for the file simplicity;
   schema choices kept portable for an eventual PostgreSQL deployment.
5. **Validate everything at the boundary.** Pydantic models on every MCP
   tool input, on every seed declaration, on every Gradio form. SQLAlchemy
   alone is not a validation layer.

---

## Installation

The project uses [`uv`](https://docs.astral.sh/uv/) for dependency and
workspace management.

```bash
git clone https://github.com/aleksander-nitka/requirements-agent.git
cd requirements-agent
uv sync --all-packages
```

Initialise a development database:

```bash
uv run --package requirements-mcp requirements-db-init --db ./data/requirements.db
```

The command creates the schema if missing and seeds the controlled
vocabularies (requirement statuses and types; issue statuses, types,
priorities) idempotently. Re-running it is safe — existing rows are left
untouched, locally-edited descriptions survive.

A `REQUIREMENTS_DB_PATH` environment variable can replace the
`--db` flag; the default when neither is set is `./data/requirements.db`.

Launch the Gradio + MCP app:

```bash
uv run --package requirements-mcp requirements-mcp-server \
  --db ./data/requirements.db --no-init
```

By default the server binds to `127.0.0.1:7860`. The Gradio UI is at
`http://127.0.0.1:7860/` and the MCP endpoint (Server-Sent Events) is at
`http://127.0.0.1:7860/gradio_api/mcp/sse`. All 17 MCP tools are exposed
through both surfaces, backed by the same Python functions — there is no
parallel registration.

Host and port are read in priority order from `--host` / `--port`, the
`REQUIREMENTS_HOST` / `REQUIREMENTS_PORT` environment variables, the
`host` / `port` keys in `config/default.yaml`, and finally the built-in
defaults. To run two checkouts on the same machine, edit
`config/default.yaml` in each one and set a distinct `port:` value.

The UI is organised into three tabs. Both the **Requirements** and **Issues** tabs follow the same single-column inner-tab layout — **Search** / **Create** / **Update** — so the two domains feel symmetric:

- **Requirements**
  - *Search* — free-text query, status / type filters, lookup-by-id; results table; detail panel with audit history below.
  - *Create* — full creation form. Successful submit blanks every field so an accidental second click cannot create a duplicate.
  - *Update* — id input + Load button prefills the form, Save writes through and logs the diff.
- **Issues** — same layout as Requirements, plus issue-specific *Add update* and *Link / unlink* sub-tabs and quick filters for open / blocking issues.
- **Metadata** — read-only browser of every controlled vocabulary (statuses, types, priorities).

The browser title is `<PROJECT_NAME> - requirements db`. `PROJECT_NAME` defaults to `PROJECT` and can be overridden by setting `REQUIREMENTS_PROJECT_NAME` (3–15 chars, `[A-Za-z0-9_-]`) before launch.

UI button click handlers are marked `api_visibility="private"` so they do not appear over MCP — the MCP tool surface stays exactly the canonical 17 tools registered via `gr.api(...)` in `app.py`.

`--port`, `--host`, `--log-level`, `--share`, and `--no-init` are
documented via `requirements-mcp-server --help`.

---

## Tech stack

- **Python 3.13+**
- **SQLAlchemy 2** for ORM, with a future Alembic migration path
- **Pydantic v2** for input validation, seed models, and tool I/O
- **Gradio 6** with `mcp_server=True` — single app for UI + MCP-over-SSE
- **MCP Python SDK** under the hood (used by Gradio's MCP server)
- **loguru** for structured logging — stdout plus a daily file under `logs/`
- **uv** for workspace and lockfile management
- **pytest** + **interrogate** + **ruff** + **bandit** for quality gates

---

## Repository layout

```
requirements-agent/
  agent.yaml                       # agent identity, model preferences, compliance config
  SOUL.md  RULES.md  CLAUDE.md     # agent operating constraints
  skills/  tools/  hooks/          # agent capabilities
  memory/  knowledge/              # agent state
  compliance/  config/             # governance and runtime config
  logs/                            # daily loguru output

  pyproject.toml                   # uv workspace root
  uv.lock

  packages/
    agent_runtime/                 # agent identity & wiring
      pyproject.toml
      src/agent_runtime/
      tests/

    requirements_mcp/              # system of record (this is where the work happens)
      pyproject.toml
      src/requirements_mcp/
        __init__.py                # configure_logging, init_db, resolve_db_path
        config.py                  # CLI > env > default DB path resolver
        cli.py                     # `requirements-db-init` entry point
        app.py                     # `requirements-mcp-server` (Gradio + MCP-over-SSE)
        logging.py                 # loguru: stdout + daily file sink
        db/                        # Base, engine, session factory, init_db
        models/                    # SQLAlchemy ORM (requirement, issue, *_meta, JSONList)
        schemas/                   # Pydantic input/output models for the MCP tools
        services/                  # SQLAlchemy business logic + diff utility
        seeds/                     # Pydantic seed models + idempotent apply_seeds
        tools/                     # Thin tool wrappers used by app.py
        ui/                        # Per-tab Gradio Blocks builders
      tests/                       # 230+ unit tests

  data/                            # SQLite databases (gitignored)
```

---

## Development

```bash
# Run the full test suite
uv run --package requirements-mcp pytest packages/requirements_mcp/tests -v

# Docstring coverage gate (configured at 80% minimum, project sits at 100%)
uv run interrogate packages/requirements_mcp/src

# Lint and format
uv run ruff check .
uv run ruff format .
```

Tests are hermetic: every test that touches the database routes through a
`tmp_path`-scoped fixture, so test runs never write to the real `data/` or
`logs/` directories.

---

## Roadmap

The project is being built in phases that each produce something usable end
to end before adding the next layer.

| Phase | Scope | Status |
|---|---|---|
| **1. Core database & seeds** | SQLAlchemy ORM, Pydantic seeds, idempotent `init_db`, `requirements-db-init` CLI, loguru wiring | ✅ Implemented |
| **2. Requirement tools** | `create_requirement`, `update_requirement`, `get_requirement`, `search_requirements`, `list_requirement_changes`, `list_requirement_statuses`, `list_requirement_types` | ✅ Implemented |
| **3. Issue tools + Gradio MCP app** | `create_issue`, `update_issue`, `get_issue`, `search_issues`, `list_issue_updates`, `list_open_issues`, `list_blocking_issues`, `add_issue_update`, `link_issue_to_requirement`, `unlink_issue_from_requirement` — all 17 tools exposed via a single Gradio app with `mcp_server=True` (UI on `/`, MCP-over-SSE on `/gradio_api/mcp/sse`) | ✅ Implemented |
| **4. UI tabs** | Per-subsystem tabs with search/filter, view-with-history, create, edit, link/unlink, action-log append, and a metadata browser. UI handlers reuse the same tool wrappers as the MCP endpoints; they're marked `api_visibility="private"` so the MCP surface stays exactly the canonical 17 tools. | ✅ Implemented |
| **5. Agent integration** | Skill ↔ MCP wiring, end-to-end stakeholder-interview scenarios, agent autonomy patterns | 🚧 Next |

Future extensions kept explicitly out of scope today but not architecturally
blocked: PostgreSQL deployment, vector search, evidence ingestion, email
ingestion, Slack/Teams integration, multi-user authentication.

---

## License

MIT — see [LICENSE](LICENSE).
