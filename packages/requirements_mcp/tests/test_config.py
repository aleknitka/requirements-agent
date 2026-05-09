"""Tests for ``requirements_mcp.config``."""

from __future__ import annotations

from pathlib import Path

import pytest

from requirements_mcp.config import (
    DEFAULT_DB_PATH,
    DEFAULT_HOST,
    DEFAULT_PORT,
    ENV_VAR,
    HOST_ENV_VAR,
    PORT_ENV_VAR,
    load_yaml_config,
    resolve_db_path,
    resolve_host,
    resolve_port,
)


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


# ---- load_yaml_config ----------------------------------------------------


def test_load_yaml_config_returns_empty_when_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no.yaml"
    assert load_yaml_config(missing) == {}


def test_load_yaml_config_parses_mapping(tmp_path: Path) -> None:
    cfg_file = tmp_path / "default.yaml"
    cfg_file.write_text("host: 0.0.0.0\nport: 9000\n", encoding="utf-8")
    assert load_yaml_config(cfg_file) == {"host": "0.0.0.0", "port": 9000}


def test_load_yaml_config_ignores_non_mapping(tmp_path: Path) -> None:
    cfg_file = tmp_path / "default.yaml"
    cfg_file.write_text("- a\n- b\n", encoding="utf-8")
    assert load_yaml_config(cfg_file) == {}


def test_load_yaml_config_ignores_malformed(tmp_path: Path) -> None:
    cfg_file = tmp_path / "default.yaml"
    cfg_file.write_text(": : :\n", encoding="utf-8")
    assert load_yaml_config(cfg_file) == {}


# ---- resolve_host --------------------------------------------------------


def test_resolve_host_cli_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(HOST_ENV_VAR, "1.2.3.4")
    assert resolve_host("9.9.9.9", config={"host": "8.8.8.8"}) == "9.9.9.9"


def test_resolve_host_env_wins_over_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(HOST_ENV_VAR, "1.2.3.4")
    assert resolve_host(None, config={"host": "8.8.8.8"}) == "1.2.3.4"


def test_resolve_host_config_used_when_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(HOST_ENV_VAR, raising=False)
    assert resolve_host(None, config={"host": "0.0.0.0"}) == "0.0.0.0"


def test_resolve_host_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(HOST_ENV_VAR, raising=False)
    assert resolve_host(None, config={}) == DEFAULT_HOST


# ---- resolve_port --------------------------------------------------------


def test_resolve_port_cli_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PORT_ENV_VAR, "8000")
    assert resolve_port(9000, config={"port": 7000}) == 9000


def test_resolve_port_cli_out_of_range_raises() -> None:
    with pytest.raises(ValueError):
        resolve_port(70000, config={})
    with pytest.raises(ValueError):
        resolve_port(0, config={})


def test_resolve_port_env_wins_over_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PORT_ENV_VAR, "8000")
    assert resolve_port(None, config={"port": 7000}) == 8000


def test_resolve_port_invalid_env_falls_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PORT_ENV_VAR, "not-a-number")
    assert resolve_port(None, config={"port": 7000}) == 7000


def test_resolve_port_out_of_range_env_falls_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PORT_ENV_VAR, "70000")
    assert resolve_port(None, config={"port": 7000}) == 7000


def test_resolve_port_config_used_when_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PORT_ENV_VAR, raising=False)
    assert resolve_port(None, config={"port": 7000}) == 7000


def test_resolve_port_invalid_config_falls_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PORT_ENV_VAR, raising=False)
    assert resolve_port(None, config={"port": "not-an-int"}) == DEFAULT_PORT
    assert resolve_port(None, config={"port": 70000}) == DEFAULT_PORT


def test_resolve_port_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PORT_ENV_VAR, raising=False)
    assert resolve_port(None, config={}) == DEFAULT_PORT
