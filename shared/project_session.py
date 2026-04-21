"""
project_session.py — shared helper for resolving the active project.

Every skill calls `resolve(slug_or_name)` at the start of its session.
If exactly one project exists and no slug is given, it is selected automatically.
If multiple projects exist, the agent must ask the user which one to use.

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

    Rules:
    - If slug_or_name given: match exactly by slug or partial name.
    - If not given and exactly one project exists: use it silently.
    - If not given and multiple exist: print a selection list and exit with
      instructions for the caller to ask the user.
    """
    projects = db.list_all_projects()

    if not projects:
        _err(
            "No projects found. Run the project-init skill first:\n"
            "  python skills/project-init/scripts/init.py new"
        )

    if slug_or_name:
        matches = [
            p for p in projects
            if p["slug"] == slug_or_name
            or slug_or_name.lower() in p["name"].lower()
        ]
        if not matches:
            names = [f"  {p['slug']} — {p['name']}" for p in projects]
            _err(f"No project matching '{slug_or_name}'. Available:\n" + "\n".join(names))
        if len(matches) > 1:
            names = [f"  {p['slug']} — {p['name']}" for p in matches]
            _err(f"Ambiguous '{slug_or_name}'. Matches:\n" + "\n".join(names)
                 + "\nBe more specific with --project <slug>.")
        slug = matches[0]["slug"]
    elif len(projects) == 1:
        slug = projects[0]["slug"]
    else:
        # Multiple projects — must ask user
        listing = json.dumps({
            "ok": False,
            "error": "Multiple projects found. Pass --project <slug>.",
            "projects": projects,
        }, indent=2)
        print(listing)
        sys.exit(1)

    conn = db.get_db(slug)
    meta = db.get_project(conn)
    if not meta:
        _err(f"Project DB for '{slug}' exists but has no project row. Re-run project-init.")
    return slug, conn, meta


def refresh_md(slug: str, conn: sqlite3.Connection) -> Path:
    """Recompute all stats and regenerate PROJECT.md. Call after every write."""
    meta  = db.get_project(conn)
    reqs  = db.search_requirements(conn)

    req_counts:    dict = {}
    status_counts: dict = {}
    for r in reqs:
        req_counts[r.req_type.value]  = req_counts.get(r.req_type.value, 0) + 1
        status_counts[r.status.value] = status_counts.get(r.status.value, 0) + 1

    with_fret = sum(1 for r in reqs if r.fret_statement)
    total     = len(reqs)
    fret_cov  = {"with_fret": with_fret, "total": total,
                 "pct": (with_fret / total * 100) if total else 0}

    all_decs   = db.list_decisions(conn)
    open_decs  = sum(1 for d in all_decs if d["status"] == "open")
    mins       = db.list_minutes(conn)
    pending_a  = sum(1 for m in mins for a in m.action_items if not a.done)
    unint      = sum(1 for m in mins if not m.integrated_into_status)

    return md_writer.regenerate(
        slug, meta, req_counts, status_counts,
        open_decs, pending_a, unint, fret_cov,
    )


def _err(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}, indent=2))
    sys.exit(1)
    