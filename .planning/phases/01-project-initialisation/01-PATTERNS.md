# Phase 1: Project Initialisation - Pattern Map

**Mapped:** 2026-04-30
**Files analyzed:** 16 new/modified files
**Analogs found:** 14 / 16

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/requirements_agent_tools/CONSTANTS.py` | config/utility | — | `src/requirements_agent_tools/CONSTANTS.py` (current) | self (rewrite) |
| `src/requirements_agent_tools/project_session.py` | utility | request-response | `src/requirements_agent_tools/project_session.py` (current) | self (rewrite) |
| `src/requirements_agent_tools/init_project.py` | CLI/command | request-response | `src/requirements_agent_tools/init_project.py` (current) | self (rewrite) |
| `src/requirements_agent_tools/db/schema.py` | config/DDL | — | `src/requirements_agent_tools/db/schema.py` (current) | self (surgical) |
| `src/requirements_agent_tools/db/connection.py` | service | CRUD | `src/requirements_agent_tools/db/connection.py` (current) | self (surgical) |
| `src/requirements_agent_tools/db/projects.py` | service | CRUD | `src/requirements_agent_tools/db/projects.py` (current) | self (surgical) |
| `src/requirements_agent_tools/db/_serialization.py` | utility | transform | `src/requirements_agent_tools/db/_serialization.py` (current) | self (surgical) |
| `src/requirements_agent_tools/models.py` | model | — | `src/requirements_agent_tools/models.py` (current) | self (surgical) |
| `src/requirements_agent_tools/project_md.py` | service | file-I/O | `src/requirements_agent_tools/project_md.py` (current) | self (surgical) |
| `src/requirements_agent_tools/project_md_cli.py` | CLI/command | request-response | `src/requirements_agent_tools/refine.py` | role-match |
| `refine.py`, `req_ops.py`, `review.py`, `report.py`, `meeting.py`, `db/cli.py` | CLI/command | request-response | `src/requirements_agent_tools/refine.py` | exact (pattern to remove) |
| `config/project.yaml` | config | — | `config/default.yaml` | role-match |
| `tests/test_setup.py` | test | — | `tests/test_init.py` | role-match |
| `tests/test_db.py` | test | — | `tests/test_db.py` (current) | self (surgical) |
| `tests/test_slug_infrastructure.py` | test | — | — | DELETE |
| `tests/test_init.py` | test | — | `tests/test_init.py` (current) | self (rewrite) |
| `pyproject.toml` | config | — | `pyproject.toml` (current) | self (1-line add) |

---

## Pattern Assignments

### `src/requirements_agent_tools/CONSTANTS.py` (config/utility — rewrite)

**Analog:** current `CONSTANTS.py`

**Imports pattern** (lines 1-14):
```python
"""
CONSTANTS.py — single source of truth for all configuration.

PROJECT_DIR defaults to a path relative to this file's location
(requirements-agent/project/), so scripts work correctly regardless
of the working directory they are launched from.
"""

import os
from pathlib import Path
```

**Core pattern to replace** (lines 17-31, current):
```python
# REMOVE: PROJECTS_DIR and all slug helpers
PROJECTS_DIR: Path = (
    Path(os.environ["PROJECTS_DIR"])
    if "PROJECTS_DIR" in os.environ
    else _AGENT_ROOT / "projects"
)
# REMOVE: project_dir(slug), db_path(slug), md_path(slug), slugify()
```

**New flat-constant pattern** (from RESEARCH.md Pattern 1):
```python
# _AGENT_ROOT is already correct; keep as-is
_AGENT_ROOT: Path = Path(__file__).resolve().parents[2]

# REPLACE with flat constants — override via PROJECT_DIR env var
PROJECT_DIR: Path = (
    Path(os.environ["PROJECT_DIR"])
    if "PROJECT_DIR" in os.environ
    else _AGENT_ROOT / "project"
)

DB_PATH: Path = PROJECT_DIR / "project.db"
MD_PATH: Path = PROJECT_DIR / "PROJECT.md"
```

**Keep unchanged** (lines 35-47):
```python
# These are unchanged — embedding config and update log policy stay
EMBEDDING_API_BASE: str = os.getenv("EMBEDDING_API_BASE", "https://api.openai.com/v1")
EMBEDDING_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1536"))

SNAPSHOT_ON_STATUSES: set[str] = {"in-progress", "done", "rejected"}

MD_NOTES_BEGIN: str = "<!-- NOTES:BEGIN -->"
MD_NOTES_END: str = "<!-- NOTES:END -->"
```

---

### `src/requirements_agent_tools/project_session.py` (utility — rewrite)

**Analog:** current `project_session.py`

**Current imports to keep** (lines 1-9):
```python
from __future__ import annotations

import sqlite3
from typing import Optional  # remove after rewrite

from . import CONSTANTS as C
from ._cli_io import err as _err
from .db.connection import get_db
```

**Remove:** import of `get_project`, `ProjectMeta` (no longer returned)

**New `get_project_conn()` pattern** (from RESEARCH.md Pattern 2):
```python
def get_project_conn() -> sqlite3.Connection:
    """Open the single project DB. Exits with error if not initialised.

    Returns:
        An open sqlite3.Connection to the project database.
    """
    if not C.DB_PATH.exists():
        _err("No project found. Run 'uv run init-project setup' first.")
    return get_db(str(C.DB_PATH))
```

**Remove entirely:** `resolve(slug_or_name)` function (lines 24-46 of current file).

**Docstring module-level update:** Remove references to `slug_or_name`, `.active` sentinel, and multi-project.

---

### `src/requirements_agent_tools/init_project.py` (CLI/command — rewrite)

**Analog:** current `init_project.py`

**Imports pattern** (lines 1-21, adapted):
```python
"""
init_project.py — project initialisation.

Commands
────────
  setup    Create project/ directory tree, bootstrap DB, write config/project.yaml
"""

import argparse
from pathlib import Path

import click
import yaml

from . import CONSTANTS as C
from ._cli_io import err as _err
from ._cli_io import ok as _ok
from .db.connection import bootstrap, get_db
```

**Guard pattern** (D-07 — check before any work):
```python
def cmd_setup(args: argparse.Namespace) -> None:
    """Create the project directory, bootstrap the DB, and write setup config.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    if C.PROJECT_DIR.exists():
        _err(
            "Project already initialised. "
            "Use 'init-project reset' to start fresh."
        )
```

**Interactive prompt pattern** (click.confirm, from RESEARCH.md Pattern 5):
```python
    # Ask setup questions
    sqlite_vec = click.confirm(
        "Enable vector embeddings (requires sqlite-vec)?", default=False
    )
    otel = click.confirm(
        "Enable OpenTelemetry tracing (stores flag only)?", default=False
    )

    # .gitignore — individual confirm per entry
    gitignore_entries: list[str] = []
    for entry, description in [
        ("project/logs/", "project/logs/ (log files)"),
        ("project/notes/", "project/notes/ (notes directory)"),
        ("project/*.db", "project/*.db (database file)"),
    ]:
        if click.confirm(f"  Add {description} to .gitignore?", default=True):
            gitignore_entries.append(entry)
```

**Directory scaffold pattern** (D-06):
```python
    # Create directory tree — only cmd_setup() should mkdir
    C.PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    (C.PROJECT_DIR / "logs").mkdir(exist_ok=True)
    (C.PROJECT_DIR / "notes").mkdir(exist_ok=True)
```

**DB bootstrap pattern** (D-06 + RESEARCH.md Pattern 3):
```python
    conn = get_db(str(C.DB_PATH))
    bootstrap(conn, sqlite_vec_enabled=sqlite_vec)
    conn.close()
```

**Config write pattern** (D-11, yaml.safe_dump — from `config/default.yaml` analogy):
```python
    _CONFIG_PATH = C._AGENT_ROOT / "config" / "project.yaml"
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {"sqlite_vec": sqlite_vec, "otel_enabled": otel},
            f,
            default_flow_style=False,
        )
```

**`.gitignore` idempotent-append pattern** (D-11, from RESEARCH.md anti-patterns):
```python
    gitignore_path = C._AGENT_ROOT / ".gitignore"
    if gitignore_entries:
        existing = (
            gitignore_path.read_text(encoding="utf-8")
            if gitignore_path.exists()
            else ""
        )
        to_add = [e for e in gitignore_entries if e not in existing]
        if to_add:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# requirements-agent project\n")
                for entry in to_add:
                    f.write(f"{entry}\n")
```

**Success output pattern** (matches `_ok()` contract from `_cli_io.py`):
```python
    _ok({
        "project_dir": str(C.PROJECT_DIR),
        "db": str(C.DB_PATH),
        "config": str(_CONFIG_PATH),
        "sqlite_vec": sqlite_vec,
        "otel_enabled": otel,
        "next_step": "Run 'uv run req-ops add' to add requirements.",
    })
```

**Parser pattern** (argparse, from current `init_project.py` lines 149-201):
```python
def build_parser() -> argparse.ArgumentParser:
    """Build and return the init-project argument parser."""
    p = argparse.ArgumentParser(description="Project initialisation")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("setup")   # only subcommand in Phase 1
    return p


def main():
    """Entry point for the init-project CLI."""
    args = build_parser().parse_args()
    {"setup": cmd_setup}[args.command](args)
```

---

### `src/requirements_agent_tools/db/schema.py` (config/DDL — surgical)

**Analog:** current `db/schema.py`

**Change 1 — remove `slug` column from `projects` DDL** (lines 27-28 of current):
```python
# REMOVE this line from SCHEMA_SQL projects table:
    slug              TEXT NOT NULL DEFAULT '',
```

**Change 2 — split SCHEMA_SQL into BASE + VEC** (lines 72-77 of current):
```python
# SPLIT: extract the vec virtual table block into its own constant
# Current (lines 72-77 of schema.py):
CREATE VIRTUAL TABLE IF NOT EXISTS req_embeddings
USING vec0(
    requirement_id TEXT PRIMARY KEY,
    embedding      FLOAT[{C.EMBEDDING_DIM}]
);

# Becomes two constants:
BASE_SCHEMA_SQL: str = f"""
-- ... everything in SCHEMA_SQL except the CREATE VIRTUAL TABLE block ...
"""

VEC_SCHEMA_SQL: str = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS req_embeddings
USING vec0(
    requirement_id TEXT PRIMARY KEY,
    embedding      FLOAT[{{C.EMBEDDING_DIM}}]
);
"""
```

**Keep unchanged:** `seed_reference_tables()` function (lines 143-167), all reference table DDL, all indexes.

**Remove migration block** from `connection.py bootstrap()` that adds `slug` column — after the schema no longer has `slug`, the `ALTER TABLE projects ADD COLUMN slug` migration block (lines 66-71 of `connection.py`) must be removed entirely.

---

### `src/requirements_agent_tools/db/connection.py` (service — surgical)

**Analog:** current `db/connection.py`

**Current `get_db()` pattern to adapt** (lines 14-50):
```python
def get_db(path: str) -> sqlite3.Connection:
    """Open (or create) a SQLite database and load ``sqlite-vec``.
    ...
    """
    db_file = Path(path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    add_project_log_sink(db_file.parent)
    logger.debug("Opening DB at {}", path)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        import sqlite_vec
        sqlite_vec.load(conn)
    except Exception as e:  # noqa: BLE001
        logger.error("sqlite-vec extension cannot be loaded")
        raise RuntimeError(f"Could not load sqlite-vec extension: {e}\n") from e

    bootstrap(conn)
    return conn
```

**New pattern — conditional sqlite-vec load** (RESEARCH.md Pattern 3 + Pitfall 1):
```python
def get_db(path: str, sqlite_vec_enabled: bool = False) -> sqlite3.Connection:
    """Open (or create) a SQLite database. Loads sqlite-vec only when enabled.

    Args:
        path: Filesystem path to the SQLite file.
        sqlite_vec_enabled: Whether to load the sqlite-vec extension.
            Read from config/project.yaml by callers that know the config.

    Returns:
        An open sqlite3.Connection. Caller owns the lifetime.

    Raises:
        RuntimeError: If sqlite_vec_enabled is True but the extension cannot load.
    """
    db_file = Path(path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    add_project_log_sink(db_file.parent)
    logger.debug("Opening DB at {}", path)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    if sqlite_vec_enabled:
        try:
            import sqlite_vec
            sqlite_vec.load(conn)
        except Exception as e:  # noqa: BLE001
            logger.error("sqlite-vec extension cannot be loaded")
            raise RuntimeError(f"Could not load sqlite-vec extension: {e}\n") from e

    bootstrap(conn, sqlite_vec_enabled=sqlite_vec_enabled)
    return conn
```

**New `bootstrap()` signature** (RESEARCH.md Pattern 3):
```python
def bootstrap(conn: sqlite3.Connection, sqlite_vec_enabled: bool = False) -> None:
    """Create tables and seed reference data if absent.

    Args:
        conn: An open SQLite connection.
        sqlite_vec_enabled: When True, also creates the vec0 virtual table.
    """
    conn.executescript(schema.BASE_SCHEMA_SQL)
    if sqlite_vec_enabled:
        conn.executescript(schema.VEC_SCHEMA_SQL)
    conn.commit()
    schema.seed_reference_tables(conn)
    logger.debug("Bootstrap complete")
```

**Remove entirely from `bootstrap()`:** The `ALTER TABLE projects ADD COLUMN slug` migration block (lines 66-71) and the `singleton` migration block (lines 73-88) — these are no longer needed once the schema is canonical.

---

### `src/requirements_agent_tools/db/projects.py` (service — surgical)

**Analog:** current `db/projects.py`

**Remove entirely:**
- `discover_projects()` function (lines 127-164) — scans `PROJECTS_DIR/<slug>/` which no longer exists
- `get_project_by_slug()` function (lines 113-118)
- `if not meta.slug: meta.slug = C.slugify(meta.name)` block (lines 34-35)

**Remove from `upsert_project()` SQL** — `slug` column in INSERT and UPDATE SET:
```python
# Current INSERT columns (line 39-44) — remove :slug
INSERT INTO projects (
    project_id, slug, name, code, ...   ← remove slug
) VALUES (
    :project_id,:slug,:name,:code,...   ← remove :slug
)
ON CONFLICT(project_id) DO UPDATE SET
    slug=excluded.slug,                 ← remove this line
    name=excluded.name, ...
```

**Remove from dict literal** (lines 69-70):
```python
# REMOVE: "slug": meta.slug,
```

**Remove from logger.info** (line 96):
```python
# Change: logger.info("Upserted project id={} slug={}", meta.project_id, meta.slug)
# To:     logger.info("Upserted project id={}", meta.project_id)
```

**Keep unchanged:** `upsert_project()` structure, `get_project()`, `list_projects()`, all imports except `C.slugify` usage.

---

### `src/requirements_agent_tools/db/_serialization.py` (utility — surgical)

**Analog:** current `db/_serialization.py`

**Remove from `row_to_project()`** (lines 108-134) — `slug` mapping:
```python
# Current line 113 in row_to_project():
        slug=d.get("slug", ""),
# REMOVE this line entirely
```

**Keep unchanged:** all other deserialization functions, all imports.

---

### `src/requirements_agent_tools/models.py` (model — surgical)

**Analog:** current `models.py`

**Remove from `ProjectMeta`** (lines 552-553):
```python
# REMOVE these two lines from ProjectMeta:
    slug: str = ""  # derived from name, used for filenames
```

**Remove from docstring** (lines 530-532): Remove the `slug` attribute documentation line.

**Keep unchanged:** all other fields, all other models, all enums.

---

### `src/requirements_agent_tools/project_md.py` (service — surgical)

**Analog:** current `project_md.py`

**Remove `slug` parameter from `save()` and `append_section()`** — replace `C.md_path(slug)` with `C.MD_PATH`.

**Current signature** (line 25):
```python
def save(
    conn: sqlite3.Connection,
    slug: str,
    content: str,
    *,
    changed_by: str,
    summary: str,
) -> Path:
```

**New signature** (slug parameter removed):
```python
def save(
    conn: sqlite3.Connection,
    content: str,
    *,
    changed_by: str,
    summary: str,
) -> Path:
```

**Path derivation change** (lines 58, 114):
```python
# Remove:  path = C.md_path(slug)
# Replace: path = C.MD_PATH
```

**Same change for `append_section()`** — remove `slug` param; replace `C.md_path(slug)` with `C.MD_PATH`.

**Same change for `read()`** (line 154):
```python
# Remove:  path = C.md_path(slug)
# Replace: path = C.MD_PATH
```

**Remove from error messages:** References to `slug` in `LookupError` and `FileNotFoundError` messages.

---

### `src/requirements_agent_tools/project_md_cli.py` (CLI/command — surgical)

**Analog:** `src/requirements_agent_tools/refine.py` (same CLI pattern)

**Remove `--project` flag** and replace `ps.resolve()` with `get_project_conn()`:
```python
# Before (pattern from refine.py lines 14-15, 22):
from . import project_session as ps
...
def cmd_save(args):
    _, conn, _ = ps.resolve(args.project)

# After:
from . import project_session as ps  # or import directly
...
def cmd_save(args):
    conn = ps.get_project_conn()
```

**Remove from `build_parser()`:**
```python
# Remove: p.add_argument("--project", default=None)
```

---

### CLI Modules: `refine.py`, `req_ops.py`, `review.py`, `report.py`, `meeting.py`, `db/cli.py` (CLI/command — surgical)

**Analog:** current `refine.py` is the representative example

**The identical change applies to all 6 modules.** Pattern from `refine.py`:

**Remove import** (where present — `req_ops.py` line 11, `refine.py` line 14):
```python
# REMOVE or scope-reduce:
from . import project_session as ps
# ADD (if not already imported elsewhere in the module):
from .project_session import get_project_conn
```

**Replace every `ps.resolve()` call site** — pattern from `refine.py` lines 22, 46, 69, 101:
```python
# Before (4 occurrences in refine.py):
_, conn, _ = ps.resolve(args.project)

# After:
conn = get_project_conn()
```

**Remove `--project` flag from `build_parser()`** — pattern from `refine.py` line 119:
```python
# REMOVE this line:
p.add_argument("--project", default=None)
```

**For `db/cli.py` specifically** — the `--project` option is on the click group (lines 83-99), not argparse:
```python
# REMOVE from cli() group:
@click.option(
    "--project",
    "slug",
    required=True,
    metavar="SLUG",
    help="Project slug (directory name under projects/).",
)
@click.pass_context
def cli(ctx: click.Context, slug: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["slug"] = slug   # slug no longer stored on context

# Replace _open_conn() (lines 61-63):
# Before:
def _open_conn(slug: str) -> sqlite3.Connection:
    return get_db(str(C.db_path(slug)))

# After:
def _open_conn() -> sqlite3.Connection:
    return get_db(str(C.DB_PATH))
```

---

### `config/project.yaml` (config — new file)

**Analog:** `config/default.yaml`

**Format pattern** from `config/default.yaml` (all 2 lines):
```yaml
log_level: info
compliance_mode: false
```

**New file content** (written by `cmd_setup()` via `yaml.safe_dump()`):
```yaml
sqlite_vec: false
otel_enabled: false
```

Notes:
- Written by `cmd_setup()` only — never auto-created by other modules
- Read by `db/connection.py` (or callers) to decide whether to load sqlite-vec
- `yaml.safe_load()` only — never `yaml.load()` without Loader (security constraint from RESEARCH.md)

---

### `tests/test_setup.py` (test — new file)

**Analog:** `tests/test_init.py`

**Module-level setup pattern** (from `test_init.py` lines 1-29):
```python
"""
tests/test_setup.py — Unit tests for init_project.cmd_setup() and get_project_conn().
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from io import StringIO

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
```

**Fixture pattern using `tmp_path`** (from `test_db.py` lines 137-159 — real SQLite, no MagicMock):
```python
@pytest.fixture()
def project_env(tmp_path, monkeypatch):
    """Patch PROJECT_DIR to a tmp location so tests are isolated."""
    import requirements_agent_tools.CONSTANTS as C
    monkeypatch.setattr(C, "PROJECT_DIR", tmp_path / "project")
    monkeypatch.setattr(C, "DB_PATH", tmp_path / "project" / "project.db")
    monkeypatch.setattr(C, "MD_PATH", tmp_path / "project" / "PROJECT.md")
    yield tmp_path
```

**Subprocess test pattern** (from `test_init.py` lines 22-29):
```python
def _run(*args, env=None, **kwargs):
    return subprocess.run(
        [sys.executable, "-m", "requirements_agent_tools.init_project", *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
        **kwargs,
    )
```

**Guard test pattern** (D-07 behavior — test second-run exits non-zero):
```python
def test_setup_guard_on_second_run(project_env):
    # First run succeeds; second run must exit non-zero
    ...
```

**Output contract test pattern** (from `test_init.py` lines 164-183):
```python
def test_ok_writes_json_with_ok_true_to_stdout(init, capsys):
    init._ok({"key": "val"})
    out, _ = capsys.readouterr()
    payload = json.loads(out)
    assert payload["ok"] is True
```

**Key test names to implement** (from RESEARCH.md validation map):
- `test_setup_creates_project_dir`
- `test_setup_creates_subdirs` (logs/, notes/)
- `test_setup_bootstraps_db`
- `test_setup_writes_config_yaml`
- `test_setup_interactive_prompts`
- `test_setup_guard_on_second_run`
- `test_get_project_conn_opens_db`
- `test_get_project_conn_no_db`

---

### `tests/test_db.py` (test — surgical update)

**Analog:** current `tests/test_db.py`

**Change 1 — Remove `slug` from `_TEST_BOOTSTRAP_SQL`** (lines 34-57):
```python
# In _TEST_BOOTSTRAP_SQL, remove this line from projects table:
    slug              TEXT NOT NULL DEFAULT '',
```

**Change 2 — Fix stale `minutes` table in `_TEST_BOOTSTRAP_SQL`** (lines 99-117):
```python
# Current stale DDL (lines 99-117) — has project_id FK and idx_min_project:
CREATE TABLE IF NOT EXISTS minutes (
    id                      TEXT PRIMARY KEY,
    project_id              TEXT NOT NULL REFERENCES projects(project_id),   ← REMOVE
    ...
);
CREATE INDEX IF NOT EXISTS idx_min_project ON minutes(project_id);   ← REMOVE

# Replace with canonical schema (matching schema.py minutes table, lines 97-112):
CREATE TABLE IF NOT EXISTS minutes (
    id                      TEXT PRIMARY KEY,
    title                   TEXT NOT NULL,
    source                  TEXT NOT NULL DEFAULT 'other',
    source_url              TEXT,
    occurred_at             TEXT NOT NULL,
    logged_at               TEXT NOT NULL,
    logged_by               TEXT NOT NULL,
    attendees               TEXT NOT NULL DEFAULT '[]',
    summary                 TEXT NOT NULL DEFAULT '',
    raw_notes               TEXT NOT NULL DEFAULT '',
    decisions               TEXT NOT NULL DEFAULT '[]',
    action_items            TEXT NOT NULL DEFAULT '[]',
    integrated_into_status  INTEGER NOT NULL DEFAULT 0,
    integrated_at           TEXT
);
```

**Change 3 — Remove stale migration in `_test_bootstrap()`** (lines 126-131):
```python
# REMOVE the ALTER TABLE slug migration from _test_bootstrap():
    try:
        conn.execute("ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass
```

**Change 4 — Delete slug-specific test cases** (lines 187-224):
```python
# DELETE these test functions:
# - test_slug_column_exists (line 187)
# - test_upsert_project_auto_derives_slug (line 195)
# - test_upsert_project_preserves_explicit_slug (line 205)
# - test_upsert_project_stores_slug_in_db (line 214)
```

**Add new test:**
```python
def test_projects_table_no_slug_column(conn):
    """Projects table must NOT have a slug column after Phase 1 bootstrap."""
    cols = [
        row["name"] for row in conn.execute("PRAGMA table_info(projects)").fetchall()
    ]
    assert "slug" not in cols, f"'slug' column must not exist in Phase 1: {cols}"
```

**Keep unchanged:** `test_get_db_requires_path_argument`, `test_get_db_raises_type_error_without_args`, `test_db_rejects_second_project`, `test_list_projects_*`, all requirement CRUD tests.

---

### `tests/test_slug_infrastructure.py` (DELETE)

**Action:** Delete file entirely. All tests in this file cover `slug` column, `get_project_by_slug`, `slugify`, and `_row_to_project` slug field — all of which are removed in Phase 1.

No pattern to extract — this file is obsolete.

---

### `tests/test_init.py` (test — rewrite)

**Analog:** current `tests/test_init.py`

**Keep from current file** (lines 1-60):
- `REPO_ROOT`, `MODULE`, `_run()` helper — same pattern
- Import block, `pytest` fixture structure

**Rewrite `TestInitHelp`** to test `setup` subcommand instead of `new`/`list`/`update`:
```python
# Before (lines 33-52):
assert "new" in output.lower() or "list" in output.lower()
assert _run("new", "--help").returncode == 0
assert _run("list", "--help").returncode == 0
assert _run("update", "--help").returncode == 0

# After:
assert "setup" in output.lower()
assert _run("setup", "--help").returncode == 0
```

**Rewrite `TestBuildParser`** — test `setup` subcommand; remove all `TestBuildParser` cases that reference `new`, `list`, `update` with metadata args.

**Keep `TestParseJson` unchanged** (lines 129-161) — `_parse_json` helper is unaffected.

**Keep `TestOutputHelpers` unchanged** (lines 164-183) — `_ok`/`_err` contract is unaffected.

---

### `pyproject.toml` (config — 1-line add)

**Analog:** current `pyproject.toml`

**Add to `dependencies` list** (after line 19 `"sqlite-vec>=0.1.9",`):
```toml
    "pyyaml>=6.0",
```

---

## Shared Patterns

### JSON stdout / stderr contract
**Source:** `src/requirements_agent_tools/_cli_io.py` lines 17-29
**Apply to:** All CLI command functions (`cmd_setup()` and any modified commands)
```python
from ._cli_io import err as _err
from ._cli_io import ok as _ok

# Success:
_ok({"key": "value", ...})

# Failure (exits non-zero):
_err("Human-readable error message")
# Never use sys.exit() directly in module code
```

### Google-style docstrings
**Source:** `src/requirements_agent_tools/db/projects.py` lines 16-31 (canonical example)
**Apply to:** All new and rewritten functions
```python
def func(conn: sqlite3.Connection, param: str) -> ReturnType:
    """One-line summary sentence.

    Optional longer description paragraph.

    Args:
        conn: Open DB connection.
        param: Description of param.

    Returns:
        Description of return value.

    Raises:
        SomeError: When this condition occurs.
    """
```

### Real-SQLite test pattern (no MagicMock)
**Source:** `tests/test_db.py` lines 137-159
**Apply to:** `tests/test_setup.py` and all updated test files
```python
@pytest.fixture()
def conn(tmp_path):
    """Open a real SQLite DB via db.get_db with sqlite_vec disabled."""
    c = db_conn.get_db(str(tmp_path / "test.db"), sqlite_vec_enabled=False)
    yield c
    c.close()
```
Note: After Phase 1, `get_db()` accepts `sqlite_vec_enabled=False` (default), eliminating the need for `sys.modules["sqlite_vec"]` patching in most tests.

### `from __future__ import annotations` header
**Source:** All existing source modules (e.g., `project_session.py` line 1, `db/projects.py` line 1)
**Apply to:** All new and rewritten Python files
```python
from __future__ import annotations
```

### Loguru logging
**Source:** `src/requirements_agent_tools/db/projects.py` lines 9, 96; `db/connection.py` lines 8, 33
**Apply to:** All new modules that perform significant operations
```python
from loguru import logger

logger.debug("Opening DB at {}", path)   # positional {} not %s
logger.info("Upserted project id={}", meta.project_id)
logger.error("Something failed: {}", e)
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `config/project.yaml` | config | — | No existing per-setup config file; `config/default.yaml` is closest but is static runtime config, not setup-generated |

Note: RESEARCH.md Pattern 4 (`load_project_config()`) has no existing codebase analog. The planner should implement it following the RESEARCH.md pattern directly.

---

## Metadata

**Analog search scope:** `src/requirements_agent_tools/`, `tests/`, `config/`
**Files scanned:** 14 source files + 4 test files
**Pattern extraction date:** 2026-04-30
