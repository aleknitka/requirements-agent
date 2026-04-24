"""
CLI subprocess tests for skills/new-project-initiation/scripts/init.py

Replaces the old MagicMock-based test file that loaded init.py from a non-existent
path (agents/project-initiation-assistant/...) and patched around import crashes.

After Phase 0 bug fixes:
  BUG-02 — init.py now uses bare imports (D-09) and can be imported cleanly.
  BUG-03 — db.py exposes list_projects(conn), not list_all_projects().

Strategy (D-15/D-16):
  - Subprocess tests verify --help exits 0 and subcommands are listed.
  - Parser/helper unit tests load init.py via importlib from the correct path
    (skills/new-project-initiation/scripts/init.py) with no MagicMock patching.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INIT_PATH = REPO_ROOT / "skills" / "new-project-initiation" / "scripts" / "init.py"


# ═══════════════════════════════════════════════════════════════════════════════
# Subprocess CLI tests (D-16) — verify BUG-02 is fixed
# ═══════════════════════════════════════════════════════════════════════════════


class TestInitHelp:
    def test_help_exits_0(self):
        """BUG-02: init.py --help must exit 0 after bare-import fix."""
        result = subprocess.run(
            [sys.executable, str(INIT_PATH), "--help"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0

    def test_help_mentions_subcommands(self):
        """--help output must mention at least one subcommand (new or list)."""
        result = subprocess.run(
            [sys.executable, str(INIT_PATH), "--help"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        output = result.stdout + result.stderr
        assert "new" in output.lower() or "list" in output.lower()

    def test_new_help_exits_0(self):
        """new --help must exit 0 and show usage for the 'new' subcommand."""
        result = subprocess.run(
            [sys.executable, str(INIT_PATH), "new", "--help"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0

    def test_list_help_exits_0(self):
        """list --help must exit 0."""
        result = subprocess.run(
            [sys.executable, str(INIT_PATH), "list", "--help"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0

    def test_update_help_exits_0(self):
        """update --help must exit 0."""
        result = subprocess.run(
            [sys.executable, str(INIT_PATH), "update", "--help"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0

    def test_new_without_name_exits_nonzero(self):
        """'new' without --name must exit non-zero (required argument)."""
        result = subprocess.run(
            [sys.executable, str(INIT_PATH), "new"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0

    def test_init_path_is_correct(self):
        """Verify INIT_PATH points to the skills/ directory, not agents/."""
        assert "skills" in str(INIT_PATH)
        assert "agents" not in str(INIT_PATH)
        assert INIT_PATH.exists(), f"init.py not found at {INIT_PATH}"


# ═══════════════════════════════════════════════════════════════════════════════
# Module fixture — load init.py via importlib (no MagicMock)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def init():
    """
    Load init.py from skills/new-project-initiation/scripts/init.py.

    spec.loader.exec_module() runs the module body, which includes the
    sys.path.insert for shared/. After Phase 0 fixes the import succeeds
    without any mocking.
    """
    spec = importlib.util.spec_from_file_location("init", INIT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ═══════════════════════════════════════════════════════════════════════════════
# Parser tests — using real module, no MagicMock
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildParser:
    def test_new_requires_name(self, init):
        """'new' without --name must raise SystemExit."""
        with pytest.raises(SystemExit):
            init.build_parser().parse_args(["new"])

    def test_new_parses_name(self, init):
        """'new --name My Project' must set args.name and args.command."""
        args = init.build_parser().parse_args(["new", "--name", "My Project"])
        assert args.name == "My Project"
        assert args.command == "new"

    def test_new_default_phase_is_discovery(self, init):
        """'new' default phase must be 'discovery'."""
        args = init.build_parser().parse_args(["new", "--name", "X"])
        assert args.phase == "discovery"

    def test_new_all_phases_accepted(self, init):
        """'new' must accept all valid ProjectPhase values."""
        from models import ProjectPhase  # imported via shared/ on sys.path

        for phase in ProjectPhase:
            args = init.build_parser().parse_args(["new", "--name", "X", "--phase", phase.value])
            assert args.phase == phase.value

    def test_new_optional_fields_parsed(self, init):
        """'new' must parse optional metadata fields correctly."""
        args = init.build_parser().parse_args([
            "new", "--name", "P", "--code", "P1",
            "--objective", "obj", "--business-case", "bc",
            "--project-owner", "Alice", "--sponsor", "Bob",
        ])
        assert args.code == "P1"
        assert args.objective == "obj"
        assert args.business_case == "bc"
        assert args.project_owner == "Alice"
        assert args.sponsor == "Bob"

    def test_list_subcommand(self, init):
        """'list' subcommand must parse with command='list'."""
        args = init.build_parser().parse_args(["list"])
        assert args.command == "list"

    def test_update_requires_project(self, init):
        """'update' without --project must raise SystemExit."""
        with pytest.raises(SystemExit):
            init.build_parser().parse_args(["update"])

    def test_update_parses_project_slug(self, init):
        """'update --project my-slug' must set args.project and args.command."""
        args = init.build_parser().parse_args(["update", "--project", "my-slug"])
        assert args.project == "my-slug"
        assert args.command == "update"

    def test_update_rejects_invalid_phase(self, init):
        """'update --phase invalid' must raise SystemExit."""
        with pytest.raises(SystemExit):
            init.build_parser().parse_args(["update", "--project", "x", "--phase", "invalid"])


# ═══════════════════════════════════════════════════════════════════════════════
# _parse_json helper tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseJson:
    def test_none_returns_empty_list(self, init):
        assert init._parse_json(None, "field") == []

    def test_empty_string_returns_empty_list(self, init):
        assert init._parse_json("", "field") == []

    def test_valid_string_array(self, init):
        assert init._parse_json('["a", "b"]', "field") == ["a", "b"]

    def test_valid_object_array(self, init):
        data = '[{"name": "Alice", "role": "sponsor"}]'
        assert init._parse_json(data, "stakeholders") == [{"name": "Alice", "role": "sponsor"}]

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


# ═══════════════════════════════════════════════════════════════════════════════
# _ok / _err output helper tests
# ═══════════════════════════════════════════════════════════════════════════════


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
