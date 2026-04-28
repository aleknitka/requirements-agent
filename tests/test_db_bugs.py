"""
test_db_bugs.py — TDD RED tests for BUG-01, BUG-03, BUG-04 in requirements_agent_tools.db.

Plan: 00-01 (phase 00-bug-triage)

Bugs under test:
  BUG-01 — C.DB_PATH does not exist: `import requirements_agent_tools.db` raises AttributeError.
  BUG-03 — `list_all_projects` does not exist in db.py; canonical name is list_projects.
  BUG-04 — `_make_req_id` uses `req_type.id_prefix` which does not exist; must use .value.
"""

import inspect
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_SOURCE = REPO_ROOT / "src" / "requirements_agent_tools" / "db" / "requirements.py"


def _fresh_import():
    import requirements_agent_tools.db as db_mod
    from requirements_agent_tools.db import connection, projects  # noqa: F401

    return db_mod


class TestImportDB:
    """BUG-01: import requirements_agent_tools.db must not raise AttributeError."""

    def test_import_db_does_not_raise(self):
        _fresh_import()


class TestGetDbSignature:
    """BUG-01: get_db must require an explicit path (no default argument)."""

    def test_get_db_has_no_default_argument(self):
        db = _fresh_import()
        sig = inspect.signature(db.connection.get_db)
        param = sig.parameters["path"]
        assert param.default is inspect.Parameter.empty, (
            "get_db must not have a default for `path`"
        )

    def test_get_db_raises_type_error_when_called_without_args(self):
        db = _fresh_import()
        with pytest.raises(TypeError):
            db.connection.get_db()


class TestListProjectsCanonicalName:
    """BUG-03: list_projects must exist; list_all_projects must NOT exist."""

    def test_list_projects_exists(self):
        db = _fresh_import()
        assert hasattr(db.projects, "list_projects"), (
            "db.projects must expose list_projects(conn)"
        )

    def test_list_all_projects_does_not_exist(self):
        db = _fresh_import()
        assert not hasattr(db.projects, "list_all_projects"), (
            "db.projects must not expose list_all_projects"
        )


class TestMakeReqIdUsesValue:
    """BUG-04: _make_req_id must use req_type.value not req_type.id_prefix."""

    def test_make_req_id_source_uses_value_not_id_prefix(self):
        source = DB_SOURCE.read_text()
        assert "req_type.value" in source, "_make_req_id must use req_type.value"
        assert "id_prefix" not in source, "_make_req_id must not reference id_prefix"
