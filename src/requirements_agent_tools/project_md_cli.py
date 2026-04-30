"""
project_md_cli.py — persist skill-authored PROJECT.md content with audit.

Commands
────────
  save     Write the full markdown body (creates or replaces the file)
  append   Append a section to the existing PROJECT.md
  read     Print the current PROJECT.md to stdout
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import project_md
from ._cli_io import err as _err
from ._cli_io import ok as _ok
from .project_session import get_project_conn


def _resolve_content(inline: str | None, file_path: str | None, label: str) -> str:
    """Resolve inline content or a file path to a string.

    Exactly one of inline or file_path must be provided; providing both
    or neither causes an error exit.

    Args:
        inline: Inline content string, or None.
        file_path: Path to a file to read, or None.
        label: CLI option name used in error messages (e.g. "content").

    Returns:
        The resolved content string.
    """
    if inline is not None and file_path is not None:
        _err(f"Pass either --{label} or --{label}-file, not both.")
    if file_path is not None:
        p = Path(file_path)
        if not p.exists():
            _err(f"File not found: {file_path}")
        return p.read_text(encoding="utf-8")
    if inline is not None:
        return inline
    _err(f"Provide --{label} or --{label}-file.")


def cmd_save(args: argparse.Namespace) -> None:
    """Write the full PROJECT.md content, creating or replacing the file.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    conn = get_project_conn()
    content = _resolve_content(args.content, args.content_file, "content")
    path = project_md.save(conn, content, changed_by=args.by, summary=args.summary)
    _ok({"path": str(path), "bytes": len(content.encode("utf-8"))})


def cmd_append(args: argparse.Namespace) -> None:
    """Append a markdown section to the existing PROJECT.md.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    conn = get_project_conn()
    section = _resolve_content(args.section, args.section_file, "section")
    try:
        path = project_md.append_section(
            conn, section, changed_by=args.by, summary=args.summary
        )
    except FileNotFoundError as e:
        _err(str(e))
    _ok(
        {
            "path": str(path),
            "appended_bytes": len(section.encode("utf-8")),
        }
    )


def cmd_read(args: argparse.Namespace) -> None:
    """Print the current PROJECT.md content to stdout.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    body = project_md.read()
    if body is None:
        _err("PROJECT.md does not exist.")
    print(body, end="" if body.endswith("\n") else "\n")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the project-md-cli argument parser.

    Returns:
        Configured ArgumentParser with save, append, and read subcommands.
    """
    p = argparse.ArgumentParser(description="PROJECT.md persistence")
    sub = p.add_subparsers(dest="command", required=True)

    sv = sub.add_parser("save", help="Create or replace PROJECT.md")
    sv.add_argument("--by", required=True)
    sv.add_argument("--summary", required=True)
    sv.add_argument("--content", help="Inline markdown content")
    sv.add_argument(
        "--content-file", dest="content_file", help="Path to a markdown file"
    )

    ap = sub.add_parser("append", help="Append a section to PROJECT.md")
    ap.add_argument("--by", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--section", help="Inline section markdown")
    ap.add_argument(
        "--section-file", dest="section_file", help="Path to a section file"
    )

    sub.add_parser("read", help="Print the current PROJECT.md")

    return p


def main() -> None:
    """Entry point for the project_md_cli CLI."""
    args = build_parser().parse_args()
    {"save": cmd_save, "append": cmd_append, "read": cmd_read}[args.command](args)


if __name__ == "__main__":
    main()
