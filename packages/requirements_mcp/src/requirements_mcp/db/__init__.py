"""Low-level database primitives: declarative base, engine, sessions, init.

This subpackage owns everything that touches SQLAlchemy directly. ORM
model modules import :data:`Base` from here; higher layers (services,
MCP tools, CLI) import :func:`init_db` and the engine and session
factories. Nothing outside this subpackage should construct an engine,
issue raw SQL, or call ``Base.metadata.create_all`` itself.

Public surface:
    - :class:`Base`: declarative base shared by every ORM model.
    - :func:`make_engine`: build a SQLite engine with foreign-key
      enforcement enabled.
    - :func:`make_session_factory`: build a ``sessionmaker`` bound to a
      given engine.
    - :func:`init_db`: idempotent schema creation and seed application.
"""

from requirements_mcp.db.base import Base
from requirements_mcp.db.engine import make_engine, make_session_factory
from requirements_mcp.db.init import init_db

__all__ = ["Base", "init_db", "make_engine", "make_session_factory"]
