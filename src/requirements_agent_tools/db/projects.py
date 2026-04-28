"""Project CRUD. Each DB file holds exactly one project row."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from .. import CONSTANTS as C
from ..models import ProjectMeta
from . import _serialization as ser


def upsert_project(conn: sqlite3.Connection, meta: ProjectMeta) -> ProjectMeta:
    """Insert or update the single project row in this database.

    Auto-derives ``meta.slug`` from ``meta.name`` when empty, and bumps
    ``updated_at`` to *now*.

    Args:
        conn: Open DB connection.
        meta: Project metadata. Mutated in place to reflect derived slug
            and updated timestamp.

    Returns:
        The same ``meta`` instance with derived fields filled in.

    Raises:
        sqlite3.IntegrityError: If a different project already exists in
            this DB (the ``singleton`` UNIQUE constraint blocks the insert).
    """
    if not meta.slug:
        meta.slug = C.slugify(meta.name)

    meta.updated_at = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT INTO projects (
            project_id, slug, name, code, phase, objective, business_case,
            success_criteria, out_of_scope, project_owner, sponsor,
            stakeholders, start_date, target_date, actual_end_date,
            external_links, status_summary, status_updated_at,
            created_at, updated_at
        ) VALUES (
            :project_id,:slug,:name,:code,:phase,:objective,:business_case,
            :success_criteria,:out_of_scope,:project_owner,:sponsor,
            :stakeholders,:start_date,:target_date,:actual_end_date,
            :external_links,:status_summary,:status_updated_at,
            :created_at,:updated_at
        )
        ON CONFLICT(project_id) DO UPDATE SET
            slug=excluded.slug,
            name=excluded.name, code=excluded.code, phase=excluded.phase,
            objective=excluded.objective, business_case=excluded.business_case,
            success_criteria=excluded.success_criteria,
            out_of_scope=excluded.out_of_scope,
            project_owner=excluded.project_owner, sponsor=excluded.sponsor,
            stakeholders=excluded.stakeholders,
            start_date=excluded.start_date, target_date=excluded.target_date,
            actual_end_date=excluded.actual_end_date,
            external_links=excluded.external_links,
            status_summary=excluded.status_summary,
            status_updated_at=excluded.status_updated_at,
            updated_at=excluded.updated_at
        """,
        {
            "project_id": meta.project_id,
            "slug": meta.slug,
            "name": meta.name,
            "code": meta.code,
            "phase": meta.phase.value,
            "objective": meta.objective,
            "business_case": meta.business_case,
            "success_criteria": ser.to_json(meta.success_criteria),
            "out_of_scope": ser.to_json(meta.out_of_scope),
            "project_owner": meta.project_owner,
            "sponsor": meta.sponsor,
            "stakeholders": ser.to_json(meta.stakeholders),
            "start_date": str(meta.start_date) if meta.start_date else None,
            "target_date": str(meta.target_date) if meta.target_date else None,
            "actual_end_date": str(meta.actual_end_date)
            if meta.actual_end_date
            else None,
            "external_links": ser.to_json(meta.external_links),
            "status_summary": meta.status_summary,
            "status_updated_at": (
                meta.status_updated_at.isoformat() if meta.status_updated_at else None
            ),
            "created_at": meta.created_at.isoformat(),
            "updated_at": meta.updated_at.isoformat(),
        },
    )
    conn.commit()
    logger.info("Upserted project id={} slug={}", meta.project_id, meta.slug)
    return meta


def get_project(conn: sqlite3.Connection) -> Optional[ProjectMeta]:
    """Return the single project stored in this database, or ``None``.

    Args:
        conn: Open DB connection.

    Returns:
        The project metadata, or ``None`` if no project has been inserted.
    """
    row = conn.execute("SELECT * FROM projects LIMIT 1").fetchone()
    return ser.row_to_project(row) if row else None


def get_project_by_slug(
    conn: sqlite3.Connection, slug: str
) -> Optional[ProjectMeta]:
    """Return the project with the matching slug in this database, or ``None``."""
    row = conn.execute(
        "SELECT * FROM projects WHERE slug = ? LIMIT 1", (slug,)
    ).fetchone()
    return ser.row_to_project(row) if row else None


def list_projects(conn: sqlite3.Connection) -> list[ProjectMeta]:
    """Return every project row in this database, ordered by ``created_at``."""
    rows = conn.execute("SELECT * FROM projects ORDER BY created_at").fetchall()
    return [ser.row_to_project(r) for r in rows]


def discover_projects() -> list[dict]:
    """Discover every project on disk by scanning ``PROJECTS_DIR``.

    Each project lives at ``PROJECTS_DIR/<slug>/<slug>.db``. Directories
    without a matching DB file (or whose DB has no project row) are skipped.

    Returns:
        A list of dicts with ``slug``, ``name``, ``code``, and ``phase``
        for every discoverable project, sorted by slug.
    """
    from .connection import get_db

    out: list[dict] = []
    if not C.PROJECTS_DIR.exists():
        return out
    for entry in sorted(C.PROJECTS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        db_file = entry / f"{entry.name}.db"
        if not db_file.exists():
            continue
        try:
            conn = get_db(str(db_file))
            meta = get_project(conn)
        except sqlite3.DatabaseError as e:
            logger.warning("Skipping {}: {}", db_file, e)
            continue
        if not meta:
            continue
        out.append(
            {
                "slug": meta.slug,
                "name": meta.name,
                "code": meta.code,
                "phase": meta.phase.value,
            }
        )
    return out
