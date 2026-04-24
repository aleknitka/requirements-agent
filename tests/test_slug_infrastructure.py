"""
test_slug_infrastructure.py — TDD tests for BUG-08 slug column fix (plan 00-05).

Tests:
  1. After bootstrap(conn), projects table has a 'slug' column.
  2. upsert_project auto-derives slug from name when meta.slug is empty.
  3. get_project_by_slug returns the correct ProjectMeta.
  4. get_project_by_slug returns None for non-existent slug.
  5. _row_to_project populates slug from the DB row.
"""

from __future__ import annotations

import sqlite3
import sys

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "shared"))

import db
from models import ProjectMeta


def _make_conn() -> sqlite3.Connection:
    """
    Create a fresh in-memory SQLite connection and run only the non-vec DDL.

    sqlite-vec (vec0 virtual table) cannot be loaded in this WSL environment.
    We create the connection directly and call bootstrap() with the vec0 DDL
    replaced by a no-op so that all Projects/Requirements/Minutes tables are
    created normally.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Run bootstrap manually, replacing the vec virtual-table creation with a
    # plain dummy table so the rest of bootstrap's DDL runs unchanged.
    import CONSTANTS as C
    conn.executescript(f"""
    CREATE TABLE IF NOT EXISTS projects (
        project_id        TEXT PRIMARY KEY,
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
    """)
    conn.commit()
    return conn


@pytest.fixture()
def conn():
    """Provide a fresh in-memory DB for each test (no sqlite-vec dependency)."""
    c = _make_conn()
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Test 1: bootstrap creates a slug column
# ---------------------------------------------------------------------------

def test_bootstrap_creates_slug_column():
    """
    projects table must have a 'slug' column after bootstrap().
    This test calls bootstrap() directly (bypassing get_db/sqlite-vec).
    """
    import types
    import sys as _sys

    # Monkeypatch sqlite_vec so bootstrap() doesn't crash on vec0
    fake_vec = types.ModuleType("sqlite_vec")
    fake_vec.load = lambda _c: None
    _sys.modules["sqlite_vec"] = fake_vec

    try:
        import CONSTANTS as C
        # Patch bootstrap's executescript so vec0 DDL is replaced with a dummy
        real_executescript = sqlite3.Connection.executescript

        def patched_executescript(self, sql):
            # Replace vec0 CREATE VIRTUAL TABLE with a plain table stub
            import re
            sql = re.sub(
                r"CREATE VIRTUAL TABLE IF NOT EXISTS req_embeddings[^;]+;",
                "CREATE TABLE IF NOT EXISTS req_embeddings (requirement_id TEXT PRIMARY KEY, embedding BLOB);",
                sql,
                flags=re.DOTALL,
            )
            return real_executescript(self, sql)

        sqlite3.Connection.executescript = patched_executescript

        c = sqlite3.connect(":memory:")
        c.row_factory = sqlite3.Row
        db.bootstrap(c)

        cols = [row[1] for row in c.execute("PRAGMA table_info(projects)").fetchall()]
        assert "slug" in cols, f"'slug' column not found. columns: {cols}"
        c.close()
    finally:
        sqlite3.Connection.executescript = real_executescript
        _sys.modules.pop("sqlite_vec", None)


# ---------------------------------------------------------------------------
# Test 2: upsert_project auto-derives slug from name
# ---------------------------------------------------------------------------

def test_upsert_project_auto_derives_slug(conn):
    """When meta.slug is empty, upsert_project should set slug to slugified name."""
    meta = ProjectMeta(name="My Project")
    assert meta.slug == "", "Precondition: meta.slug should start empty"
    returned = db.upsert_project(conn, meta)
    assert returned.slug == "my-project", f"Expected 'my-project', got '{returned.slug}'"
    # Also verify the in-memory meta was mutated
    assert meta.slug == "my-project"


# ---------------------------------------------------------------------------
# Test 3: get_project_by_slug returns correct ProjectMeta
# ---------------------------------------------------------------------------

def test_get_project_by_slug_returns_correct_row(conn):
    """get_project_by_slug should return a ProjectMeta matching the inserted row."""
    meta = ProjectMeta(name="Test Project")
    db.upsert_project(conn, meta)

    fetched = db.get_project_by_slug(conn, "test-project")
    assert fetched is not None, "Expected a ProjectMeta, got None"
    assert fetched.name == "Test Project"
    assert fetched.slug == "test-project"


# ---------------------------------------------------------------------------
# Test 4: get_project_by_slug returns None for unknown slug
# ---------------------------------------------------------------------------

def test_get_project_by_slug_returns_none_for_missing(conn):
    """get_project_by_slug should return None when slug does not exist."""
    result = db.get_project_by_slug(conn, "nonexistent-slug")
    assert result is None, f"Expected None, got {result}"


# ---------------------------------------------------------------------------
# Test 5: _row_to_project populates slug from DB row
# ---------------------------------------------------------------------------

def test_row_to_project_populates_slug(conn):
    """_row_to_project must read slug from the DB row."""
    meta = ProjectMeta(name="Row Slug Test")
    db.upsert_project(conn, meta)

    row = conn.execute(
        "SELECT * FROM projects WHERE project_id = ?", (meta.project_id,)
    ).fetchone()
    assert row is not None
    project = db._row_to_project(row)
    assert project.slug == "row-slug-test", f"Expected 'row-slug-test', got '{project.slug}'"
