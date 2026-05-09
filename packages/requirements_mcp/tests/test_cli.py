"""Tests for the ``requirements-db-init`` CLI.

The CLI no longer accepts a ``--db`` flag — the database path is
locked to ``./data/requirements.db``. Tests therefore ``chdir`` into
``tmp_path`` so each invocation creates its database under the
temporary directory rather than the developer's checkout.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect

from requirements_mcp.cli import _build_db_init_parser, db_init
from requirements_mcp.db.engine import make_engine, make_session_factory
from requirements_mcp.models import Issue, Requirement, RequirementIssueLink


def _expected_db(tmp_path: Path) -> Path:
    return (tmp_path / "data" / "requirements.db").resolve()


def test_db_init_succeeds_at_fixed_path(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = db_init([])
    captured = capsys.readouterr()
    expected = _expected_db(tmp_path)

    assert exit_code == 0
    assert expected.exists()
    assert "Database ready at:" in captured.out

    engine = make_engine(expected)
    assert "requirement_statuses" in inspect(engine).get_table_names()


def test_db_init_aborts_on_unconfirmed_reset(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    db_init([])
    capsys.readouterr()

    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    exit_code = db_init(["--reset"])
    assert exit_code == 1


def test_db_init_reset_with_yes_flag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    db_init([])
    exit_code = db_init(["--reset", "--yes"])
    assert exit_code == 0
    assert _expected_db(tmp_path).exists()


def test_db_init_rejects_db_flag() -> None:
    """The --db flag is gone; argparse must reject it."""
    with pytest.raises(SystemExit):
        _build_db_init_parser().parse_args(["--db", "anything"])


def test_db_init_demo_data_populates(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = db_init(["--demo-data"])
    captured = capsys.readouterr()
    expected = _expected_db(tmp_path)

    assert exit_code == 0
    assert "Demo data: 10 requirements, 5 issues, 3 links inserted" in captured.out

    engine = make_engine(expected)
    factory = make_session_factory(engine)
    with factory() as session:
        assert session.query(Requirement).count() == 10
        assert session.query(Issue).count() == 5
        assert session.query(RequirementIssueLink).count() == 3


def test_db_init_without_demo_leaves_db_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    db_init([])

    engine = make_engine(_expected_db(tmp_path))
    factory = make_session_factory(engine)
    with factory() as session:
        assert session.query(Requirement).count() == 0
        assert session.query(Issue).count() == 0


def test_db_init_demo_data_idempotent(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    db_init(["--demo-data"])
    capsys.readouterr()

    exit_code = db_init(["--demo-data"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Demo data: skipped (existing requirements found)." in captured.out

    engine = make_engine(_expected_db(tmp_path))
    factory = make_session_factory(engine)
    with factory() as session:
        assert session.query(Requirement).count() == 10
