# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Enterprise agent for autonomous requirements management (elicitation, refinement, updates) in data science, ML, and AI projects. The agent applies formal FRET (NASA) grammar to make requirements unambiguous and machine-checkable.

## Commands

```bash
# Install dependencies
uv sync

# Run linter
uv run ruff check .
uv run ruff format .

# Run tests
uv run pytest

# Run a single test
uv run pytest path/to/test_file.py::test_name

```

## Architecture

### Gitagent
This agent takes advantage of the [gitagent](https://github.com/open-gitagent/gitagent) which is a framework-agnostic method of developing agents.

### Agent Configuration

`agent.yaml` is the top-level agent spec: model preferences, skills list, compliance/governance settings, and runtime parameters. The agent uses `anthropic/claude-opus-4.6` as preferred model.

### Skills (`skills/`)

Each skill is a directory with `SKILL.md` (frontmatter + instructions) and optionally `scripts/` and `references/`. The six skills are:

- **project-init** / **project-update** — project lifecycle management
- **refine-requirements** — applies FRET grammar interactively; has a CLI at `skills/refine-requirements/scripts/refine.py` and full grammar reference at `skills/refine-requirements/references/fret_grammar.md`
- **review-requirements** — requirement quality review
- **status-report** — project status reporting
- **meeting-agent** — meeting minutes, decisions, action items

Skills declare `allowed-tools` in their frontmatter to restrict what the agent may do.

### Shared Library (`shared/`)

All skills import from `shared/` using `sys.path.insert(0, str(_ROOT / "shared"))`. The five modules are:

- **`CONSTANTS.py`** — single source of truth for paths (`PROJECTS_DIR`), embedding config, and path helper functions (`project_dir`, `db_path`, `md_path`, `slugify`)
- **`models.py`** — Pydantic validation models (`RequirementIn`, `RequirementRow`, `ProjectMeta`, `MinuteIn`, `UpdateRecord`, etc.); nothing writes to the DB without going through these first
- **`db/`** — SQLite persistence layer split into focused submodules: `connection` (open/bootstrap), `schema` (DDL + reference seeds), `projects`, `requirements`, `minutes`, `updates`, `embeddings` (sqlite-vec), plus private `_serialization` and `_logging` helpers. A click CLI is exposed via `db = "requirements_agent_tools.db.cli:cli"` (full CRUD over a `--project <slug>` DB). All log calls go through loguru — stderr (level via `REQ_AGENT_LOG_LEVEL`, default `INFO`) plus a per-project daily-rotated file at `projects/<slug>/logs/db-{date}.log` at `DEBUG` (sink installed lazily by `get_db()`). Import directly from the submodule you need (`from requirements_agent_tools.db.requirements import insert_requirement`); the package does not re-export.
- **`md_writer.py`** — generates and maintains `PROJECT.md` (auto header + protected `<!-- NOTES:BEGIN/END -->` block)
- **`project_session.py`** — `resolve(slug_or_name)` auto-selects the active project; `refresh_md()` should be called after every write

### Supporting Directories

- `compliance/` — risk assessment, regulatory map, validation schedule templates
- `config/default.yaml` — runtime defaults (`log_level`, `compliance_mode`)
- `hooks/hooks.yaml` — `on_session_start` and `on_error` hooks pointing to `hooks/scripts/`
- `knowledge/index.yaml` — knowledge document index (currently empty)
- `RULES.md` — behavioral constraints for the agent (escalation, PII, audit trail)
- `SOUL.md` — agent identity and communication style

### Data Layer

Requirements are stored in SQLite (via `sqlite-vec`). The `refine.py` CLI outputs structured JSON to stdout, errors to stderr with non-zero exit code. All commands accept an optional `--project <slug>` to target a specific project session.

## Known Issues

- `skills/status-report/scripts/report.py.py` has a double `.py` extension (root-owned file — rename to `report.py` when possible). The `SKILL.md` and README both reference it correctly as `report.py`.

## Skill Development Convention

When adding a new skill:
1. Create `skills/<name>/SKILL.md` with frontmatter fields: `name`, `description`, `license`, `allowed-tools`, and `metadata` (author, version, category).
2. Place CLI scripts under `skills/<name>/scripts/` and reference material under `skills/<name>/references/`.
3. Register the skill name in `agent.yaml` under `model.skills`.
