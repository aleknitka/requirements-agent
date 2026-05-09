"""End-to-end database provisioning: create schema and apply seed data.

The :func:`init_db` helper is the single supported way to bring a fresh
database into a usable state. It resolves the target path, ensures the
parent directory exists, creates every ORM table, and upserts the
controlled-vocabulary seed rows in one transaction. Running it again
against an already-initialised database is safe: existing tables are
left in place and existing seed rows are skipped rather than
overwritten.
"""

from __future__ import annotations

import os
from pathlib import Path

from loguru import logger

from requirements_mcp.config import resolve_db_path
from requirements_mcp.db.base import Base
from requirements_mcp.db.engine import make_engine, make_session_factory

# Importing the models package registers every ORM class with
# ``Base.metadata`` so ``create_all`` can see all tables. The import is
# deliberate and must not be removed even though the name is unused.
from requirements_mcp import models  # noqa: F401  pylint: disable=unused-import
from requirements_mcp.seeds.apply import SeedReport, apply_seeds


def init_db(
    db_path: str | os.PathLike[str] | None = None,
    *,
    drop_first: bool = False,
) -> tuple[Path, SeedReport]:
    """Provision the SQLite database and seed controlled metadata.

    The function performs three steps in order:

    1. Resolve the target path. When ``db_path`` is ``None`` the fixed
       project location :func:`requirements_mcp.config.resolve_db_path`
       (``./data/requirements.db``) is used. The ``db_path`` keyword is
       a *programmatic* seam used by tests to redirect at a
       ``tmp_path``; it is not exposed through any user-facing CLI.
    2. Open a SQLAlchemy engine, optionally drop every table when
       ``drop_first`` is ``True``, and call ``Base.metadata.create_all``
       to ensure all ORM tables exist.
    3. Open a session, run :func:`requirements_mcp.seeds.apply.apply_seeds`
       to upsert every seed list, and commit.

    Each step emits a structured loguru message so that operators can
    follow database provisioning in development logs.

    Args:
        db_path: Optional override for tests. When ``None``, the locked
            project path returned by :func:`resolve_db_path` is used.
        drop_first: When ``True``, drop every table before recreating
            the schema. This destroys all stored data and exists to
            support the CLI's ``--reset`` flag and tests that need a
            clean slate. Defaults to ``False``.

    Returns:
        A two-tuple of ``(absolute_path, seed_report)`` where
        ``absolute_path`` is the resolved location of the database file
        and ``seed_report`` is a :class:`SeedReport` describing how many
        rows were inserted versus skipped per seed table.

    Raises:
        OSError: If the target directory does not exist and cannot be
            created (for example because of insufficient permissions).
    """
    resolved = (
        Path(db_path).expanduser().resolve()
        if db_path is not None
        else resolve_db_path()
    )
    logger.info("Initialising database at {}", resolved)
    resolved.parent.mkdir(parents=True, exist_ok=True)

    engine = make_engine(resolved)
    if drop_first:
        logger.warning("Dropping all tables at {}", resolved)
        Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)
    logger.debug("Schema ensured ({} tables)", len(Base.metadata.tables))

    session_factory = make_session_factory(engine)
    with session_factory() as session:
        report = apply_seeds(session)
        session.commit()

    inserted_total = sum(report.inserted.values())
    skipped_total = sum(report.skipped.values())
    logger.info(
        "Seeds applied: inserted={} skipped={} (per-table inserted={})",
        inserted_total,
        skipped_total,
        report.inserted,
    )
    return resolved, report


__all__ = ["init_db"]
