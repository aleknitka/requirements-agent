"""
tests/test_setup.py — Unit tests for init_project.cmd_setup() and get_project_conn().

Tests cover INIT-01 through INIT-06:
  INIT-01: project/ directory scaffold created
  INIT-02: project/project.db bootstrapped
  INIT-03: config/project.yaml written with sqlite_vec and otel_enabled
  INIT-04: interactive prompts (click.confirm) accept inputs correctly
  INIT-05: guard exits non-zero on second run
  INIT-06: get_project_conn() opens DB when present; exits with error when absent

Note: Tests calling cmd_setup() or get_project_conn() are marked xfail until
Plans 02-04 implement init_project.cmd_setup(), CONSTANTS flat paths, and
project_session.get_project_conn(). When those plans execute, the xfail
markers must be removed and the tests must pass.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def project_env(tmp_path, monkeypatch):
    """Patch CONSTANTS to use a tmp project directory so tests are isolated."""
    import requirements_agent_tools.CONSTANTS as C

    project_dir = tmp_path / "project"
    monkeypatch.setattr(C, "PROJECT_DIR", project_dir)
    monkeypatch.setattr(C, "DB_PATH", project_dir / "project.db")
    monkeypatch.setattr(C, "MD_PATH", project_dir / "PROJECT.md")
    # Patch _AGENT_ROOT so config/project.yaml writes to tmp_path/config/
    monkeypatch.setattr(C, "_AGENT_ROOT", tmp_path)
    (tmp_path / "config").mkdir(exist_ok=True)
    yield tmp_path


@pytest.fixture()
def setup_module():
    """Import init_project module."""
    import requirements_agent_tools.init_project as m

    return m


# ── Helpers ───────────────────────────────────────────────────────────────────


def _run_setup(project_env, answers=None):
    """Run cmd_setup() with click prompts patched to return given answers.

    answers is a list of bool values consumed in order by click.confirm calls.
    Default: all False (sqlite_vec=no, otel=no, no .gitignore entries).
    """
    import argparse

    import requirements_agent_tools.init_project as m

    if answers is None:
        # sqlite_vec=False, otel=False, gitignore entries all False
        answers = [False, False, False, False, False]

    answer_iter = iter(answers)

    def _fake_confirm(prompt, default=False, **kw):
        return next(answer_iter)

    args = argparse.Namespace(command="setup")
    with patch("click.confirm", side_effect=_fake_confirm):
        m.cmd_setup(args)


# ── INIT-01: directory scaffold ───────────────────────────────────────────────


@pytest.mark.xfail(
    strict=False,
    reason="cmd_setup() not yet implemented — requires Plan 02",
)
def test_setup_creates_project_dir(project_env):
    """cmd_setup() creates project/ directory."""
    _run_setup(project_env)
    import requirements_agent_tools.CONSTANTS as C

    assert C.PROJECT_DIR.is_dir()


@pytest.mark.xfail(
    strict=False,
    reason="cmd_setup() not yet implemented — requires Plan 02",
)
def test_setup_creates_subdirs(project_env):
    """cmd_setup() creates project/logs/ and project/notes/ subdirectories."""
    _run_setup(project_env)
    import requirements_agent_tools.CONSTANTS as C

    assert (C.PROJECT_DIR / "logs").is_dir()
    assert (C.PROJECT_DIR / "notes").is_dir()


# ── INIT-02: DB bootstrap ─────────────────────────────────────────────────────


@pytest.mark.xfail(
    strict=False,
    reason="cmd_setup() not yet implemented — requires Plan 02",
)
def test_setup_bootstraps_db(project_env):
    """cmd_setup() creates project/project.db that opens as valid SQLite."""
    _run_setup(project_env)
    import requirements_agent_tools.CONSTANTS as C

    assert C.DB_PATH.exists()
    conn = sqlite3.connect(str(C.DB_PATH))
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()
    assert "projects" in tables
    assert "requirements" in tables


@pytest.mark.xfail(
    strict=False,
    reason="cmd_setup() not yet implemented — requires Plan 02",
)
def test_projects_table_has_no_slug_column(project_env):
    """After setup, projects table must NOT contain a slug column (D-01)."""
    _run_setup(project_env)
    import requirements_agent_tools.CONSTANTS as C

    conn = sqlite3.connect(str(C.DB_PATH))
    cols = [row[1] for row in conn.execute("PRAGMA table_info(projects)").fetchall()]
    conn.close()
    assert "slug" not in cols, f"slug column must not exist: {cols}"


# ── INIT-03: config/project.yaml ──────────────────────────────────────────────


@pytest.mark.xfail(
    strict=False,
    reason="cmd_setup() not yet implemented — requires Plan 02",
)
def test_setup_writes_config_yaml(project_env):
    """cmd_setup() writes config/project.yaml with sqlite_vec and otel_enabled."""
    _run_setup(project_env)
    config_path = project_env / "config" / "project.yaml"
    assert config_path.exists()
    cfg = yaml.safe_load(config_path.read_text())
    assert "sqlite_vec" in cfg
    assert "otel_enabled" in cfg


@pytest.mark.xfail(
    strict=False,
    reason="cmd_setup() not yet implemented — requires Plan 02",
)
def test_setup_config_reflects_answers(project_env):
    """config/project.yaml reflects user's interactive answers (per D-11)."""
    # sqlite_vec=True, otel=True, gitignore entries all False
    _run_setup(project_env, answers=[True, True, False, False, False])
    config_path = project_env / "config" / "project.yaml"
    cfg = yaml.safe_load(config_path.read_text())
    assert cfg["sqlite_vec"] is True
    assert cfg["otel_enabled"] is True


# ── INIT-04: interactive prompts ──────────────────────────────────────────────


@pytest.mark.xfail(
    strict=False,
    reason="cmd_setup() not yet implemented — requires Plan 02",
)
def test_setup_interactive_prompts(project_env):
    """cmd_setup() calls click.confirm for sqlite-vec, OTel, and gitignore entries."""
    confirm_calls = []

    def _tracking_confirm(prompt, default=False, **kw):
        confirm_calls.append(prompt)
        return False

    import argparse

    import requirements_agent_tools.init_project as m

    args = argparse.Namespace(command="setup")
    with patch("click.confirm", side_effect=_tracking_confirm):
        m.cmd_setup(args)

    # Must have at least 2 confirm calls: sqlite_vec + otel + up to 3 gitignore
    assert len(confirm_calls) >= 2


# ── INIT-05: guard on second run ──────────────────────────────────────────────


@pytest.mark.xfail(
    strict=False,
    reason="cmd_setup() not yet implemented — requires Plan 02",
)
def test_setup_guard_on_second_run(project_env):
    """Second call to cmd_setup() exits non-zero with guard message (D-07)."""
    import argparse

    import requirements_agent_tools.init_project as m

    args = argparse.Namespace(command="setup")

    def _no_confirm(prompt, default=False, **kw):
        return False

    # First run succeeds
    with patch("click.confirm", side_effect=_no_confirm):
        m.cmd_setup(args)

    # Second run must call _err() (which raises SystemExit with code 1)
    with patch("click.confirm", side_effect=_no_confirm):
        with pytest.raises(SystemExit) as exc:
            m.cmd_setup(args)
    assert exc.value.code == 1


# ── INIT-06: get_project_conn ─────────────────────────────────────────────────


@pytest.mark.xfail(
    strict=False,
    reason="get_project_conn() and cmd_setup() not yet implemented — requires Plans 02-04",
)
def test_get_project_conn_opens_db(project_env):
    """get_project_conn() returns a valid sqlite3.Connection when DB exists."""
    _run_setup(project_env)

    import requirements_agent_tools.project_session as ps

    conn = ps.get_project_conn()
    assert conn is not None
    # Verify it is a real connection by running a trivial query
    result = conn.execute("SELECT 1").fetchone()
    assert result[0] == 1
    conn.close()


@pytest.mark.xfail(
    strict=False,
    reason="get_project_conn() not yet implemented — requires Plan 02",
)
def test_get_project_conn_no_db(project_env):
    """get_project_conn() exits non-zero when DB does not exist (D-04)."""
    import requirements_agent_tools.project_session as ps

    # DB_PATH does not exist yet (project_env is empty)
    with pytest.raises(SystemExit) as exc:
        ps.get_project_conn()
    assert exc.value.code == 1
