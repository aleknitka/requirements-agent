"""Tests for ``requirements_mcp.config.resolve_db_path``."""

from __future__ import annotations

from pathlib import Path

import pytest

from requirements_mcp.config import DEFAULT_DB_PATH, ENV_VAR, resolve_db_path


def test_cli_argument_wins_over_env_and_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "from_env.db"))
    cli_path = tmp_path / "from_cli.db"

    resolved = resolve_db_path(cli_path)

    assert resolved == cli_path.resolve()


def test_env_used_when_no_cli_argument(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_path = tmp_path / "env.db"
    monkeypatch.setenv(ENV_VAR, str(env_path))

    resolved = resolve_db_path(None)

    assert resolved == env_path.resolve()


def test_default_used_when_nothing_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)

    resolved = resolve_db_path(None)

    assert resolved == DEFAULT_DB_PATH.expanduser().resolve()


def test_returns_absolute_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)

    resolved = resolve_db_path("relative.db")

    assert resolved.is_absolute()
