"""Shared pytest fixtures for the requirements_mcp test suite."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from loguru import logger
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from requirements_mcp.db.base import Base
from requirements_mcp.db.engine import make_engine, make_session_factory

# Importing models registers ORM classes against ``Base.metadata``.
from requirements_mcp import models  # noqa: F401


@pytest.fixture(autouse=True)
def _reset_logger() -> Iterator[None]:
    """Remove all loguru handlers after each test to prevent state leakage."""
    yield
    logger.remove()


@pytest.fixture()
def temp_db_path(tmp_path: Path) -> Path:
    """Return an unused SQLite path inside the per-test temporary directory."""
    return tmp_path / "requirements.db"


@pytest.fixture()
def empty_engine(temp_db_path: Path) -> Iterator[Engine]:
    """Yield an engine bound to a fresh database with the schema created.

    No seed rows are applied. Use this fixture for tests that exercise the
    schema directly.
    """
    engine = make_engine(temp_db_path)
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(empty_engine: Engine) -> Iterator[Session]:
    """Yield a SQLAlchemy session bound to a fresh, empty schema."""
    factory = make_session_factory(empty_engine)
    with factory() as session:
        yield session
