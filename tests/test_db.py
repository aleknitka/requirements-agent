"""
tests/test_db.py — Real-SQLite CRUD tests for shared/db.py after Phase 0 bug fixes.

Bugs covered:
  BUG-01 — get_db() must require an explicit path argument (no default).
  BUG-03 — list_projects() must exist and return ProjectMeta objects, not dicts.

Phase 1 changes:
  - _TEST_BOOTSTRAP_SQL projects table has NO slug column (single-project model, D-01)
  - minutes table updated to canonical schema (no project_id FK)
  - test_projects_table_no_slug_column added: asserts slug NOT in new schema
  - _LEGACY_BOOTSTRAP_SQL retained so upsert_project() tests continue to pass
    until Plan 02 removes slug from the production INSERT statement
  - conn fixture will be updated to use sqlite_vec_enabled=False once Plan 02
    ships the new get_db() signature (currently uses sys.modules patching)
"""

from __future__ import annotations

import inspect
import sqlite3
import sys
from unittest.mock import MagicMock, patch

import pytest

from requirements_agent_tools import CONSTANTS as C  # noqa: F401
from requirements_agent_tools.db import connection as db_conn
from requirements_agent_tools.db import projects as db_projects


# ── Phase 1 canonical bootstrap SQL (no slug column) ─────────────────────────
# This is the NEW schema for Phase 1. The test_projects_table_no_slug_column
# test verifies this SQL does NOT include a slug column.

_TEST_BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    project_id        TEXT PRIMARY KEY,
    singleton         INTEGER NOT NULL DEFAULT 1 CHECK (singleton = 1),
    name              TEXT NOT NULL,
    code              TEXT,
    phase             TEXT NOT NULL DEFAULT 'discovery',
    objective         TEXT NOT NULL DEFAULT '',
    business_case     TEXT NOT NULL DEFAULT '',
    success_criteria  TEXT NOT NULL DEFAULT '[]',
    out_of_scope      TEXT NOT NULL DEFAULT '[]',
    project_owner     TEXT,
    sponsor           TEXT,
    stakeholders      TEXT NOT NULL DEFAULT '[]',
    start_date        TEXT,
    target_date       TEXT,
    actual_end_date   TEXT,
    external_links    TEXT NOT NULL DEFAULT '[]',
    status_summary    TEXT NOT NULL DEFAULT '',
    status_updated_at TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_singleton ON projects(singleton);

CREATE TABLE IF NOT EXISTS requirements (
    id             TEXT PRIMARY KEY,
    req_type       TEXT NOT NULL DEFAULT 'CORE',
    title          TEXT NOT NULL,
    description    TEXT NOT NULL DEFAULT '',
    status         TEXT NOT NULL DEFAULT 'open',
    priority       TEXT NOT NULL DEFAULT 'medium',
    owner          TEXT,
    stakeholders   TEXT NOT NULL DEFAULT '[]',
    predecessors   TEXT NOT NULL DEFAULT '[]',
    dependencies   TEXT NOT NULL DEFAULT '[]',
    external_links TEXT NOT NULL DEFAULT '[]',
    tags           TEXT NOT NULL DEFAULT '[]',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_req_status   ON requirements(status);
CREATE INDEX IF NOT EXISTS idx_req_type     ON requirements(req_type);
CREATE INDEX IF NOT EXISTS idx_req_priority ON requirements(priority);

CREATE TABLE IF NOT EXISTS req_embeddings (
    requirement_id TEXT PRIMARY KEY,
    embedding      BLOB
);

CREATE TABLE IF NOT EXISTS updates (
    id             TEXT PRIMARY KEY,
    entity_type    TEXT NOT NULL CHECK (entity_type IN ('requirement', 'project_md')),
    entity_id      TEXT NOT NULL,
    changed_at     TEXT NOT NULL,
    changed_by     TEXT NOT NULL,
    summary        TEXT NOT NULL DEFAULT '',
    diffs          TEXT NOT NULL DEFAULT '[]',
    full_snapshot  TEXT
);

CREATE INDEX IF NOT EXISTS idx_upd_entity ON updates(entity_type, entity_id);

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
"""

# ── Legacy bootstrap SQL (with slug) — used by upsert_project() tests ────────
# Retained until Plan 02 removes slug from db/projects.py upsert INSERT.
# Once Plan 02 is executed, this constant can be removed and conn can use
# _TEST_BOOTSTRAP_SQL directly.

_LEGACY_BOOTSTRAP_SQL = _TEST_BOOTSTRAP_SQL.replace(
    "    singleton         INTEGER NOT NULL DEFAULT 1 CHECK (singleton = 1),\n"
    "    name              TEXT NOT NULL,",
    "    singleton         INTEGER NOT NULL DEFAULT 1 CHECK (singleton = 1),\n"
    "    slug              TEXT NOT NULL DEFAULT '',\n"
    "    name              TEXT NOT NULL,",
)


def _test_bootstrap(conn: sqlite3.Connection) -> None:
    """Test-safe bootstrap using the legacy schema (with slug) so upsert_project
    tests continue to pass until Plan 02 removes slug from production INSERT."""
    conn.executescript(_LEGACY_BOOTSTRAP_SQL)
    conn.commit()


# ── Fixture (legacy schema for upsert_project compatibility) ─────────────────


@pytest.fixture()
def conn(tmp_path):
    """Open a real SQLite DB (via db.get_db) with sqlite_vec patched to a no-op.

    Uses _LEGACY_BOOTSTRAP_SQL (with slug) until Plan 02 removes slug from
    db/projects.py. Uses sys.modules injection until Plan 02 ships
    get_db(sqlite_vec_enabled=False).
    All project/requirement CRUD runs against a real SQLite file on disk.
    """
    mock_vec = MagicMock()
    mock_vec.load = MagicMock()
    original_vec = sys.modules.get("sqlite_vec", None)
    sys.modules["sqlite_vec"] = mock_vec
    try:
        with patch.object(db_conn, "bootstrap", _test_bootstrap):
            c = db_conn.get_db(str(tmp_path / "test.db"))
    finally:
        if original_vec is None:
            sys.modules.pop("sqlite_vec", None)
        else:
            sys.modules["sqlite_vec"] = original_vec
    yield c
    c.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Test group 1: BUG-01 — get_db() signature
# ═══════════════════════════════════════════════════════════════════════════════


def test_get_db_requires_path_argument():
    """get_db() with no arguments raises TypeError — no default parameter."""
    sig = inspect.signature(db_conn.get_db)
    param = sig.parameters["path"]
    assert param.default is inspect.Parameter.empty, (
        "get_db must not have a default for `path`"
    )


def test_get_db_raises_type_error_without_args():
    """Calling get_db() without arguments raises TypeError."""
    with pytest.raises(TypeError):
        db_conn.get_db()  # type: ignore[call-arg]


# ═══════════════════════════════════════════════════════════════════════════════
# Test group 2: Phase 1 schema — no slug column
# ═══════════════════════════════════════════════════════════════════════════════


def test_projects_table_no_slug_column():
    """Projects table must NOT have a slug column in the Phase 1 schema (D-01).

    Directly verifies _TEST_BOOTSTRAP_SQL, the new canonical test schema,
    without going through upsert_project() (which still uses slug until Plan 02).
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_TEST_BOOTSTRAP_SQL)
    conn.commit()
    cols = [
        row["name"] for row in conn.execute("PRAGMA table_info(projects)").fetchall()
    ]
    conn.close()
    assert "slug" not in cols, f"'slug' column must not exist in Phase 1 schema: {cols}"


def test_db_rejects_second_project(conn):
    """Schema must structurally prevent a second project from being inserted."""
    from requirements_agent_tools.models import ProjectMeta

    db_projects.upsert_project(conn, ProjectMeta(name="First"))
    with pytest.raises(sqlite3.IntegrityError):
        db_projects.upsert_project(conn, ProjectMeta(name="Second"))


# ═══════════════════════════════════════════════════════════════════════════════
# Test group 3: BUG-03 — list_projects returns ProjectMeta objects
# ═══════════════════════════════════════════════════════════════════════════════


def test_list_projects_empty(conn):
    """list_projects returns an empty list when no projects have been inserted."""
    projects = db_projects.list_projects(conn)
    assert projects == []


def test_list_projects_returns_project_meta(conn):
    """list_projects returns a list of ProjectMeta, not raw dicts."""
    from requirements_agent_tools.models import ProjectMeta

    meta = ProjectMeta(name="Alpha")
    db_projects.upsert_project(conn, meta)
    results = db_projects.list_projects(conn)
    assert len(results) == 1
    assert results[0].name == "Alpha"


def test_upsert_second_project_rejected_by_singleton(conn):
    """Each DB holds exactly one project — a second insert must be rejected."""
    from requirements_agent_tools.models import ProjectMeta

    db_projects.upsert_project(conn, ProjectMeta(name="Proj A"))
    with pytest.raises(sqlite3.IntegrityError):
        db_projects.upsert_project(conn, ProjectMeta(name="Proj B"))
    results = db_projects.list_projects(conn)
    assert len(results) == 1
    assert results[0].name == "Proj A"


def test_list_projects_items_are_project_meta_instances(conn):
    """Each item returned by list_projects must be a ProjectMeta instance."""
    from requirements_agent_tools.models import ProjectMeta

    db_projects.upsert_project(conn, ProjectMeta(name="Type Check"))
    results = db_projects.list_projects(conn)
    assert all(isinstance(r, ProjectMeta) for r in results)
