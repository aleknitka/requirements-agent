"""Behaviour tests for project_md (PROJECT.md create / update / append)."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from requirements_agent_tools import CONSTANTS as C
from requirements_agent_tools import project_md, project_md_cli
from requirements_agent_tools.db import connection as db_conn
from requirements_agent_tools.db import projects as db_projects
from requirements_agent_tools.db import requirements as db_req
from requirements_agent_tools.db.updates import (
    get_project_md_history,
    get_updates,
)
from requirements_agent_tools.models import (
    ProjectMeta,
    RequirementIn,
    RequirementType,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_MODULE = "requirements_agent_tools.project_md_cli"


def _cli_run(*args):
    return subprocess.run(
        [sys.executable, "-m", CLI_MODULE, *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


_BOOTSTRAP_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    project_id        TEXT PRIMARY KEY,
    singleton         INTEGER NOT NULL DEFAULT 1 CHECK (singleton = 1),
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

CREATE INDEX IF NOT EXISTS idx_upd_entity ON updates(entity_type, entity_id);
"""


def _bootstrap(conn: sqlite3.Connection) -> None:
    conn.executescript(_BOOTSTRAP_SQL)
    conn.commit()


@pytest.fixture()
def project_env(tmp_path, monkeypatch):
    """Real DB at PROJECTS_DIR/<slug>/<slug>.db with a project row inserted."""
    monkeypatch.setattr(C, "PROJECTS_DIR", tmp_path)
    slug = "demo"

    mock_vec = MagicMock()
    mock_vec.load = MagicMock()
    saved = sys.modules.get("sqlite_vec")
    sys.modules["sqlite_vec"] = mock_vec
    try:
        with patch.object(db_conn, "bootstrap", _bootstrap):
            conn = db_conn.get_db(str(C.db_path(slug)))
    finally:
        if saved is None:
            sys.modules.pop("sqlite_vec", None)
        else:
            sys.modules["sqlite_vec"] = saved

    meta = ProjectMeta(name="Demo")
    db_projects.upsert_project(conn, meta)
    yield slug, conn, meta
    conn.close()


# ── save: create path ─────────────────────────────────────────────────────────


def test_save_creates_file_when_missing(project_env):
    slug, conn, meta = project_env
    path = project_md.save(
        conn, slug, "# Demo\n\nbody\n", changed_by="alice", summary="initial"
    )
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "# Demo\n\nbody\n"

    history = get_project_md_history(conn, meta.project_id)
    assert len(history) == 1
    rec = history[0]
    assert rec.entity_type == "project_md"
    assert rec.entity_id == meta.project_id
    assert rec.changed_by == "alice"
    assert rec.summary == "initial"
    assert rec.diffs == []  # creation has no diff
    assert rec.full_snapshot == {"content": "# Demo\n\nbody\n"}


# ── save: replace path ───────────────────────────────────────────────────────


def test_save_overwrites_and_records_diff(project_env):
    slug, conn, meta = project_env
    project_md.save(conn, slug, "v1\n", changed_by="alice", summary="initial")
    project_md.save(conn, slug, "v2\n", changed_by="bob", summary="rewrite")

    assert C.md_path(slug).read_text(encoding="utf-8") == "v2\n"
    history = get_project_md_history(conn, meta.project_id)
    assert len(history) == 2
    update = history[-1]
    assert update.changed_by == "bob"
    assert update.summary == "rewrite"
    assert len(update.diffs) == 1
    diff = update.diffs[0]
    assert diff.field == "content"
    assert diff.old_value == "v1\n"
    assert diff.new_value == "v2\n"
    assert update.full_snapshot == {"content": "v2\n"}


# ── save: loguru log ─────────────────────────────────────────────────────────


def test_save_emits_loguru_record(project_env):
    from loguru import logger

    slug, conn, _ = project_env
    captured: list[str] = []
    sink_id = logger.add(lambda m: captured.append(str(m)), level="INFO")
    try:
        project_md.save(conn, slug, "hi", changed_by="carol", summary="hello")
    finally:
        logger.remove(sink_id)

    joined = "\n".join(captured)
    assert "Created PROJECT.md" in joined
    assert slug in joined
    assert "carol" in joined


# ── append_section ───────────────────────────────────────────────────────────


def test_append_section_extends_file(project_env):
    slug, conn, meta = project_env
    project_md.save(conn, slug, "# Demo\n", changed_by="a", summary="init")
    project_md.append_section(
        conn, slug, "## Update\nProgress note", changed_by="a", summary="weekly"
    )

    body = C.md_path(slug).read_text(encoding="utf-8")
    assert body.startswith("# Demo\n")
    assert body.endswith("## Update\nProgress note\n")

    history = get_project_md_history(conn, meta.project_id)
    assert len(history) == 2
    appended = history[-1]
    assert appended.summary == "weekly"
    assert len(appended.diffs) == 1
    assert appended.diffs[0].field == "content_appended"
    assert "Progress note" in appended.diffs[0].new_value


def test_append_requires_existing_file(project_env):
    slug, conn, _ = project_env
    with pytest.raises(FileNotFoundError):
        project_md.append_section(
            conn, slug, "anything", changed_by="a", summary="oops"
        )


# ── isolation: requirement updates and project_md updates do not bleed ───────


def test_audit_isolated_from_requirement_updates(project_env):
    slug, conn, meta = project_env
    project_md.save(conn, slug, "body", changed_by="a", summary="md")
    req = db_req.insert_requirement(
        conn,
        RequirementIn(req_type=RequirementType.FUN, title="login"),
        created_by="a",
    )

    md_history = get_project_md_history(conn, meta.project_id)
    req_history = get_updates(conn, req.id)

    assert len(md_history) == 1 and md_history[0].entity_type == "project_md"
    assert len(req_history) == 1 and req_history[0].entity_type == "requirement"
    # And no cross-contamination on the other lookup direction:
    assert get_updates(conn, meta.project_id) == []
    assert get_project_md_history(conn, req.id) == []


# ── CLI: parser + subcommand wiring ──────────────────────────────────────────


class TestCLIHelp:
    def test_help_exits_0(self):
        assert _cli_run("--help").returncode == 0

    def test_save_help_exits_0(self):
        assert _cli_run("save", "--help").returncode == 0

    def test_append_help_exits_0(self):
        assert _cli_run("append", "--help").returncode == 0

    def test_read_help_exits_0(self):
        assert _cli_run("read", "--help").returncode == 0


class TestCLIParser:
    def test_save_requires_by_and_summary(self):
        with pytest.raises(SystemExit):
            project_md_cli.build_parser().parse_args(["save"])

    def test_save_parses_inline_content(self):
        args = project_md_cli.build_parser().parse_args(
            [
                "--project",
                "demo",
                "save",
                "--by",
                "alice",
                "--summary",
                "initial",
                "--content",
                "# Demo",
            ]
        )
        assert args.command == "save"
        assert args.by == "alice"
        assert args.summary == "initial"
        assert args.content == "# Demo"
        assert args.content_file is None

    def test_save_parses_content_file(self):
        args = project_md_cli.build_parser().parse_args(
            [
                "--project",
                "demo",
                "save",
                "--by",
                "alice",
                "--summary",
                "initial",
                "--content-file",
                "/tmp/x.md",
            ]
        )
        assert args.content_file == "/tmp/x.md"

    def test_append_parses(self):
        args = project_md_cli.build_parser().parse_args(
            [
                "--project",
                "demo",
                "append",
                "--by",
                "alice",
                "--summary",
                "weekly",
                "--section",
                "## hi",
            ]
        )
        assert args.command == "append"
        assert args.section == "## hi"
