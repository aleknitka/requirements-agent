"""SQLAlchemy engine and session-factory helpers for SQLite.

Two SQLite-specific behaviours are configured on every new connection
via an event listener:

* ``PRAGMA foreign_keys=ON`` — SQLite does not enforce foreign-key
  constraints by default, but the schema relies on FKs to keep the
  audit trail consistent (requirement-to-status, requirement-to-type,
  issue-to-priority, the requirement-issue link table). Without this
  pragma, invalid references would be silently accepted.
* ``PRAGMA journal_mode=WAL`` — write-ahead logging permits concurrent
  readers while a writer is active, which matters once the MCP server
  and the Gradio frontend touch the database at the same time. WAL is
  a database-wide setting that persists in the file, but issuing the
  pragma per connection is harmless and ensures a freshly created
  database is upgraded immediately.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def _configure_sqlite_connection(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    """Apply SQLite per-connection pragmas required by the schema.

    Bound to the engine's ``connect`` event in :func:`make_engine` so the
    pragmas run before any application SQL on a freshly opened DBAPI
    connection. Two pragmas are issued: foreign-key enforcement (which
    SQLite leaves off by default) and WAL journalling (for concurrent
    reader/writer access from the MCP server and the Gradio frontend).

    Args:
        dbapi_connection: The raw DBAPI connection just opened by the
            pool. Provided positionally by the SQLAlchemy event system.
        connection_record: The pool's bookkeeping record for the
            connection. Unused but required by the event signature.
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
    finally:
        cursor.close()


def make_engine(db_path: Path | str, *, echo: bool = False) -> Engine:
    """Construct a SQLite-backed SQLAlchemy engine.

    The path is resolved to an absolute location before being inserted
    into the SQLite URL so that engines built from relative paths still
    refer to the same file regardless of the caller's working directory.
    Foreign-key enforcement and WAL journalling are wired up via an event
    listener; callers do not need to issue any pragmas themselves.

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
    event.listen(engine, "connect", _configure_sqlite_connection)
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
