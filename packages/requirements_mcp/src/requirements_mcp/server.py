"""MCP server for the requirements MCP package.

Builds a :class:`FastMCP` server, registers the seven requirement tools
defined in :mod:`requirements_mcp.tools.requirements`, and exposes a
``main`` entry point that runs the server over the stdio transport.

The server takes its database location from the standard resolver (CLI
``--db`` argument, then ``REQUIREMENTS_DB_PATH`` environment variable,
then ``./data/requirements.db``). Logging is initialised on startup so
both stdout and the daily log file capture every tool call.
"""

from __future__ import annotations

import argparse
from typing import Sequence

from loguru import logger
from mcp.server.fastmcp import FastMCP

from requirements_mcp.config import resolve_db_path
from requirements_mcp.db.engine import make_engine, make_session_factory
from requirements_mcp.db.init import init_db
from requirements_mcp.logging import configure_logging
from requirements_mcp.schemas.requirements import (
    RequirementChangeOut,
    RequirementCreate,
    RequirementOut,
    RequirementSearchHit,
    RequirementSearchQuery,
    RequirementStatusOut,
    RequirementTypeOut,
    RequirementUpdate,
)
from requirements_mcp.tools import requirements as tools

__all__ = ["main", "make_server"]

SERVER_NAME = "requirements-mcp"

REGISTERED_TOOLS: tuple[str, ...] = (
    "create_requirement",
    "update_requirement",
    "get_requirement",
    "search_requirements",
    "list_requirement_changes",
    "list_requirement_statuses",
    "list_requirement_types",
)
"""Names of every MCP tool registered by :func:`make_server`.

Used by the smoke test to verify registration without depending on
``FastMCP`` internals.
"""


def make_server(session_factory) -> FastMCP:  # noqa: ANN001
    """Build the FastMCP server with all requirement tools registered.

    Each tool wraps the matching helper in
    :mod:`requirements_mcp.tools.requirements`, binding the supplied
    ``session_factory`` so handlers can open per-call sessions without
    leaking the factory through the public tool signature.

    Args:
        session_factory: A SQLAlchemy ``sessionmaker`` bound to the
            target database. Produced by
            :func:`requirements_mcp.db.engine.make_session_factory`.

    Returns:
        A configured :class:`FastMCP` instance ready to be started via
        ``await server.run_stdio_async()``.
    """
    server = FastMCP(SERVER_NAME)

    @server.tool(name="create_requirement")
    def _create_requirement(payload: RequirementCreate) -> RequirementOut:
        """Create a requirement and return its full state."""
        return tools.create_requirement(session_factory, payload)

    @server.tool(name="update_requirement")
    def _update_requirement(
        requirement_id: str, payload: RequirementUpdate
    ) -> RequirementOut:
        """Apply changes to a requirement; logs an audit row when fields change."""
        return tools.update_requirement(session_factory, requirement_id, payload)

    @server.tool(name="get_requirement")
    def _get_requirement(requirement_id: str) -> RequirementOut | None:
        """Return one requirement by id, or null if not found."""
        return tools.get_requirement(session_factory, requirement_id)

    @server.tool(name="search_requirements")
    def _search_requirements(
        query: RequirementSearchQuery,
    ) -> list[RequirementSearchHit]:
        """Search requirements by free text and optional code filters."""
        return tools.search_requirements(session_factory, query)

    @server.tool(name="list_requirement_changes")
    def _list_requirement_changes(
        requirement_id: str, limit: int = 100, offset: int = 0
    ) -> list[RequirementChangeOut]:
        """Return the audit log for one requirement, oldest first."""
        return tools.list_requirement_changes(
            session_factory, requirement_id, limit=limit, offset=offset
        )

    @server.tool(name="list_requirement_statuses")
    def _list_requirement_statuses() -> list[RequirementStatusOut]:
        """Return every requirement status ordered by sort_order."""
        return tools.list_requirement_statuses(session_factory)

    @server.tool(name="list_requirement_types")
    def _list_requirement_types() -> list[RequirementTypeOut]:
        """Return every requirement type ordered by sort_order."""
        return tools.list_requirement_types(session_factory)

    return server


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the ``requirements-mcp-server`` command.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="requirements-mcp-server",
        description=(
            "Run the requirements MCP server over stdio. Initialises the "
            "database if missing (idempotent) and exposes the requirement "
            "tools to MCP clients."
        ),
    )
    parser.add_argument(
        "--db",
        dest="db",
        default=None,
        help=(
            "Path to the SQLite database file. Overrides the "
            "REQUIREMENTS_DB_PATH environment variable. Default: "
            "./data/requirements.db."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Loguru level for stdout and the daily log file. Default: INFO.",
    )
    parser.add_argument(
        "--no-init",
        action="store_true",
        help=(
            "Skip the idempotent init_db call. Use when the database has "
            "already been provisioned by `requirements-db-init`."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``requirements-mcp-server`` console script.

    Steps performed at start-up:

    1. Parse arguments.
    2. Configure loguru with stdout + daily file sinks.
    3. Resolve the database path; run :func:`init_db` unless
       ``--no-init`` is passed.
    4. Build the engine + session factory.
    5. Construct the MCP server with all tools registered.
    6. Run the server on the stdio transport.

    Args:
        argv: Optional argument vector. ``None`` parses ``sys.argv[1:]``.

    Returns:
        ``0`` on a clean shutdown.
    """
    args = _build_parser().parse_args(argv)
    configure_logging(name="requirements_mcp", level=args.log_level)

    resolved = resolve_db_path(args.db)
    if args.no_init:
        logger.info("Skipping init_db (--no-init); using {}", resolved)
    else:
        init_db(resolved)

    engine = make_engine(resolved)
    session_factory = make_session_factory(engine)
    server = make_server(session_factory)
    logger.info("Starting {} over stdio (db={})", SERVER_NAME, resolved)
    server.run()
    return 0
