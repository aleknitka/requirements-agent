"""Append-only change log for any auditable entity in the project DB.

Two entity kinds share this table:
  - ``requirement`` — entity_id is the requirement id (e.g. ``REQ-FUN-...``)
  - ``project_md`` — entity_id is the singleton project_id; one row per
    PROJECT.md write or section append.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

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


def get_project_md_history(
    conn: sqlite3.Connection, project_id: str
) -> list[UpdateRecord]:
    """Return the full PROJECT.md change history for a project, oldest first."""
    return get_updates(conn, project_id, entity_type="project_md")


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
