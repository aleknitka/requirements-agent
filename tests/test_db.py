"""
tests/test_db.py — Real-SQLite CRUD tests for shared/db.py after Phase 0 bug fixes.

Bugs covered:
  BUG-01 — get_db() must require an explicit path argument (no default).
  BUG-03 — list_projects() must exist and return ProjectMeta objects, not dicts.
  BUG-04 — get_project_by_slug() must exist and perform a correct slug lookup.
  BUG-08 — projects table must have a slug column; upsert_project auto-derives slug.

Strategy:
  - Patch sys.modules["sqlite_vec"] so sqlite_vec.load() becomes a no-op.
  - Patch db.bootstrap with a test-safe version that replaces the vec0 virtual table
    with a plain table (vec0 requires the native extension to be loaded into SQLite).
  - All other operations use a real SQLite file via pytest's tmp_path fixture.
"""

from __future__ import annotations

import inspect
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "shared"))

import db  # noqa: E402 — must come after sys.path mutation
import CONSTANTS as C  # noqa: E402


# ── Test-safe bootstrap (replaces vec0 virtual table with plain table) ────────

_TEST_BOOTSTRAP_SQL = f"""
CREATE TABLE IF NOT EXISTS projects (
    project_id        TEXT PRIMARY KEY,
    slug              TEXT NOT NULL DEFAULT '',
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

CREATE TABLE IF NOT EXISTS requirements (
    id             TEXT PRIMARY KEY,
    project_id     TEXT NOT NULL REFERENCES projects(project_id),
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

CREATE INDEX IF NOT EXISTS idx_req_project  ON requirements(project_id);
CREATE INDEX IF NOT EXISTS idx_req_status   ON requirements(status);
CREATE INDEX IF NOT EXISTS idx_req_type     ON requirements(req_type);
CREATE INDEX IF NOT EXISTS idx_req_priority ON requirements(priority);

CREATE TABLE IF NOT EXISTS req_embeddings (
    requirement_id TEXT PRIMARY KEY,
    embedding      BLOB
);

CREATE TABLE IF NOT EXISTS updates (
    id             TEXT PRIMARY KEY,
    requirement_id TEXT NOT NULL REFERENCES requirements(id),
    changed_at     TEXT NOT NULL,
    changed_by     TEXT NOT NULL,
    summary        TEXT NOT NULL DEFAULT '',
    diffs          TEXT NOT NULL DEFAULT '[]',
    full_snapshot  TEXT
);

CREATE INDEX IF NOT EXISTS idx_upd_req ON updates(requirement_id);

CREATE TABLE IF NOT EXISTS minutes (
    id                      TEXT PRIMARY KEY,
    project_id              TEXT NOT NULL REFERENCES projects(project_id),
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

CREATE INDEX IF NOT EXISTS idx_min_project ON minutes(project_id);
"""


def _test_bootstrap(conn: sqlite3.Connection) -> None:
    """Test-safe bootstrap: identical to db.bootstrap() but uses a plain table
    instead of the vec0 virtual table so tests run without the native extension."""
    conn.executescript(_TEST_BOOTSTRAP_SQL)
    conn.commit()
    # Idempotent slug migration (mirrors db.bootstrap)
    try:
        conn.execute("ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass


# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture()
def conn(tmp_path):
    """
    Open a real SQLite DB (via db.get_db) with:
      - sqlite_vec patched to a no-op (sys.modules injection)
      - db.bootstrap patched to _test_bootstrap (avoids vec0 module requirement)

    All project/requirement CRUD runs against a real SQLite file on disk.
    """
    mock_vec = MagicMock()
    mock_vec.load = MagicMock()
    original_vec = sys.modules.get("sqlite_vec", None)
    sys.modules["sqlite_vec"] = mock_vec
    try:
        with patch.object(db, "bootstrap", _test_bootstrap):
            c = db.get_db(str(tmp_path / "test.db"))
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
    sig = inspect.signature(db.get_db)
    param = sig.parameters["path"]
    assert param.default is inspect.Parameter.empty, (
        "get_db must not have a default for `path`"
    )


def test_get_db_raises_type_error_without_args():
    """Calling get_db() without arguments raises TypeError."""
    with pytest.raises(TypeError):
        db.get_db()  # type: ignore[call-arg]


# ═══════════════════════════════════════════════════════════════════════════════
# Test group 2: BUG-08 — slug column exists after bootstrap
# ═══════════════════════════════════════════════════════════════════════════════


def test_slug_column_exists(conn):
    """Projects table has a slug column after bootstrap."""
    cols = [row["name"] for row in conn.execute("PRAGMA table_info(projects)").fetchall()]
    assert "slug" in cols, f"'slug' not found in columns: {cols}"


def test_upsert_project_auto_derives_slug(conn):
    """When meta.slug is empty, upsert_project derives it from name via C.slugify."""
    from models import ProjectMeta

    meta = ProjectMeta(name="My ML Project")
    assert meta.slug == "", "Precondition: slug starts empty"
    db.upsert_project(conn, meta)
    assert meta.slug == "my-ml-project", f"Expected 'my-ml-project', got '{meta.slug}'"


def test_upsert_project_preserves_explicit_slug(conn):
    """When meta.slug is already set, upsert_project does not overwrite it."""
    from models import ProjectMeta

    meta = ProjectMeta(name="My Project", slug="custom-slug")
    db.upsert_project(conn, meta)
    assert meta.slug == "custom-slug", f"Expected 'custom-slug', got '{meta.slug}'"


def test_upsert_project_stores_slug_in_db(conn):
    """Slug written by upsert_project is actually persisted in the DB."""
    from models import ProjectMeta

    meta = ProjectMeta(name="Stored Slug Test")
    db.upsert_project(conn, meta)
    row = conn.execute(
        "SELECT slug FROM projects WHERE project_id = ?", (meta.project_id,)
    ).fetchone()
    assert row is not None
    assert row["slug"] == "stored-slug-test"


# ═══════════════════════════════════════════════════════════════════════════════
# Test group 3: BUG-03 — list_projects returns ProjectMeta objects
# ═══════════════════════════════════════════════════════════════════════════════


def test_list_projects_empty(conn):
    """list_projects returns an empty list when no projects have been inserted."""
    projects = db.list_projects(conn)
    assert projects == []


def test_list_projects_returns_project_meta(conn):
    """list_projects returns a list of ProjectMeta, not raw dicts."""
    from models import ProjectMeta

    meta = ProjectMeta(name="Alpha")
    db.upsert_project(conn, meta)
    results = db.list_projects(conn)
    assert len(results) == 1
    # Must be attribute access, not dict["slug"]
    assert hasattr(results[0], "slug"), "list_projects result must be ProjectMeta (has .slug)"
    assert results[0].name == "Alpha"
    assert results[0].slug == "alpha"


def test_list_projects_returns_multiple_rows(conn):
    """list_projects returns all inserted projects in created_at order."""
    from models import ProjectMeta

    for name in ("Proj A", "Proj B", "Proj C"):
        db.upsert_project(conn, ProjectMeta(name=name))
    results = db.list_projects(conn)
    assert len(results) == 3
    assert [r.slug for r in results] == ["proj-a", "proj-b", "proj-c"]


def test_list_projects_items_are_project_meta_instances(conn):
    """Each item returned by list_projects must be a ProjectMeta instance."""
    from models import ProjectMeta

    db.upsert_project(conn, ProjectMeta(name="Type Check"))
    results = db.list_projects(conn)
    assert all(isinstance(r, ProjectMeta) for r in results)


# ═══════════════════════════════════════════════════════════════════════════════
# Test group 4: BUG-04 — get_project_by_slug lookup
# ═══════════════════════════════════════════════════════════════════════════════


def test_get_project_by_slug_returns_correct_meta(conn):
    """get_project_by_slug returns the matching ProjectMeta for a known slug."""
    from models import ProjectMeta

    meta = ProjectMeta(name="Test Project")
    db.upsert_project(conn, meta)
    fetched = db.get_project_by_slug(conn, "test-project")
    assert fetched is not None
    assert fetched.name == "Test Project"
    assert fetched.slug == "test-project"


def test_get_project_by_slug_returns_none_for_missing(conn):
    """get_project_by_slug returns None when no project has the given slug."""
    fetched = db.get_project_by_slug(conn, "no-such-slug")
    assert fetched is None


def test_get_project_by_slug_returns_project_meta_instance(conn):
    """get_project_by_slug result is a ProjectMeta instance, not a dict."""
    from models import ProjectMeta

    db.upsert_project(conn, ProjectMeta(name="Slug Meta"))
    result = db.get_project_by_slug(conn, "slug-meta")
    assert isinstance(result, ProjectMeta)


def test_get_project_by_slug_correct_project_id(conn):
    """get_project_by_slug returns the project with the matching project_id."""
    from models import ProjectMeta

    m1 = ProjectMeta(name="Project One")
    m2 = ProjectMeta(name="Project Two")
    db.upsert_project(conn, m1)
    db.upsert_project(conn, m2)
    fetched = db.get_project_by_slug(conn, "project-two")
    assert fetched is not None
    assert fetched.project_id == m2.project_id
