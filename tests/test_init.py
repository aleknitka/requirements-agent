"""
CLI subprocess tests for requirements_agent_tools.init_project.

After the src/ layout migration:
  - The script is invoked via `python -m requirements_agent_tools.init_project`.
  - The module is imported directly (relative imports require package context).
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

    def test_help_mentions_subcommands(self):
        result = _run("--help")
        output = result.stdout + result.stderr
        assert "new" in output.lower() or "list" in output.lower()

    def test_new_help_exits_0(self):
        assert _run("new", "--help").returncode == 0

    def test_list_help_exits_0(self):
        assert _run("list", "--help").returncode == 0

    def test_update_help_exits_0(self):
        assert _run("update", "--help").returncode == 0

    def test_new_without_name_exits_nonzero(self):
        assert _run("new").returncode != 0


@pytest.fixture(scope="module")
def init():
    """Import the init_project module as a package member."""
    import requirements_agent_tools.init_project as module

    return module


class TestBuildParser:
    def test_new_requires_name(self, init):
        with pytest.raises(SystemExit):
            init.build_parser().parse_args(["new"])

    def test_new_parses_name(self, init):
        args = init.build_parser().parse_args(["new", "--name", "My Project"])
        assert args.name == "My Project"
        assert args.command == "new"

    def test_new_default_phase_is_discovery(self, init):
        args = init.build_parser().parse_args(["new", "--name", "X"])
        assert args.phase == "discovery"

    def test_new_all_phases_accepted(self, init):
        from requirements_agent_tools.models import ProjectPhase

        for phase in ProjectPhase:
            args = init.build_parser().parse_args(
                ["new", "--name", "X", "--phase", phase.value]
            )
            assert args.phase == phase.value

    def test_new_optional_fields_parsed(self, init):
        args = init.build_parser().parse_args(
            [
                "new",
                "--name",
                "P",
                "--code",
                "P1",
                "--objective",
                "obj",
                "--business-case",
                "bc",
                "--project-owner",
                "Alice",
                "--sponsor",
                "Bob",
            ]
        )
        assert args.code == "P1"
        assert args.objective == "obj"
        assert args.business_case == "bc"
        assert args.project_owner == "Alice"
        assert args.sponsor == "Bob"

    def test_list_subcommand(self, init):
        args = init.build_parser().parse_args(["list"])
        assert args.command == "list"

    def test_update_requires_project(self, init):
        with pytest.raises(SystemExit):
            init.build_parser().parse_args(["update"])

    def test_update_parses_project_slug(self, init):
        args = init.build_parser().parse_args(["update", "--project", "my-slug"])
        assert args.project == "my-slug"
        assert args.command == "update"

    def test_update_rejects_invalid_phase(self, init):
        with pytest.raises(SystemExit):
            init.build_parser().parse_args(
                ["update", "--project", "x", "--phase", "invalid"]
            )


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
