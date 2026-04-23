"""
test_db_bugs.py — TDD RED tests for BUG-01, BUG-03, BUG-04 in shared/db.py.

Plan: 00-01 (phase 00-bug-triage)

Bugs under test:
  BUG-01 — C.DB_PATH does not exist: `import shared.db` raises AttributeError.
  BUG-03 — `list_all_projects` does not exist in db.py; canonical name is list_projects.
  BUG-04 — `_make_req_id` uses `req_type.id_prefix` which does not exist; must use .value.

These tests are written BEFORE the fixes and MUST fail against the current code.
After the fixes in Task 1, they MUST all pass.
"""

import inspect
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class TestImportDB:
    """BUG-01: import shared.db must not raise AttributeError."""

    def test_import_shared_db_does_not_raise(self):
        """Importing shared.db must succeed without AttributeError."""
        # Remove cached broken import if present so we get a real import
        for key in list(sys.modules.keys()):
            if key in ("shared.db", "db"):
                del sys.modules[key]

        import shared.db  # noqa: F401 — must not raise


class TestGetDbSignature:
    """BUG-01: get_db must require an explicit path (no default argument)."""

    def test_get_db_has_no_default_argument(self):
        """get_db(path: str) must have no default value for `path`."""
        for key in list(sys.modules.keys()):
            if key in ("shared.db", "db"):
                del sys.modules[key]

        import shared.db

        sig = inspect.signature(shared.db.get_db)
        param = sig.parameters["path"]
        assert param.default is inspect.Parameter.empty, (
            "get_db must not have a default for `path` (C.DB_PATH does not exist)"
        )

    def test_get_db_raises_type_error_when_called_without_args(self):
        """Calling get_db() without arguments must raise TypeError."""
        for key in list(sys.modules.keys()):
            if key in ("shared.db", "db"):
                del sys.modules[key]

        import shared.db

        with pytest.raises(TypeError):
            shared.db.get_db()


class TestListProjectsCanonicalName:
    """BUG-03: list_projects must exist; list_all_projects must NOT exist."""

    def test_list_projects_exists(self):
        """db.list_projects must be present."""
        for key in list(sys.modules.keys()):
            if key in ("shared.db", "db"):
                del sys.modules[key]

        import shared.db

        assert hasattr(shared.db, "list_projects"), (
            "shared.db must expose list_projects(conn)"
        )

    def test_list_all_projects_does_not_exist(self):
        """db.list_all_projects must NOT be present (callers will be fixed in later plans)."""
        for key in list(sys.modules.keys()):
            if key in ("shared.db", "db"):
                del sys.modules[key]

        import shared.db

        assert not hasattr(shared.db, "list_all_projects"), (
            "shared.db must not expose list_all_projects (callers fixed in 00-03/00-04)"
        )


class TestMakeReqIdUsesValue:
    """BUG-04: _make_req_id must use req_type.value not req_type.id_prefix."""

    def test_make_req_id_source_uses_value_not_id_prefix(self):
        """_make_req_id must reference req_type.value in its source."""
        source_path = REPO_ROOT / "shared" / "db.py"
        source = source_path.read_text()

        # Must use .value
        assert "req_type.value" in source, (
            "_make_req_id must use req_type.value"
        )
        # Must NOT use .id_prefix
        assert "id_prefix" not in source, (
            "_make_req_id must not reference id_prefix (does not exist on str Enum)"
        )
