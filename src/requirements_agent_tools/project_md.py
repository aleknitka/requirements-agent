"""Skill-owned PROJECT.md persistence with audit trail.

The skill drafts the markdown content and calls ``save()`` (full replace, also
the create path) or ``append_section()``. Every write records a row in the
``updates`` table with ``entity_type='project_md'`` and emits a loguru log
entry, so the change history is queryable both from the DB and the per-project
log file.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from loguru import logger

from . import CONSTANTS as C
from .db.projects import get_project
from .db.updates import write_update
from .models import FieldDiff, UpdateRecord


def save(
    conn: sqlite3.Connection,
    content: str,
    *,
    changed_by: str,
    summary: str,
) -> Path:
    """Write ``content`` as the full PROJECT.md body.

    Creates the file if it does not exist; otherwise overwrites it. In both
    cases an audit row is inserted in the same transaction as the file write.

    Args:
        conn: Open connection to the project's DB.
        content: The full markdown body to persist.
        changed_by: User or agent identifier for the audit row.
        summary: Human-readable description of the change.

    Returns:
        The path that was written.

    Raises:
        LookupError: If the project row is missing from the DB (the audit
            row's ``entity_id`` references the singleton project_id, which
            must exist).
    """
    meta = get_project(conn)
    if meta is None:
        raise LookupError("No project row in DB — initialise the project first.")

    path = C.MD_PATH
    previous = path.read_text(encoding="utf-8") if path.exists() else None

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    if previous is None:
        diffs: list[FieldDiff] = []
        log_msg = "Created PROJECT.md ({} chars) by {}"
        log_args = (len(content), changed_by)
    else:
        diffs = [FieldDiff(field="content", old_value=previous, new_value=content)]
        delta = len(content) - len(previous)
        log_msg = "Updated PROJECT.md ({:+} chars) by {}"
        log_args = (delta, changed_by)

    write_update(
        conn,
        UpdateRecord(
            entity_type="project_md",
            entity_id=meta.project_id,
            changed_by=changed_by,
            summary=summary,
            diffs=diffs,
            full_snapshot={"content": content},
        ),
    )
    conn.commit()
    logger.info(log_msg, *log_args)
    return path


def append_section(
    conn: sqlite3.Connection,
    section: str,
    *,
    changed_by: str,
    summary: str,
) -> Path:
    """Append ``section`` to the existing PROJECT.md, audit-logged.

    A blank line is inserted between the existing body and the new section.

    Args:
        conn: Open connection to the project's DB.
        section: Markdown text to append (no leading/trailing blank required).
        changed_by: Audit author.
        summary: Audit summary.

    Raises:
        FileNotFoundError: If PROJECT.md does not exist yet — call ``save``
            first.
        LookupError: If the project row is missing from the DB.
    """
    path = C.MD_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"PROJECT.md not found at {path} — call save() before append_section()."
        )
    meta = get_project(conn)
    if meta is None:
        raise LookupError("No project row in DB — initialise the project first.")

    existing = path.read_text(encoding="utf-8")
    addition = section if section.endswith("\n") else section + "\n"
    new_content = existing.rstrip("\n") + "\n\n" + addition
    path.write_text(new_content, encoding="utf-8")

    write_update(
        conn,
        UpdateRecord(
            entity_type="project_md",
            entity_id=meta.project_id,
            changed_by=changed_by,
            summary=summary,
            diffs=[
                FieldDiff(field="content_appended", old_value="", new_value=addition)
            ],
            full_snapshot={"content": new_content},
        ),
    )
    conn.commit()
    logger.info(
        "Appended section to PROJECT.md ({} chars) by {}",
        len(addition),
        changed_by,
    )
    return path


def read() -> Optional[str]:
    """Return the current PROJECT.md content, or ``None`` if it does not exist."""
    path = C.MD_PATH
    return path.read_text(encoding="utf-8") if path.exists() else None
