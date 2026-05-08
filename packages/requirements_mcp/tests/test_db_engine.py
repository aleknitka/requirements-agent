"""Tests for ``requirements_mcp.db.engine``."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from requirements_mcp.db.engine import make_engine, make_session_factory


def test_make_engine_enables_sqlite_foreign_keys(tmp_path: Path) -> None:
    engine = make_engine(tmp_path / "fk.db")

    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys")).scalar_one()

    assert result == 1


def test_session_factory_yields_usable_session(tmp_path: Path) -> None:
    engine = make_engine(tmp_path / "sess.db")
    factory = make_session_factory(engine)

    with factory() as session:
        value = session.execute(text("SELECT 42")).scalar_one()

    assert value == 42
