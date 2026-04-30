"""
CLI subprocess tests for requirements_agent_tools.init_project.

After the src/ layout migration:
  - The script is invoked via `python -m requirements_agent_tools.init_project`.
  - The module is imported directly (relative imports require package context).

Phase 1 rewrite (Plan 04):
  - TestInitHelp: tests the setup subcommand (not new/list/update)
  - TestBuildParser: tests setup subcommand parsing
  - TestOutputHelpers: tests _ok and _err helpers (imported from _cli_io)
  - TestParseJson removed: _parse_json was removed from init_project.py in Plan 04
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = "requirements_agent_tools.init_project"


def _run(*args, **kwargs):
    return subprocess.run(
        [sys.executable, "-m", MODULE, *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        **kwargs,
    )


class TestInitHelp:
    def test_help_exits_0(self):
        assert _run("--help").returncode == 0

    def test_help_mentions_setup(self):
        result = _run("--help")
        output = result.stdout + result.stderr
        assert "setup" in output.lower()

    def test_setup_help_exits_0(self):
        assert _run("setup", "--help").returncode == 0


@pytest.fixture(scope="module")
def init():
    """Import the init_project module as a package member."""
    import requirements_agent_tools.init_project as module

    return module


class TestBuildParser:
    def test_setup_subcommand_registered(self, init):
        args = init.build_parser().parse_args(["setup"])
        assert args.command == "setup"

    def test_no_subcommand_exits_nonzero(self):
        result = _run()
        assert result.returncode != 0


class TestOutputHelpers:
    def test_ok_writes_json_with_ok_true_to_stdout(self, init, capsys):
        init._ok({"key": "val"})
        out, _ = capsys.readouterr()
        payload = json.loads(out)
        assert payload["ok"] is True
        assert payload["key"] == "val"

    def test_err_writes_json_with_ok_false_to_stderr(self, init, capsys):
        with pytest.raises(SystemExit):
            init._err("boom")
        _, err = capsys.readouterr()
        payload = json.loads(err)
        assert payload["ok"] is False
        assert payload["error"] == "boom"

    def test_err_exits_with_code_1(self, init):
        with pytest.raises(SystemExit) as exc:
            init._err("boom")
        assert exc.value.code == 1
