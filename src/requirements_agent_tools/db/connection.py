"""Connection lifecycle: open/close DB files and apply schema migrations."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from loguru import logger

from . import schema
from ._logging import add_project_log_sink


def get_db(path: str, sqlite_vec_enabled: bool = False) -> sqlite3.Connection:
    """Open (or create) a SQLite database and optionally load sqlite-vec.

    The connection is configured with WAL journaling, FK enforcement,
    and Row factory before bootstrap runs.

    Args:
        path: Filesystem path to the SQLite file. Parent directories are
            created if missing.
        sqlite_vec_enabled: When True, loads the sqlite-vec extension and
            creates the vec0 virtual table. Read from config/project.yaml
            by callers that know the config; defaults to False.

    Returns:
        An open sqlite3.Connection. Caller owns the lifetime.

    Raises:
        RuntimeError: If sqlite_vec_enabled is True but the extension
            cannot be loaded.
    """
    db_file = Path(path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    add_project_log_sink(db_file.parent)
    logger.debug("Opening DB at {}", path)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    if sqlite_vec_enabled:
        try:
            import sqlite_vec

            sqlite_vec.load(conn)
        except Exception as e:  # noqa: BLE001 — surface as RuntimeError
            logger.error("sqlite-vec extension cannot be loaded")
            raise RuntimeError(f"Could not load sqlite-vec extension: {e}\n") from e

    bootstrap(conn, sqlite_vec_enabled=sqlite_vec_enabled)
    return conn


def bootstrap(conn: sqlite3.Connection, sqlite_vec_enabled: bool = False) -> None:
    """Create tables and seed reference data if absent.

    Safe to call on an already-bootstrapped database.

    Args:
        conn: An open SQLite connection.
        sqlite_vec_enabled: When True, also creates the vec0 virtual table.
    """
    conn.executescript(schema.BASE_SCHEMA_SQL)
    if sqlite_vec_enabled:
        conn.executescript(schema.VEC_SCHEMA_SQL)
    conn.commit()
    schema.seed_reference_tables(conn)
    logger.debug("Bootstrap complete")
