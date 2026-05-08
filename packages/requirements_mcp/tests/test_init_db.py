"""Tests for ``requirements_mcp.db.init.init_db``."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect

from requirements_mcp.db.engine import make_engine
from requirements_mcp.db.init import init_db

EXPECTED_TABLES = {
    "requirements",
    "requirements_changes",
    "requirement_statuses",
    "requirement_types",
    "issues",
    "issue_updates",
    "issue_priorities",
    "issue_statuses",
    "issue_types",
    "requirement_issues",
}


def test_init_db_creates_file_and_all_tables(temp_db_path: Path) -> None:
    resolved, report = init_db(temp_db_path)

    assert resolved.exists()
    assert resolved == temp_db_path.resolve()

    engine = make_engine(resolved)
    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES.issubset(tables)

    assert sum(report.inserted.values()) > 0


def test_init_db_is_idempotent(temp_db_path: Path) -> None:
    init_db(temp_db_path)
    _, second = init_db(temp_db_path)

    assert sum(second.inserted.values()) == 0
    assert sum(second.skipped.values()) == 11 + 19 + 10 + 11 + 4


def test_init_db_creates_missing_parent_directory(tmp_path: Path) -> None:
    nested = tmp_path / "nested" / "subdir" / "requirements.db"
    assert not nested.parent.exists()

    init_db(nested)

    assert nested.parent.is_dir()
    assert nested.exists()


def test_init_db_uses_resolver_when_no_argument(
    monkeypatch: pytest.MonkeyPatch, temp_db_path: Path
) -> None:
    monkeypatch.setenv("REQUIREMENTS_DB_PATH", str(temp_db_path))

    resolved, _ = init_db()

    assert resolved == temp_db_path.resolve()
    assert temp_db_path.exists()


def test_init_db_drop_first_resets_data(temp_db_path: Path) -> None:
    from requirements_mcp.db.engine import make_engine, make_session_factory
    from requirements_mcp.models import IssueStatus

    init_db(temp_db_path)

    engine = make_engine(temp_db_path)
    factory = make_session_factory(engine)
    with factory() as session:
        row = session.get(IssueStatus, "open")
        assert row is not None
        row.description = "modified"
        session.commit()

    init_db(temp_db_path, drop_first=True)

    engine2 = make_engine(temp_db_path)
    factory2 = make_session_factory(engine2)
    with factory2() as session:
        row = session.get(IssueStatus, "open")
        assert row is not None
        assert row.description != "modified"
