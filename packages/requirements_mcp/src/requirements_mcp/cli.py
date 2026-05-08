"""Command-line entry points exposed by the package.

Currently the only command is ``requirements-db-init``, which creates the
SQLite database file (if missing), applies the ORM schema, and seeds the
controlled-vocabulary tables idempotently. The CLI is the recommended
way to provision a development database before starting the MCP server
or the Gradio frontend.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from requirements_mcp.db.init import init_db
from requirements_mcp.logging import configure_logging


def _build_db_init_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the ``requirements-db-init`` command.

    Kept as a private helper so tests can import it directly to assert on
    the parser's options without invoking ``argparse``'s ``sys.exit``
    behaviour.

    Returns:
        A configured :class:`argparse.ArgumentParser` ready to call
        ``parse_args``.
    """
    parser = argparse.ArgumentParser(
        prog="requirements-db-init",
        description=(
            "Initialise the SQLite database used by the requirements MCP "
            "server. Creates the schema if it does not yet exist and "
            "upserts controlled-vocabulary metadata in a single, "
            "idempotent operation. Safe to re-run."
        ),
    )
    parser.add_argument(
        "--db",
        dest="db",
        default=None,
        help=(
            "Path to the SQLite database file. Overrides the "
            "REQUIREMENTS_DB_PATH environment variable. When neither is "
            "set, the default ./data/requirements.db is used."
        ),
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help=(
            "Drop every table before recreating the schema. This DELETES "
            "all stored requirements, issues, and audit history. Combine "
            "with --yes to bypass the interactive confirmation."
        ),
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation prompt for --reset.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help=(
            "Minimum loguru level for stdout and the daily log file. "
            "Defaults to INFO; pass DEBUG to see SQL-level detail."
        ),
    )
    return parser


def db_init(argv: Sequence[str] | None = None) -> int:
    """Run the ``requirements-db-init`` command.

    Configures logging, parses arguments, prompts for confirmation on
    destructive resets, calls :func:`requirements_mcp.db.init.init_db`,
    and prints a short summary of the resulting seed counts to standard
    output.

    Args:
        argv: Optional argument vector. When ``None``, ``sys.argv[1:]``
            is parsed automatically. Tests pass an explicit list to avoid
            depending on the real process argv.

    Returns:
        ``0`` on success. ``1`` when ``--reset`` was requested but the
        user declined the interactive confirmation prompt.
    """
    args = _build_db_init_parser().parse_args(argv)
    configure_logging(name="requirements_mcp", level=args.log_level)

    if args.reset and not args.yes:
        confirmation = input(
            f"This will DROP all tables at {args.db or '<default>'}. Continue? [y/N] "
        )
        if confirmation.strip().lower() not in {"y", "yes"}:
            print("Aborted.", file=sys.stderr)
            return 1

    resolved, report = init_db(db_path=args.db, drop_first=args.reset)
    print(f"Database ready at: {resolved}")
    print(f"Seeds inserted: {report.inserted}")
    print(f"Seeds skipped:  {report.skipped}")
    return 0


__all__ = ["db_init"]
