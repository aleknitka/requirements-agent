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

# Generate API docs (lazydocs → docs/)
uv run --with lazydocs lazydocs --output-path docs/ requirements_agent_tools
# Note: run `git add docs/` after this if committing docs changes

# Install pre-commit hooks (one-time setup per clone)
uv run pre-commit install

# Run all pre-commit hooks manually
uv run pre-commit run --all-files
```

## Architecture

### Gitagent
This agent takes advantage of the [gitagent](https://github.com/open-gitagent/gitagent) which is a framework-agnostic method of developing agents.

### Agent Configuration

`agent.yaml` is the top-level agent spec: model preferences, skills list, compliance/governance settings, and runtime parameters. The agent uses `anthropic/claude-opus-4.6` as preferred model.

#### Gitagent Fallback Pattern

The gitagent harness reads `agent.yaml` and selects the next model on failure. Current
fallback list:
1. `anthropic/claude-opus-4.6` (preferred)
2. `openai/gpt-5.2`
3. `openai/gpt-oss-20b`
4. `google/gemma-4-31b`

If the preferred model is unavailable or returns an error, the harness automatically
retries with the next entry in the list. No code change is required to change the
fallback order — edit `agent.yaml` under `model.fallback`.

**Note:** The fallback model IDs above reflect the current `agent.yaml` configuration
but may not correspond to currently available production models. Verify availability
against your provider contracts before production use.

### Skills (`skills/`)

Each skill is a directory with `SKILL.md` (frontmatter + instructions) and optionally `references/`. CLI logic for a skill lives in `src/requirements_agent_tools/<module>.py` and is wired as a `[project.scripts]` entry point in `pyproject.toml`. The six skills are:

- **project-init** / **project-update** — project lifecycle management
- **refine-requirements** — applies FRET grammar interactively; invoked via `uv run refine`; full grammar reference at `skills/refine-requirements/references/fret_grammar.md`
- **review-requirements** — requirement quality review
- **status-report** — project status reporting
- **meeting-agent** — meeting minutes, decisions, action items

Skills declare `allowed-tools` in their frontmatter to restrict what the agent may do.

### Package (`src/requirements_agent_tools/`)

All logic lives in the installed `requirements_agent_tools` package. Import directly
from the submodule you need. The seven entry points are:

| Entry point | Module | Subcommands |
|-------------|--------|-------------|
| `uv run init-project` | `init_project:main` | `new`, `list`, `update` |
| `uv run refine` | `refine:main` | `pending`, `show`, `apply`, `coverage` |
| `uv run req-ops` | `req_ops:main` | `add`, `update`, `get`, `list`, `search`, `history`, `vector` |
| `uv run review` | `review:main` | `gaps`, `conflicts`, `coverage`, `report` |
| `uv run report` | `report:main` | `generate`, `save` |
| `uv run meeting` | `meeting:main` | `log`, `get`, `list`, `decisions`, `update_decision`, `close_action`, `integrate` |
| `uv run db` | `db.cli:cli` | `req`, `project`, `minute`, `update` |

`--project <slug>` is an optional global flag on `refine`, `req-ops`, `review`, `report`,
`meeting`. On `db` it is a required option (`--project SLUG` before the subcommand).

Key modules:

- **`CONSTANTS.py`** — single source of truth for paths (`PROJECTS_DIR`), embedding config,
  and path helper functions (`project_dir`, `db_path`, `md_path`, `slugify`)
- **`models.py`** — Pydantic validation models (`RequirementIn`, `RequirementRow`,
  `ProjectMeta`, `MinuteIn`, `UpdateRecord`, etc.); nothing writes to the DB without going
  through these first
- **`db/`** — SQLite persistence layer split into focused submodules: `connection`
  (open/bootstrap), `schema` (DDL + reference seeds), `projects`, `requirements`, `minutes`,
  `updates`, `embeddings` (sqlite-vec), plus private `_serialization` and `_logging`
  helpers. All log calls go through loguru — stderr (level via `REQ_AGENT_LOG_LEVEL`,
  default `INFO`) plus a per-project daily-rotated file at
  `projects/<slug>/logs/db-{date}.log` at `DEBUG`. Import directly from the submodule you
  need (`from requirements_agent_tools.db.requirements import insert_requirement`); the
  package does not re-export.
- **`project_md.py`** — generates and maintains `PROJECT.md` (auto header + protected
  `<!-- NOTES:BEGIN/END -->` block)
- **`project_session.py`** — `resolve(slug_or_name)` auto-selects the active project;
  `refresh_md()` should be called after every write

### Supporting Directories

- `compliance/` — risk assessment, regulatory map, validation schedule templates
- `config/default.yaml` — runtime defaults (`log_level`, `compliance_mode`)
- `hooks/hooks.yaml` — `on_session_start` and `on_error` hooks pointing to `hooks/scripts/`
- `knowledge/index.yaml` — knowledge document index (currently empty)
- `RULES.md` — behavioral constraints for the agent (escalation, PII, audit trail)
- `SOUL.md` — agent identity and communication style

### Data Layer

Requirements are stored in SQLite (via `sqlite-vec`). The `uv run refine` CLI outputs structured JSON to stdout, errors to stderr with non-zero exit code. All commands accept an optional `--project <slug>` to target a specific project session.

## Skill Development Convention

When adding a new skill:
1. Create `skills/<name>/SKILL.md` with frontmatter fields: `name`, `description`, `license`, `allowed-tools`, and `metadata` (author, version, category).
2. Place reference material under `skills/<name>/references/`. CLI logic goes in `src/requirements_agent_tools/<name>.py` and is wired as a `[project.scripts]` entry point in `pyproject.toml`.
3. Register the skill name in `agent.yaml` under `model.skills`.
