"""SQLite-backed persistence and audit layer for requirements management.

This package is the system of record for requirements, their change
history, issues, issue updates, and the link table that joins issues to
requirements. It owns the SQLAlchemy ORM models, Pydantic seed data for
controlled vocabularies, the idempotent database initialiser, and the
loguru-based logging configuration shared by the rest of the system.

External callers should treat this package as a sealed boundary: instead
of importing ORM classes or opening their own database connections, they
should drive all reads and writes through the higher-level service and
MCP tool layers built on top of it.

Public surface:
    - :func:`configure_logging`: attach stdout and daily-rotating file
      sinks to the shared loguru logger.
    - :func:`init_db`: create the schema and upsert controlled metadata
      idempotently.
    - :func:`resolve_db_path`: turn a CLI argument, environment variable,
      or default into an absolute database path.
"""

from requirements_mcp.config import resolve_db_path
from requirements_mcp.db.init import init_db
from requirements_mcp.logging import configure_logging

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "configure_logging",
    "init_db",
    "resolve_db_path",
]
