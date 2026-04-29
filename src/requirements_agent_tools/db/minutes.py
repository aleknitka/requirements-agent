"""Meeting minutes, decisions, and action items."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any, Optional

from loguru import logger

from ..models import MinuteIn, MinuteRow
from . import _serialization as ser


def insert_minute(conn: sqlite3.Connection, minute_in: MinuteIn) -> MinuteRow:
    """Insert one meeting record.

    Args:
        conn: Open DB connection.
        minute_in: Validated meeting input.

    Returns:
        The reloaded :class:`MinuteRow` with its assigned id.
    """
    now = ser.now_iso()
    mid = f"MTG-{str(uuid.uuid4())[:8].upper()}"
    conn.execute(
        """
        INSERT INTO minutes VALUES (
            :id,:title,:source,:source_url,
            :occurred_at,:logged_at,:logged_by,:attendees,
            :summary,:raw_notes,:decisions,:action_items,0,NULL
        )
        """,
        {
            "id": mid,
            "title": minute_in.title,
            "source": minute_in.source.value,
            "source_url": minute_in.source_url,
            "occurred_at": minute_in.occurred_at.isoformat(),
            "logged_at": now,
            "logged_by": minute_in.logged_by,
            "attendees": ser.to_json(minute_in.attendees),
            "summary": minute_in.summary,
            "raw_notes": minute_in.raw_notes,
            "decisions": ser.to_json(minute_in.decisions),
            "action_items": ser.to_json(minute_in.action_items),
        },
    )
    conn.commit()
    logger.info(
        "Inserted meeting {} ({} decisions, {} actions)",
        mid,
        len(minute_in.decisions),
        len(minute_in.action_items),
    )
    return get_minute(conn, mid)  # type: ignore[return-value]


def get_minute(conn: sqlite3.Connection, minute_id: str) -> Optional[MinuteRow]:
    """Return one meeting by id, or ``None`` if missing."""
    row = conn.execute("SELECT * FROM minutes WHERE id = ?", (minute_id,)).fetchone()
    return ser.row_to_minute(row) if row else None


def list_minutes(
    conn: sqlite3.Connection,
    source: Optional[str] = None,
    unintegrated: bool = False,
    since: Optional[str] = None,
) -> list[MinuteRow]:
    """List meetings ordered by ``occurred_at`` ascending.

    Args:
        conn: Open DB connection.
        source: Filter by meeting source enum value.
        unintegrated: If ``True``, only meetings whose decisions/actions
            have not yet been integrated into the project status.
        since: ISO date/datetime string. Only meetings on/after this
            instant are returned.

    Returns:
        A list of :class:`MinuteRow`.
    """
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if source:
        clauses.append("source = :source")
        params["source"] = source
    if unintegrated:
        clauses.append("integrated_into_status = 0")
    if since:
        clauses.append("occurred_at >= :since")
        params["since"] = since
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM minutes{where} ORDER BY occurred_at",  # nosec B608 — where clause built from hardcoded column filter constants; values are parameterized
        params,
    ).fetchall()
    return [ser.row_to_minute(r) for r in rows]


def mark_integrated(conn: sqlite3.Connection, minute_id: str) -> MinuteRow:
    """Flag a meeting as integrated into the project status.

    Args:
        conn: Open DB connection.
        minute_id: Meeting identifier.

    Returns:
        The reloaded :class:`MinuteRow`.
    """
    now = ser.now_iso()
    conn.execute(
        "UPDATE minutes SET integrated_into_status = 1, integrated_at = ? WHERE id = ?",
        (now, minute_id),
    )
    conn.commit()
    logger.info("Marked meeting {} as integrated", minute_id)
    return get_minute(conn, minute_id)  # type: ignore[return-value]


def list_decisions(
    conn: sqlite3.Connection,
    status: Optional[str] = None,
    affects_req: Optional[str] = None,
) -> list[dict]:
    """Return a flat list of decisions across every meeting.

    Args:
        conn: Open DB connection.
        status: Optional decision-status enum value to filter on.
        affects_req: Optional requirement id; only decisions whose
            ``affects_reqs`` list contains this id are returned.

    Returns:
        A list of dicts with the decision fields plus ``meeting_id`` and
        ``meeting_title`` from the parent minute.
    """
    minutes = list_minutes(conn)
    out: list[dict] = []
    for m in minutes:
        for d in m.decisions:
            if status and d.status.value != status:
                continue
            if affects_req and affects_req not in d.affects_reqs:
                continue
            out.append(
                {
                    "meeting_id": m.id,
                    "meeting_title": m.title,
                    **d.model_dump(mode="json"),
                }
            )
    return out
