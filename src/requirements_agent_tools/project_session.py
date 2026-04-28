"""
project_session.py — shared helper for resolving the active project.

Every skill calls `resolve(slug_or_name)` at the start of its session.
Pass an explicit slug via --project <slug>. Auto-selection via .active
sentinel will be added in Phase 1 (INIT-06).

PROJECT.md is owned by the skill: write through ``project_md_cli`` (or call
``project_md.save`` / ``append_section`` directly). There is no auto-refresh.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from . import CONSTANTS as C
from ._cli_io import err as _err
from .db.connection import get_db
from .db.projects import get_project
from .models import ProjectMeta


def resolve(
    slug_or_name: Optional[str] = None,
) -> tuple[str, sqlite3.Connection, ProjectMeta]:
    """
    Resolve which project to work on.
    Returns (slug, conn, meta).

    Phase 0: requires explicit slug_or_name. Auto-selection via .active sentinel
    is implemented in Phase 1 (INIT-06).
    """
    if not slug_or_name:
        _err(
            "No project selected. Pass --project <slug>.\n"
            "To list projects: python -m requirements_agent_tools.init_project list\n"
            "(Auto-selection via .active sentinel will be added in Phase 1.)"
        )

    slug = slug_or_name
    conn = get_db(str(C.db_path(slug)))
    meta = get_project(conn)
    if not meta:
        _err(f"Project '{slug}' not found. Run project-init new --name '<name>' first.")
    return slug, conn, meta
