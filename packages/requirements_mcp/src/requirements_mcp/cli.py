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

from requirements_mcp.config import resolve_db_path
from requirements_mcp.db.engine import make_engine, make_session_factory
from requirements_mcp.db.init import init_db
from requirements_mcp.logging import configure_logging
from requirements_mcp.seeds.demo import apply_demo_data


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
            "Initialise the SQLite database at ./data/requirements.db. "
            "Creates the schema if it does not yet exist and upserts "
            "controlled-vocabulary metadata in a single, idempotent "
            "operation. The path is fixed; there is no --db flag."
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
        "--demo-data",
        dest="demo_data",
        action="store_true",
        help=(
            "After init/seed, populate the database with ~10 sample "
            "requirements and ~5 sample issues for demo / play. Skipped "
            "if any requirements already exist; combine with --reset "
            "--yes to start clean."
        ),
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
        user declined the confirmation prompt, or when ``--reset`` was
        requested in a non-interactive environment without ``--yes``.
    """
    args = _build_db_init_parser().parse_args(argv)
    configure_logging(name="requirements_mcp", level=args.log_level)

    if args.reset and not args.yes:
        if not sys.stdin.isatty():
            print(
                "Error: --reset requires --yes in non-interactive environments.",
                file=sys.stderr,
            )
            return 1
        resolved_path = resolve_db_path()
        confirmation = input(
            f"This will DROP all tables at {resolved_path}. Continue? [y/N] "
        )
        if confirmation.strip().lower() not in {"y", "yes"}:
            print("Aborted.", file=sys.stderr)
            return 1

    resolved, report = init_db(drop_first=args.reset)
    print(f"Database ready at: {resolved}")
    print(f"Seeds inserted: {report.inserted}")
    print(f"Seeds skipped:  {report.skipped}")

    if args.demo_data:
        engine = make_engine(resolved)
        session_factory = make_session_factory(engine)
        with session_factory() as session:
            demo_report = apply_demo_data(session)
            session.commit()
        if demo_report.skipped:
            print("Demo data: skipped (existing requirements found).")
        else:
            print(
                f"Demo data: {demo_report.requirements} requirements, "
                f"{demo_report.issues} issues, "
                f"{demo_report.links} links inserted."
            )

    return 0


__all__ = ["db_init"]
