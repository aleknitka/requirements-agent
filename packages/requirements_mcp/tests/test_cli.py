"""Tests for the ``requirements-db-init`` CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect

from requirements_mcp.cli import db_init
from requirements_mcp.db.engine import make_engine


def test_db_init_succeeds_with_explicit_path(
    capsys: pytest.CaptureFixture[str], temp_db_path: Path
) -> None:
    exit_code = db_init(["--db", str(temp_db_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert temp_db_path.exists()
    assert "Database ready at:" in captured.out

    engine = make_engine(temp_db_path)
    assert "requirement_statuses" in inspect(engine).get_table_names()


def test_db_init_aborts_on_unconfirmed_reset(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    temp_db_path: Path,
) -> None:
    db_init(["--db", str(temp_db_path)])
    capsys.readouterr()

    monkeypatch.setattr("builtins.input", lambda _prompt: "n")

    exit_code = db_init(["--db", str(temp_db_path), "--reset"])

    assert exit_code == 1


def test_db_init_reset_with_yes_flag(
    capsys: pytest.CaptureFixture[str], temp_db_path: Path
) -> None:
    db_init(["--db", str(temp_db_path)])
    capsys.readouterr()

    exit_code = db_init(["--db", str(temp_db_path), "--reset", "--yes"])

    assert exit_code == 0
    assert temp_db_path.exists()
