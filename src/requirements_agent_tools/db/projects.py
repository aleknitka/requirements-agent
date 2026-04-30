"""Project CRUD. Each DB file holds exactly one project row."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from ..models import ProjectMeta
from . import _serialization as ser


def upsert_project(conn: sqlite3.Connection, meta: ProjectMeta) -> ProjectMeta:
    """Insert or update the single project row in this database.

    Bumps ``updated_at`` to now on every call.

    Args:
        conn: Open DB connection.
        meta: Project metadata. Mutated in place to reflect updated timestamp.

    Returns:
        The same ``meta`` instance with ``updated_at`` refreshed.

    Raises:
        sqlite3.IntegrityError: If a different project already exists in
            this DB (the ``singleton`` UNIQUE constraint blocks the insert).
    """
    meta.updated_at = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT INTO projects (
            project_id, name, code, phase, objective, business_case,
            success_criteria, out_of_scope, project_owner, sponsor,
            stakeholders, start_date, target_date, actual_end_date,
            external_links, status_summary, status_updated_at,
            created_at, updated_at
        ) VALUES (
            :project_id,:name,:code,:phase,:objective,:business_case,
            :success_criteria,:out_of_scope,:project_owner,:sponsor,
            :stakeholders,:start_date,:target_date,:actual_end_date,
            :external_links,:status_summary,:status_updated_at,
            :created_at,:updated_at
        )
        ON CONFLICT(project_id) DO UPDATE SET
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
    logger.info("Upserted project id={}", meta.project_id)
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


def list_projects(conn: sqlite3.Connection) -> list[ProjectMeta]:
    """Return every project row in this database, ordered by ``created_at``."""
    rows = conn.execute("SELECT * FROM projects ORDER BY created_at").fetchall()
    return [ser.row_to_project(r) for r in rows]
