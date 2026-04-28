"""Connection lifecycle: open/close DB files and apply schema migrations."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from loguru import logger

from . import schema
from ._logging import add_project_log_sink


def get_db(path: str) -> sqlite3.Connection:
    """Open (or create) a SQLite database and load ``sqlite-vec``.

    The connection is configured with WAL journaling, FK enforcement,
    and ``Row`` factory before bootstrap runs.

    Args:
        path: Filesystem path to the SQLite file. Parent directories are
            created if missing.

    Returns:
        An open :class:`sqlite3.Connection`. Caller owns the lifetime.

    Raises:
        RuntimeError: If the ``sqlite-vec`` extension cannot be loaded.
    """
    db_file = Path(path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    add_project_log_sink(db_file.parent)
    logger.debug("Opening DB at {}", path)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        import sqlite_vec

        sqlite_vec.load(conn)

    except Exception as e:  # noqa: BLE001 — surface as RuntimeError
        logger.error("sqlite-vec extension cannot be loaded")
        raise RuntimeError(f"Could not load sqlite-vec extension: {e}\n") from e

    bootstrap(conn)
    return conn


def bootstrap(conn: sqlite3.Connection) -> None:
    """Create tables and seed reference data if absent.

    Safe to call on an already-bootstrapped database. Also performs the
    one-shot ``ADD COLUMN slug`` migration for legacy DBs.

    Args:
        conn: An open SQLite connection with ``sqlite-vec`` loaded.
    """
    conn.executescript(schema.SCHEMA_SQL)
    conn.commit()
    schema.seed_reference_tables(conn)

    try:
        conn.execute("ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''")
        conn.commit()
        logger.info("Migrated existing DB: added 'slug' column to projects")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute(
            "ALTER TABLE projects ADD COLUMN singleton INTEGER NOT NULL "
            "DEFAULT 1 CHECK (singleton = 1)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_singleton "
            "ON projects(singleton)"
        )
        conn.commit()
        logger.info("Migrated existing DB: added single-project structural guard")
    except sqlite3.OperationalError:
        pass

    conn.execute("DROP TRIGGER IF EXISTS enforce_single_project")
    conn.commit()

    logger.debug("Bootstrap complete")
