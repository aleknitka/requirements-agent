"""Behaviour tests for requirement CRUD, search, and reporting.

Covers:
  * find by id / exact title / title LIKE / status / type / updated-window
  * insert and update (with diff logging into ``updates`` table and logger)
  * protected fields (``id``, ``created_at``) cannot be changed
  * combined report = every requirement + its full update history
"""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from requirements_agent_tools.db import connection as db_conn
from requirements_agent_tools.db import requirements as db_req
from requirements_agent_tools.db.updates import get_updates
from requirements_agent_tools.models import (
    RequirementIn,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)


_BOOTSTRAP_SQL = """
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
"""


def _bootstrap(conn: sqlite3.Connection, sqlite_vec_enabled: bool = False) -> None:
    conn.executescript(_BOOTSTRAP_SQL)
    conn.commit()


@pytest.fixture()
def conn(tmp_path):
    """Real SQLite file with plain schema (no sqlite-vec required)."""
    with patch.object(db_conn, "bootstrap", _bootstrap):
        c = db_conn.get_db(str(tmp_path / "test.db"), sqlite_vec_enabled=False)
    yield c
    c.close()


def _add(
    conn,
    *,
    title,
    description="",
    req_type=RequirementType.FUN,
    status=RequirementStatus.OPEN,
    priority=RequirementPriority.MEDIUM,
    owner=None,
    by="tester",
):
    return db_req.insert_requirement(
        conn,
        RequirementIn(
            req_type=req_type,
            title=title,
            description=description,
            status=status,
            priority=priority,
            owner=owner,
        ),
        created_by=by,
    )


# ── Find by id ────────────────────────────────────────────────────────────────


def test_find_by_id_returns_row(conn):
    row = _add(conn, title="Login flow")
    found = db_req.get_requirement(conn, row.id)
    assert found is not None
    assert found.id == row.id
    assert found.title == "Login flow"


def test_find_by_id_returns_none_for_missing(conn):
    assert db_req.get_requirement(conn, "REQ-FUN-DEADBEEF") is None


# ── Find by exact title ───────────────────────────────────────────────────────


def test_find_by_title_exact_match(conn):
    _add(conn, title="Login flow")
    _add(conn, title="Login flow extended")
    row = db_req.get_requirement_by_title(conn, "Login flow")
    assert row is not None
    assert row.title == "Login flow"


def test_find_by_title_returns_none_for_missing(conn):
    _add(conn, title="Other")
    assert db_req.get_requirement_by_title(conn, "Login flow") is None


# ── Find by title LIKE% ───────────────────────────────────────────────────────


def test_find_by_title_substring(conn):
    _add(conn, title="Login flow")
    _add(conn, title="Login flow extended")
    _add(conn, title="Logout button")
    rows = db_req.search_requirements(conn, keyword="Login")
    titles = sorted(r.title for r in rows)
    assert titles == ["Login flow", "Login flow extended"]


# ── Find by status ────────────────────────────────────────────────────────────


def test_find_by_status(conn):
    open_row = _add(conn, title="Open one", status=RequirementStatus.OPEN)
    _add(conn, title="Done one", status=RequirementStatus.DONE)

    rows = db_req.search_requirements(conn, status=RequirementStatus.OPEN.value)
    ids = [r.id for r in rows]
    assert ids == [open_row.id]


# ── Find by type ──────────────────────────────────────────────────────────────


def test_find_by_type(conn):
    fun_row = _add(conn, title="Fun req", req_type=RequirementType.FUN)
    _add(conn, title="Non-fun req", req_type=RequirementType.NFR)

    rows = db_req.search_requirements(conn, req_type=RequirementType.FUN.value)
    ids = [r.id for r in rows]
    assert ids == [fun_row.id]


# ── Find updated within a time window ─────────────────────────────────────────


def test_find_updated_in_period(conn):
    a = _add(conn, title="Early")
    time.sleep(0.01)
    cutoff = datetime.now(timezone.utc)
    time.sleep(0.01)
    b = _add(conn, title="Late")

    far_future = cutoff + timedelta(days=1)
    early_window = db_req.find_requirements_updated_between(
        conn, cutoff - timedelta(days=1), cutoff
    )
    late_window = db_req.find_requirements_updated_between(conn, cutoff, far_future)

    assert [r.id for r in early_window] == [a.id]
    assert [r.id for r in late_window] == [b.id]


# ── Insert ────────────────────────────────────────────────────────────────────


def test_insert_persists_row_and_logs_creation(conn):
    row = _add(conn, title="Audit trail", by="alice")

    persisted = db_req.get_requirement(conn, row.id)
    assert persisted is not None
    assert persisted.title == "Audit trail"

    history = get_updates(conn, row.id)
    assert len(history) == 1
    assert history[0].changed_by == "alice"
    assert history[0].summary == "Requirement created."
    assert history[0].diffs == []


# ── Update logs into table and via loguru ─────────────────────────────────────


def test_update_writes_diff_to_updates_table(conn):
    row = _add(conn, title="Old title")
    db_req.update_requirement(conn, row.id, {"title": "New title"}, "bob", "rename")

    history = get_updates(conn, row.id)
    assert len(history) == 2  # creation + this update
    last = history[-1]
    assert last.changed_by == "bob"
    assert last.summary == "rename"
    assert len(last.diffs) == 1
    diff = last.diffs[0]
    assert diff.field == "title"
    assert diff.old_value == "Old title"
    assert diff.new_value == "New title"


def test_update_emits_loguru_record_per_diff(conn):
    from loguru import logger

    row = _add(conn, title="Old", description="d1")
    captured: list[str] = []
    sink_id = logger.add(lambda m: captured.append(str(m)), level="DEBUG")
    try:
        db_req.update_requirement(
            conn,
            row.id,
            {"title": "New", "description": "d2"},
            "carol",
            "edit",
        )
    finally:
        logger.remove(sink_id)

    joined = "\n".join(captured)
    assert "Updated" in joined and row.id in joined
    assert "title" in joined and "'Old'" in joined and "'New'" in joined
    assert "description" in joined and "'d1'" in joined and "'d2'" in joined


# ── Protected (non-updatable) fields ──────────────────────────────────────────


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "REQ-FUN-HACKED"),
        ("created_at", "1999-01-01T00:00:00+00:00"),
        ("updated_at", "1999-01-01T00:00:00+00:00"),
        ("has_embedding", True),
    ],
)
def test_update_rejects_protected_field(conn, field, value):
    row = _add(conn, title="Stable")
    original = db_req.get_requirement(conn, row.id)

    with pytest.raises(ValueError, match="not updatable"):
        db_req.update_requirement(conn, row.id, {field: value}, "mallory", "tampering")

    after = db_req.get_requirement(conn, row.id)
    assert after.id == original.id
    assert after.created_at == original.created_at
    # Only one entry (the creation) — no update was logged.
    assert len(get_updates(conn, row.id)) == 1


# ── Combined report: requirements + per-requirement update history ────────────


def test_build_requirements_report_includes_each_requirement_and_history(conn):
    a = _add(conn, title="Alpha")
    b = _add(conn, title="Beta")
    db_req.update_requirement(conn, a.id, {"title": "Alpha v2"}, "u", "rename")

    report = db_req.build_requirements_report(conn)
    by_id = {entry["requirement"].id: entry for entry in report}

    assert set(by_id) == {a.id, b.id}
    # Alpha had a creation + a rename
    assert len(by_id[a.id]["updates"]) == 2
    rename = by_id[a.id]["updates"][-1]
    assert rename.summary == "rename"
    assert rename.diffs[0].field == "title"
    # Beta only has its creation entry
    assert len(by_id[b.id]["updates"]) == 1
    assert by_id[b.id]["updates"][0].summary == "Requirement created."
