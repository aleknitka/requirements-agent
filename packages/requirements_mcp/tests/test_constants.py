"""Tests for :mod:`requirements_mcp.constants`."""

from __future__ import annotations

import importlib

import pytest


def _reload_constants(monkeypatch: pytest.MonkeyPatch, value: str | None):
    if value is None:
        monkeypatch.delenv("REQUIREMENTS_PROJECT_NAME", raising=False)
    else:
        monkeypatch.setenv("REQUIREMENTS_PROJECT_NAME", value)
    import requirements_mcp.constants as constants_mod

    return importlib.reload(constants_mod)


@pytest.fixture(autouse=True)
def _restore_constants():
    """Reload the module with a clean env after each test so other tests
    are not affected by a failed reload that left stale module attributes."""
    yield
    import os

    os.environ.pop("REQUIREMENTS_PROJECT_NAME", None)
    import requirements_mcp.constants as constants_mod

    importlib.reload(constants_mod)


def test_default_project_name(monkeypatch: pytest.MonkeyPatch) -> None:
    constants = _reload_constants(monkeypatch, None)
    assert constants.PROJECT_NAME == "PROJECT"
    assert constants.APP_NAME == "requirements db"
    assert constants.APP_TITLE == "PROJECT - requirements db"


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    constants = _reload_constants(monkeypatch, "DEMO")
    assert constants.PROJECT_NAME == "DEMO"
    assert constants.APP_TITLE == "DEMO - requirements db"


@pytest.mark.parametrize(
    "bad",
    [
        "",  # too short
        "ab",  # 2 chars
        "x" * 16,  # 16 chars
        "has space",  # space invalid
        "bad/name",  # slash invalid
        "bad.name",  # dot invalid
    ],
)
def test_rejects_invalid_names(monkeypatch: pytest.MonkeyPatch, bad: str) -> None:
    with pytest.raises(ValueError):
        _reload_constants(monkeypatch, bad)


def test_accepts_full_charset(monkeypatch: pytest.MonkeyPatch) -> None:
    constants = _reload_constants(monkeypatch, "Abc-1_2")
    assert constants.PROJECT_NAME == "Abc-1_2"
