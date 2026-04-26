"""
project_session.py — shared helper for resolving the active project.

Every skill calls `resolve(slug_or_name)` at the start of its session.
Pass an explicit slug via --project <slug>. Auto-selection via .active
sentinel will be added in Phase 1 (INIT-06).

Usage
─────
    import project_session as ps

    slug, conn, meta = ps.resolve(args.project)   # args.project may be None
    # ... do work ...
    ps.refresh_md(slug, conn)                      # call after any write
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
import CONSTANTS as C
import db
import md_writer
from models import ProjectMeta


def resolve(slug_or_name: Optional[str] = None) -> tuple[str, sqlite3.Connection, ProjectMeta]:
    """
    Resolve which project to work on.
    Returns (slug, conn, meta).

    Phase 0: requires explicit slug_or_name. Auto-selection via .active sentinel
    is implemented in Phase 1 (INIT-06).
    """
    if not slug_or_name:
        _err(
            "No project selected. Pass --project <slug>.\n"
            "To list projects: python skills/new-project-initiation/scripts/init.py list\n"
            "(Auto-selection via .active sentinel will be added in Phase 1.)"
        )

    slug = slug_or_name
    conn = db.get_db(str(C.db_path(slug)))
    meta = db.get_project_by_slug(conn, slug)
    if not meta:
        _err(f"Project '{slug}' not found. Run project-init new --name '<name>' first.")
    return slug, conn, meta


def refresh_md(slug: str, conn: sqlite3.Connection) -> Path:
    """Recompute all stats and regenerate PROJECT.md. Call after every write."""
    meta  = db.get_project_by_slug(conn, slug)
    reqs  = db.search_requirements(conn, meta.project_id) if meta else []

    req_counts:    dict = {}
    status_counts: dict = {}
    for r in reqs:
        req_counts[r.req_type.value]  = req_counts.get(r.req_type.value, 0) + 1
        status_counts[r.status.value] = status_counts.get(r.status.value, 0) + 1

    with_fret = sum(1 for r in reqs if getattr(r, 'fret_statement', None))
    total     = len(reqs)
    fret_cov  = {"with_fret": with_fret, "total": total,
                 "pct": (with_fret / total * 100) if total else 0}

    all_decs   = db.list_decisions(conn, meta.project_id) if meta else []
    open_decs  = sum(1 for d in all_decs if d["status"] == "open")
    mins       = db.list_minutes(conn, meta.project_id) if meta else []
    pending_a  = sum(1 for m in mins for a in m.action_items if not a.done)
    unint      = sum(1 for m in mins if not m.integrated_into_status)

    return md_writer.regenerate(
        slug, meta, req_counts, status_counts,
        open_decs, pending_a, unint, fret_cov,
    )


def _err(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}, indent=2))
    sys.exit(1)
