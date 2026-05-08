"""Configuration helpers, primarily database-path resolution.

The database path can be supplied on the command line, exported via the
``REQUIREMENTS_DB_PATH`` environment variable, or left to the default at
``./data/requirements.db`` (relative to the current working directory).
:func:`resolve_db_path` applies that priority order and returns an
absolute path, which both the CLI and the MCP server use to locate the
SQLite file.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "requirements.db"
"""Default SQLite location when neither CLI nor environment overrides it."""

ENV_VAR = "REQUIREMENTS_DB_PATH"
"""Name of the environment variable that overrides :data:`DEFAULT_DB_PATH`."""


def resolve_db_path(cli_arg: str | os.PathLike[str] | None = None) -> Path:
    """Choose the database path from CLI, environment, and default sources.

    The resolution order is:

    1. ``cli_arg`` if it is not ``None``;
    2. otherwise the value of the ``REQUIREMENTS_DB_PATH`` environment
       variable if it is set and non-empty;
    3. otherwise :data:`DEFAULT_DB_PATH`.

    The selected path is expanded so a leading ``~`` is replaced with the
    user's home directory, and then resolved to an absolute path. The
    file itself does not need to exist; this helper only computes a
    location and never touches the filesystem.

    Args:
        cli_arg: Optional path supplied on the command line. May be a
            string or any path-like object.

    Returns:
        An absolute :class:`pathlib.Path`. Suitable for passing to
        :func:`requirements_mcp.db.engine.make_engine` or for logging.
    """
    if cli_arg is not None:
        candidate = Path(cli_arg)
    elif env_value := os.environ.get(ENV_VAR):
        candidate = Path(env_value)
    else:
        candidate = DEFAULT_DB_PATH
    return candidate.expanduser().resolve()


__all__ = ["DEFAULT_DB_PATH", "ENV_VAR", "resolve_db_path"]
