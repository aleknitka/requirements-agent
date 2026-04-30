"""Requirement CRUD and search."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Any, Optional

from loguru import logger

from .. import CONSTANTS as C
from ..models import (
    FieldDiff,
    RequirementIn,
    RequirementPriority,
    RequirementRow,
    RequirementStatus,
    RequirementType,
    UpdateRecord,
)
from . import _serialization as ser
from .updates import write_update


def _make_req_id(req_type: RequirementType) -> str:
    """Return a fresh requirement id like ``REQ-FUN-1A2B3C4D``."""
    return f"REQ-{req_type.value}-{str(uuid.uuid4())[:8].upper()}"


def insert_requirement(
    conn: sqlite3.Connection,
    req_in: RequirementIn,
    created_by: str,
) -> RequirementRow:
    """Insert a new requirement, log the creation, and embed it.

    Args:
        conn: Open DB connection.
        req_in: Validated requirement input.
        created_by: Identifier of the user/agent writing the row.

    Returns:
        The freshly-loaded :class:`RequirementRow`.
    """
    # Lazy import: embeddings imports requirements, so break the cycle here.
    from .embeddings import store_embedding

    now = ser.now_iso()
    req_id = _make_req_id(req_in.req_type)

    conn.execute(
        """
        INSERT INTO requirements VALUES (
            :id,:req_type,:title,:description,
            :status,:priority,:owner,:stakeholders,:predecessors,
            :dependencies,:external_links,:tags,:created_at,:updated_at
        )
        """,
        {
            "id": req_id,
            "req_type": req_in.req_type.value,
            "title": req_in.title,
            "description": req_in.description,
            "status": req_in.status.value,
            "priority": req_in.priority.value,
            "owner": req_in.owner,
            "stakeholders": ser.to_json(req_in.stakeholders),
            "predecessors": ser.to_json(req_in.predecessors),
            "dependencies": ser.to_json(req_in.dependencies),
            "external_links": ser.to_json(req_in.external_links),
            "tags": ser.to_json(req_in.tags),
            "created_at": now,
            "updated_at": now,
        },
    )

    write_update(
        conn,
        UpdateRecord(
            entity_type="requirement",
            entity_id=req_id,
            changed_by=created_by,
            summary="Requirement created.",
            diffs=[],
            full_snapshot=None,
        ),
    )
    store_embedding(conn, req_id, req_in.title, req_in.description)

    conn.commit()
    logger.info("Inserted requirement {} by {}", req_id, created_by)
    row = get_requirement(conn, req_id)
    if row is None:
        raise RuntimeError(f"Failed to retrieve requirement {req_id} after operation.")
    return row


_UPDATABLE_FIELDS: set[str] = {
    "req_type",
    "title",
    "description",
    "status",
    "priority",
    "owner",
    "stakeholders",
    "predecessors",
    "dependencies",
    "external_links",
    "tags",
}


_COL_TRANSFORMS: dict[str, tuple[str, Optional[Any]]] = {
    "req_type": ("req_type", lambda v: RequirementType(v).value),
    "title": ("title", None),
    "description": ("description", None),
    "status": ("status", lambda v: RequirementStatus(v).value),
    "priority": ("priority", lambda v: RequirementPriority(v).value),
    "owner": ("owner", None),
    "stakeholders": ("stakeholders", ser.to_json),
    "predecessors": ("predecessors", ser.to_json),
    "dependencies": ("dependencies", ser.to_json),
    "external_links": ("external_links", ser.to_json),
    "tags": ("tags", ser.to_json),
}


def update_requirement(
    conn: sqlite3.Connection,
    req_id: str,
    changes: dict[str, Any],
    changed_by: str,
    summary: str,
) -> RequirementRow:
    """Apply a partial update and append a change-log entry.

    Only fields listed in :data:`_UPDATABLE_FIELDS` are accepted. A full row
    snapshot is captured when the new ``status`` value is in
    :data:`CONSTANTS.SNAPSHOT_ON_STATUSES`.

    Args:
        conn: Open DB connection.
        req_id: Requirement identifier to update.
        changes: Mapping of field name to new value.
        changed_by: Author of the change.
        summary: Human-readable change summary.

    Returns:
        The reloaded :class:`RequirementRow`.

    Raises:
        KeyError: If ``req_id`` does not exist.
        ValueError: If ``changes`` includes non-updatable fields.
    """
    from .embeddings import store_embedding

    existing = get_requirement(conn, req_id)
    if not existing:
        raise KeyError(f"Requirement '{req_id}' not found.")

    bad = set(changes) - _UPDATABLE_FIELDS
    if bad:
        raise ValueError(f"Fields not updatable: {bad}")

    diffs: list[FieldDiff] = []
    current = existing.model_dump(mode="json")
    for field, new_val in changes.items():
        old_val = current.get(field)
        if old_val != new_val:
            diffs.append(FieldDiff(field=field, old_value=old_val, new_value=new_val))

    if not diffs:
        return existing

    full_snap = None
    if "status" in changes and changes["status"] in C.SNAPSHOT_ON_STATUSES:
        full_snap = current

    write_update(
        conn,
        UpdateRecord(
            entity_type="requirement",
            entity_id=req_id,
            changed_by=changed_by,
            summary=summary,
            diffs=diffs,
            full_snapshot=full_snap,
        ),
    )

    sets: list[str] = []
    params: dict[str, Any] = {}
    for field, new_val in changes.items():
        col, transform = _COL_TRANSFORMS[field]
        params[col] = transform(new_val) if transform else new_val
        sets.append(f"{col} = :{col}")

    params["updated_at"] = ser.now_iso()
    params["req_id"] = req_id
    sets.append("updated_at = :updated_at")

    conn.execute(
        f"UPDATE requirements SET {', '.join(sets)} WHERE id = :req_id",  # nosec B608 — sets list built from validated, hardcoded column names; values are parameterized
        params,
    )

    if "title" in changes or "description" in changes:
        new_title = changes.get("title", existing.title)
        new_desc = changes.get("description", existing.description)
        store_embedding(conn, req_id, new_title, new_desc)

    conn.commit()
    logger.info("Updated {} ({} field(s)) by {}", req_id, len(diffs), changed_by)
    for diff in diffs:
        logger.debug("  {} : {!r} -> {!r}", diff.field, diff.old_value, diff.new_value)
    row = get_requirement(conn, req_id)
    if row is None:
        raise RuntimeError(f"Failed to retrieve requirement {req_id} after operation.")
    return row


def get_requirement(conn: sqlite3.Connection, req_id: str) -> Optional[RequirementRow]:
    """Return one requirement by id, or ``None`` if missing.

    The result includes a ``has_embedding`` flag joined from
    ``req_embeddings``.
    """
    row = conn.execute(
        """
        SELECT r.*,
               CASE WHEN e.requirement_id IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
        FROM requirements r
        LEFT JOIN req_embeddings e ON e.requirement_id = r.id
        WHERE r.id = ?
        """,
        (req_id,),
    ).fetchone()
    return ser.row_to_requirement(row) if row else None


def search_requirements(
    conn: sqlite3.Connection,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    req_type: Optional[str] = None,
    owner: Optional[str] = None,
    tag: Optional[str] = None,
    keyword: Optional[str] = None,
) -> list[RequirementRow]:
    """Field-based search with optional substring match on title/description.

    Args:
        conn: Open DB connection.
        status: Filter by status enum value.
        priority: Filter by priority enum value.
        req_type: Filter by requirement-type code (case-insensitive).
        owner: Filter by exact owner name.
        tag: Filter rows whose JSON ``tags`` array contains this value.
        keyword: ``LIKE %keyword%`` match against title or description.

    Returns:
        A list of :class:`RequirementRow` ordered by ``created_at``.
    """
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if status:
        clauses.append("r.status = :status")
        params["status"] = status
    if priority:
        clauses.append("r.priority = :priority")
        params["priority"] = priority
    if req_type:
        clauses.append("r.req_type = :req_type")
        params["req_type"] = req_type.upper()
    if owner:
        clauses.append("r.owner = :owner")
        params["owner"] = owner
    if keyword:
        clauses.append("(r.title LIKE :kw OR r.description LIKE :kw)")
        params["kw"] = f"%{keyword}%"

    tag_join = ""
    if tag:
        tag_join = "JOIN json_each(r.tags) ON json_each.value = :tag"
        params["tag"] = tag

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        SELECT r.*,
               CASE WHEN e.requirement_id IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
        FROM requirements r
        LEFT JOIN req_embeddings e ON e.requirement_id = r.id
        {tag_join}
        {where}
        ORDER BY r.created_at
    """  # nosec B608 — tag_join and where built from hardcoded column/table names; values are parameterized
    rows = conn.execute(sql, params).fetchall()
    return [ser.row_to_requirement(r) for r in rows]


def get_requirement_by_title(
    conn: sqlite3.Connection, title: str
) -> Optional[RequirementRow]:
    """Return the requirement whose ``title`` matches exactly, or ``None``."""
    row = conn.execute(
        """
        SELECT r.*,
               CASE WHEN e.requirement_id IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
        FROM requirements r
        LEFT JOIN req_embeddings e ON e.requirement_id = r.id
        WHERE r.title = ?
        """,
        (title,),
    ).fetchone()
    return ser.row_to_requirement(row) if row else None


def find_requirements_updated_between(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
) -> list[RequirementRow]:
    """Return requirements whose ``updated_at`` falls within ``[start, end]``.

    Both bounds are inclusive. ISO-8601 string comparison on the stored
    timestamp column is correct because all timestamps are written via
    ``ser.now_iso`` in UTC.
    """
    rows = conn.execute(
        """
        SELECT r.*,
               CASE WHEN e.requirement_id IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
        FROM requirements r
        LEFT JOIN req_embeddings e ON e.requirement_id = r.id
        WHERE r.updated_at BETWEEN ? AND ?
        ORDER BY r.updated_at
        """,
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    return [ser.row_to_requirement(r) for r in rows]


def build_requirements_report(
    conn: sqlite3.Connection,
) -> list[dict]:
    """Return every requirement together with its full update history.

    Each entry has the shape ``{"requirement": RequirementRow,
    "updates": list[UpdateRecord]}``. Results are ordered by the
    requirement's ``created_at``.
    """
    from .updates import get_updates

    reqs = search_requirements(conn)
    return [{"requirement": r, "updates": get_updates(conn, r.id)} for r in reqs]
