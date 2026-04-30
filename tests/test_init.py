"""
CLI subprocess tests for requirements_agent_tools.init_project.

After the src/ layout migration:
  - The script is invoked via `python -m requirements_agent_tools.init_project`.
  - The module is imported directly (relative imports require package context).

Phase 1 rewrite:
  - TestInitHelp: tests the setup subcommand (not new/list/update)
  - TestBuildParser: tests setup subcommand parsing
  - TestParseJson and TestOutputHelpers: unchanged (helpers survive rewrite)
  - Tests that depend on cmd_setup() not yet implemented are marked xfail.
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

    @pytest.mark.xfail(
        strict=False,
        reason="cmd_setup() not yet implemented — requires Plan 02",
    )
    def test_help_mentions_setup(self):
        result = _run("--help")
        output = result.stdout + result.stderr
        assert "setup" in output.lower()

    @pytest.mark.xfail(
        strict=False,
        reason="setup subcommand not yet registered — requires Plan 02",
    )
    def test_setup_help_exits_0(self):
        assert _run("setup", "--help").returncode == 0


@pytest.fixture(scope="module")
def init():
    """Import the init_project module as a package member."""
    import requirements_agent_tools.init_project as module

    return module


class TestBuildParser:
    @pytest.mark.xfail(
        strict=False,
        reason="setup subcommand not yet registered in build_parser() — requires Plan 02",
    )
    def test_setup_subcommand_registered(self, init):
        args = init.build_parser().parse_args(["setup"])
        assert args.command == "setup"

    def test_no_subcommand_exits_nonzero(self):
        result = _run()
        assert result.returncode != 0


class TestParseJson:
    def test_none_returns_empty_list(self, init):
        assert init._parse_json(None, "field") == []

    def test_empty_string_returns_empty_list(self, init):
        assert init._parse_json("", "field") == []

    def test_valid_string_array(self, init):
        assert init._parse_json('["a", "b"]', "field") == ["a", "b"]

    def test_valid_object_array(self, init):
        data = '[{"name": "Alice", "role": "sponsor"}]'
        assert init._parse_json(data, "stakeholders") == [
            {"name": "Alice", "role": "sponsor"}
        ]

    def test_invalid_json_exits_1(self, init):
        with pytest.raises(SystemExit) as exc:
            init._parse_json("not-json", "field")
        assert exc.value.code == 1

    def test_object_not_array_exits_1(self, init):
        with pytest.raises(SystemExit) as exc:
            init._parse_json('{"key": "v"}', "field")
        assert exc.value.code == 1

    def test_error_message_names_the_field(self, init, capsys):
        with pytest.raises(SystemExit):
            init._parse_json("42", "my-field")
        _, err = capsys.readouterr()
        payload = json.loads(err)
        assert payload["ok"] is False
        assert "my-field" in payload["error"]


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
