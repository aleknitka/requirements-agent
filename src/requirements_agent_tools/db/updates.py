"""Append-only change log for any auditable entity in the project DB.

Three entity kinds share this table:
  - ``requirement`` — entity_id is the requirement id (e.g. ``REQ-FUN-...``)
  - ``project``     — entity_id is the singleton project_id
  - ``issue``       — entity_id is the issue id
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Optional

from loguru import logger

from ..models import FieldDiff, UpdateRecord
from . import _serialization as ser


def write_update(conn: sqlite3.Connection, record: UpdateRecord) -> None:
    """Persist one :class:`UpdateRecord` to the ``updates`` table.

    The caller owns the transaction (no implicit ``commit()``).
    """
    conn.execute(
        """
        INSERT INTO updates(id, entity_type, entity_id, changed_at, changed_by,
                            summary, diffs, full_snapshot)
        VALUES (:id,:entity_type,:entity_id,:changed_at,:changed_by,
                :summary,:diffs,:full_snap)
        """,
        {
            "id": record.id,
            "entity_type": record.entity_type,
            "entity_id": record.entity_id,
            "changed_at": record.changed_at.isoformat(),
            "changed_by": record.changed_by,
            "summary": record.summary,
            "diffs": ser.to_json(record.diffs),
            "full_snap": json.dumps(record.full_snapshot)
            if record.full_snapshot
            else None,
        },
    )
    logger.debug(
        "Wrote update for {}:{} ({} diffs, snapshot={})",
        record.entity_type,
        record.entity_id,
        len(record.diffs),
        bool(record.full_snapshot),
    )


def get_updates(
    conn: sqlite3.Connection,
    entity_id: str,
    *,
    entity_type: str = "requirement",
) -> list[UpdateRecord]:
    """Return all change records for one entity, oldest first."""
    rows = conn.execute(
        """
        SELECT * FROM updates
        WHERE entity_type = ? AND entity_id = ?
        ORDER BY changed_at
        """,
        (entity_type, entity_id),
    ).fetchall()
    return [_row_to_record(dict(row)) for row in rows]


def search_updates(
    conn: sqlite3.Connection,
    *,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    changed_by: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    sort_by: str = "changed_at",
    desc: bool = True,
) -> list[UpdateRecord]:
    """Search the audit log with comprehensive filters.

    Args:
        conn: Open DB connection.
        entity_type: Filter by kind (requirement, project, issue).
        entity_id: Filter by specific entity identifier.
        changed_by: Filter by author.
        since: Changed at/after (datetime).
        until: Changed before/at (datetime).
        sort_by: Column to sort by (changed_at, changed_by).
        desc: Sort descending if True.

    Returns:
        List of matching UpdateRecord instances.
    """
    clauses = ["1=1"]
    params: dict[str, Any] = {}

    if entity_type:
        clauses.append("entity_type = :type")
        params["type"] = entity_type
    if entity_id:
        clauses.append("entity_id = :eid")
        params["eid"] = entity_id
    if changed_by:
        clauses.append("changed_by = :by")
        params["by"] = changed_by

    if since:
        clauses.append("changed_at >= :since")
        params["since"] = since.isoformat()
    if until:
        clauses.append("changed_at <= :until")
        params["until"] = until.isoformat()

    order = "DESC" if desc else "ASC"
    SAFE_SORT = {"changed_at", "changed_by", "entity_type"}
    sort_col = sort_by if sort_by in SAFE_SORT else "changed_at"

    sql = f"SELECT * FROM updates WHERE {' AND '.join(clauses)} ORDER BY {sort_col} {order}"  # nosec B608
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_record(dict(r)) for r in rows]


def _row_to_record(d: dict) -> UpdateRecord:
    """Deserialise a DB row dict into an UpdateRecord model instance.

    Args:
        d: Raw row dict from the updates table.

    Returns:
        Populated UpdateRecord with diffs and snapshot deserialised from JSON.
    """
    return UpdateRecord(
        id=d["id"],
        entity_type=d["entity_type"],
        entity_id=d["entity_id"],
        changed_at=datetime.fromisoformat(d["changed_at"]),
        changed_by=d["changed_by"],
        summary=d["summary"],
        diffs=[FieldDiff(**x) for x in json.loads(d["diffs"])],
        full_snapshot=json.loads(d["full_snapshot"]) if d["full_snapshot"] else None,
    )
