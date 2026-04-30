"""
init_project.py — project initialisation.

Commands
--------
  setup    Create project/ directory tree, bootstrap DB, write config/project.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

import click
import yaml

from . import CONSTANTS as C
from ._cli_io import err as _err
from ._cli_io import ok as _ok
from .db.connection import get_db


def cmd_setup(args: argparse.Namespace) -> None:
    """Create the project directory, bootstrap the DB, and write setup config.

    Asks three interactive questions:
      1. Enable vector embeddings (sqlite-vec)?  [default: no]
      2. Enable OpenTelemetry tracing flag?       [default: no]
      3. Append project/logs/, project/notes/, project/*.db to .gitignore?

    Writes ``config/project.yaml`` with the setup choices. Creates the
    ``project/`` directory with ``logs/`` and ``notes/`` subdirectories.
    Bootstraps ``project/project.db`` with the canonical schema.

    Exits non-zero (code 1) if ``PROJECT_DIR`` already exists — use
    ``init-project reset`` (not yet implemented) to start fresh.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    # D-07: guard against second run
    if C.PROJECT_DIR.exists():
        _err("Project already initialised. Use 'init-project reset' to start fresh.")

    # D-08: interactive setup questions
    sqlite_vec: bool = click.confirm(
        "Enable vector embeddings (requires sqlite-vec)?", default=False
    )
    otel: bool = click.confirm(
        "Enable OpenTelemetry tracing (stores flag only)?", default=False
    )

    # D-08: .gitignore entries — individual confirm per entry
    gitignore_entries: list[str] = []
    for entry, description in [
        ("project/logs/", "project/logs/ (log files)"),
        ("project/notes/", "project/notes/ (notes directory)"),
        ("project/*.db", "project/*.db (database file)"),
    ]:
        if click.confirm(f"  Add {description} to .gitignore?", default=True):
            gitignore_entries.append(entry)

    # D-06: create directory tree — only cmd_setup() should mkdir
    C.PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    (C.PROJECT_DIR / "logs").mkdir(exist_ok=True)
    (C.PROJECT_DIR / "notes").mkdir(exist_ok=True)

    # D-06 + D-09/D-10: bootstrap DB (vec table created only when sqlite_vec=True)
    conn = get_db(str(C.DB_PATH), sqlite_vec_enabled=sqlite_vec)
    conn.close()

    # D-11: write config/project.yaml using yaml.safe_dump (never yaml.dump)
    config_path: Path = C._AGENT_ROOT / "config" / "project.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {"sqlite_vec": sqlite_vec, "otel_enabled": otel},
            f,
            default_flow_style=False,
        )

    # D-11: idempotent .gitignore append — only static known strings, never user input
    added_gitignore: list[str] = []
    if gitignore_entries:
        gitignore_path: Path = C._AGENT_ROOT / ".gitignore"
        existing: str = (
            gitignore_path.read_text(encoding="utf-8")
            if gitignore_path.exists()
            else ""
        )
        added_gitignore = [e for e in gitignore_entries if e not in existing]
        if added_gitignore:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# requirements-agent project\n")
                for entry in added_gitignore:
                    f.write(f"{entry}\n")

    _ok(
        {
            "project_dir": str(C.PROJECT_DIR),
            "db": str(C.DB_PATH),
            "config": str(config_path),
            "sqlite_vec": sqlite_vec,
            "otel_enabled": otel,
            "gitignore_entries_added": added_gitignore,
            "next_step": "Run 'uv run req-ops add' to add requirements.",
        }
    )


def build_parser() -> argparse.ArgumentParser:
    """Build and return the init-project argument parser.

    Returns:
        Configured ArgumentParser with the setup subcommand.
    """
    p = argparse.ArgumentParser(description="Project initialisation")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="Initialise the project directory and database")
    return p


def main() -> None:
    """Entry point for the init-project CLI."""
    args = build_parser().parse_args()
    {"setup": cmd_setup}[args.command](args)


if __name__ == "__main__":
    main()
