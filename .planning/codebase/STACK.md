# Technology Stack

**Analysis Date:** 2026-04-21

## Languages

**Primary:**
- Python 3.13+ — all agent logic, skill scripts, shared library, and tests

**Secondary:**
- YAML — agent specs (`agent.yaml`), config (`config/default.yaml`), hooks (`hooks/hooks.yaml`), memory (`memory/memory.yaml`), knowledge index (`knowledge/index.yaml`)
- Markdown — FRET reference (`skills/refine-requirements/references/fret_grammar.md`), skill instructions (`SKILL.md`), project output (`projects/<slug>/PROJECT.md`)
- Bash — session lifecycle hooks (`hooks/scripts/on-start.sh`, `hooks/scripts/on-error.sh`)

## Runtime

**Environment:**
- Python 3.13 (specified in `pyproject.toml` as `requires-python = ">=3.13"`)

**Package Manager:**
- `uv` — dependency management and virtual environment
- Lockfile: `uv.lock` — present and committed

**Virtual Environment:**
- `.venv/` — created by `uv sync`

## Frameworks

**Core:**
- `pydantic` 2.13.3 — validation models for all data writes; all DB writes go through Pydantic models first (`shared/models.py`)
- `openai` 2.32.0 — embedding API client used in `shared/db.py` for vector search

**Agent Framework:**
- `prek` 0.3.9 — gitagent-compatible agent framework (framework-agnostic skill-based agent runtime)

**Testing:**
- `pytest` 9.0.3 — test runner; config via `pyproject.toml`

**Build/Dev:**
- `ruff` 0.15.11 — linter and formatter; run via `uv run ruff check .` and `uv run ruff format .`

## Key Dependencies

**Critical:**
- `sqlite-vec` 0.1.9 — SQLite extension for vector similarity search; loaded dynamically in `shared/db.py` via `sqlite_vec.load(conn)`; enables semantic requirement search
- `pydantic` 2.13.3 — enforces data integrity; no DB write bypasses Pydantic validation
- `openai` 2.32.0 — powers text embedding generation for vector search (`text-embedding-3-small` by default, 1536 dimensions)

**Infrastructure:**
- `sqlite3` (stdlib) — persistence layer; one `.db` file per project at `projects/<slug>/<slug>.db`
- `pathlib` (stdlib) — all file path operations throughout shared library
- `argparse` (stdlib) — CLI interface for all skill scripts

## Configuration

**Environment:**
- `PROJECTS_DIR` (optional) — override default projects storage path; defaults to `<repo-root>/projects/`
- `OPENAI_API_KEY` — required for embedding generation (vector search); sourced from environment
- `EMBEDDING_API_BASE` — defaults to `https://api.openai.com/v1`; override for self-hosted models
- `EMBEDDING_MODEL` — defaults to `text-embedding-3-small`
- `EMBEDDING_DIM` — defaults to `1536`; must match the chosen model's output dimension

**Build:**
- `pyproject.toml` — project metadata, dependencies, Python version constraint
- `config/default.yaml` — runtime defaults: `log_level: info`, `compliance_mode: false`, hook definitions

## Platform Requirements

**Development:**
- Python 3.13+
- `uv` package manager
- SQLite with `sqlite-vec` extension (installed as Python package)
- `OPENAI_API_KEY` environment variable for vector search features

**Production:**
- No web server required — agent is invoked via CLI scripts
- SQLite database per project (file-based, no separate DB server)
- File system write access to `projects/` directory (or `PROJECTS_DIR`)

---

*Stack analysis: 2026-04-21*
