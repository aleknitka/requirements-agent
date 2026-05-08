"""SQLAlchemy engine and session-factory helpers for SQLite.

SQLite does not enforce foreign-key constraints by default. Because the
schema relies on foreign keys to keep the audit trail consistent
(requirement-to-status, requirement-to-type, issue-to-priority, the
requirement-issue link table, and so on), an event listener is
attached to every new connection that issues
``PRAGMA foreign_keys=ON`` before any application SQL runs.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def _enable_sqlite_fk(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    """Enable SQLite foreign-key enforcement on a freshly opened connection.

    Bound to the engine's ``connect`` event in :func:`make_engine` so that
    every new DBAPI connection turns FK enforcement on before the
    application sees it. Without this hook SQLite would silently allow
    invalid references.

    Args:
        dbapi_connection: The raw DBAPI connection just opened by the
            pool. Provided positionally by the SQLAlchemy event system.
        connection_record: The pool's bookkeeping record for the
            connection. Unused but required by the event signature.
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def make_engine(db_path: Path | str, *, echo: bool = False) -> Engine:
    """Construct a SQLite-backed SQLAlchemy engine.

    The path is resolved to an absolute location before being inserted
    into the SQLite URL so that engines built from relative paths still
    refer to the same file regardless of the caller's working directory.
    Foreign-key enforcement is wired up via an event listener; callers
    do not need to issue any pragmas themselves.

    Args:
        db_path: Filesystem location of the SQLite database file. The
            parent directory must already exist; this helper does not
            create it (use :func:`requirements_mcp.db.init.init_db`
            for end-to-end provisioning that includes directory
            creation).
        echo: When ``True``, every emitted SQL statement is logged
            through SQLAlchemy's own logger. Useful for debugging and
            disabled by default to keep stdout free of query traffic.

    Returns:
        An :class:`sqlalchemy.Engine` ready to bind to sessions or pass
        to ``Base.metadata.create_all``.
    """
    abs_path = Path(db_path).resolve()
    engine = create_engine(
        f"sqlite:///{abs_path}",
        echo=echo,
        future=True,
    )
    event.listen(engine, "connect", _enable_sqlite_fk)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Build a ``sessionmaker`` bound to ``engine``.

    The returned factory creates sessions with ``expire_on_commit=False``
    so attribute access on persisted objects after a commit returns the
    in-memory state without triggering a SELECT. This makes
    request/response patterns simpler in service code and avoids
    surprising lazy-load roundtrips during tests.

    Args:
        engine: The engine returned by :func:`make_engine`.

    Returns:
        A :class:`sqlalchemy.orm.sessionmaker` configured for the 2.0
        ORM style, ready to use as a context manager via
        ``with factory() as session:``.
    """
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


__all__ = ["make_engine", "make_session_factory"]
