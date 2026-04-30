"""Issue CRUD and linking.

Issues can be linked to multiple requirements and multiple update records
to track regressions, bugs, or concerns arising from specific changes.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from ..models import (
    IssueActionIn,
    IssueActionRow,
    IssueIn,
    IssuePriority,
    IssueRow,
    IssueStatus,
)


def insert_issue(
    conn: sqlite3.Connection,
    issue_in: IssueIn,
    *,
    created_by: str,
) -> IssueRow:
    """Insert a new issue and link it to requirements/updates.

    Args:
        conn: Open DB connection.
        issue_in: Validated issue data.
        created_by: Identifier of the person/agent creating the issue.

    Returns:
        The full IssueRow including generated ID and timestamps.
    """
    issue_id = f"ISS-{str(uuid.uuid4())[:8].upper()}"
    now = datetime.now(timezone.utc)

    conn.execute(
        """
        INSERT INTO issues (
            id, title, description, status, priority, owner, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            issue_id,
            issue_in.title,
            issue_in.description,
            issue_in.status.value,
            issue_in.priority.value,
            issue_in.owner,
            now.isoformat(),
            now.isoformat(),
        ),
    )

    # Link requirements
    for req_id in issue_in.requirement_ids:
        conn.execute(
            "INSERT INTO issue_requirements (issue_id, requirement_id) VALUES (?, ?)",
            (issue_id, req_id),
        )

    # Link updates
    for upd_id in issue_in.update_ids:
        conn.execute(
            "INSERT INTO issue_updates (issue_id, update_id) VALUES (?, ?)",
            (issue_id, upd_id),
        )

    conn.commit()
    logger.info("Inserted issue {} by {}", issue_id, created_by)

    row = get_issue(conn, issue_id)
    if row is None:
        raise RuntimeError(f"Failed to retrieve issue {issue_id} after insertion.")
    return row


def get_issue(conn: sqlite3.Connection, issue_id: str) -> Optional[IssueRow]:
    """Return one issue by id, or ``None`` if missing."""
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if not row:
        return None

    d = dict(row)
    # Fetch links
    req_ids = [
        r["requirement_id"]
        for r in conn.execute(
            "SELECT requirement_id FROM issue_requirements WHERE issue_id = ?",
            (issue_id,),
        ).fetchall()
    ]
    upd_ids = [
        r["update_id"]
        for r in conn.execute(
            "SELECT update_id FROM issue_updates WHERE issue_id = ?",
            (issue_id,),
        ).fetchall()
    ]

    return IssueRow(
        id=d["id"],
        title=d["title"],
        description=d["description"],
        status=IssueStatus(d["status"]),
        priority=IssuePriority(d["priority"]),
        owner=d["owner"],
        requirement_ids=req_ids,
        update_ids=upd_ids,
        created_at=datetime.fromisoformat(d["created_at"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
    )


def search_issues(
    conn: sqlite3.Connection,
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    owner: Optional[str] = None,
    requirement_id: Optional[str] = None,
) -> list[IssueRow]:
    """Search issues with optional filters."""
    query = "SELECT * FROM issues WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    if owner:
        query += " AND owner = ?"
        params.append(owner)

    if requirement_id:
        query += " AND id IN (SELECT issue_id FROM issue_requirements WHERE requirement_id = ?)"
        params.append(requirement_id)

    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    return [get_issue(conn, r["id"]) for r in rows]  # type: ignore[misc]


def update_issue(
    conn: sqlite3.Connection,
    issue_id: str,
    changes: dict,
    *,
    changed_by: str,
) -> IssueRow:
    """Apply partial updates to an issue."""
    allowed = {"title", "description", "status", "priority", "owner"}
    upd_fields = {k: v for k, v in changes.items() if k in allowed}

    if not upd_fields:
        return get_issue(conn, issue_id)  # type: ignore[return-value]

    now = datetime.now(timezone.utc)
    upd_fields["updated_at"] = now.isoformat()

    cols = ", ".join(f"{k} = ?" for k in upd_fields.keys())
    conn.execute(
        f"UPDATE issues SET {cols} WHERE id = ?",  # nosec B608
        (*upd_fields.values(), issue_id),
    )

    # Handle links if provided
    if "requirement_ids" in changes:
        conn.execute("DELETE FROM issue_requirements WHERE issue_id = ?", (issue_id,))
        for rid in changes["requirement_ids"]:
            conn.execute(
                "INSERT INTO issue_requirements (issue_id, requirement_id) VALUES (?, ?)",
                (issue_id, rid),
            )

    if "update_ids" in changes:
        conn.execute("DELETE FROM issue_updates WHERE issue_id = ?", (issue_id,))
        for uid in changes["update_ids"]:
            conn.execute(
                "INSERT INTO issue_updates (issue_id, update_id) VALUES (?, ?)",
                (issue_id, uid),
            )

    conn.commit()
    logger.info("Updated issue {} by {}", issue_id, changed_by)

    row = get_issue(conn, issue_id)
    if row is None:
        raise RuntimeError(f"Failed to retrieve issue {issue_id} after update.")
    return row


# ── Issue Actions ─────────────────────────────────────────────────────────────


def log_issue_action(
    conn: sqlite3.Connection,
    action_in: IssueActionIn,
) -> IssueActionRow:
    """Record an action taken for an issue.

    Args:
        conn: Open DB connection.
        action_in: Action details.

    Returns:
        The full IssueActionRow.
    """
    action_id = f"ACT-{str(uuid.uuid4())[:8].upper()}"
    now = datetime.now(timezone.utc)

    conn.execute(
        """
        INSERT INTO issue_actions_log (id, issue_id, occurred_at, description)
        VALUES (?, ?, ?, ?)
        """,
        (action_id, action_in.issue_id, now.isoformat(), action_in.description),
    )
    conn.commit()
    logger.info("Logged action {} for issue {}", action_id, action_in.issue_id)

    row = get_issue_action(conn, action_id)
    if row is None:
        raise RuntimeError(
            f"Failed to retrieve issue action {action_id} after logging."
        )
    return row


def get_issue_action(
    conn: sqlite3.Connection, action_id: str
) -> Optional[IssueActionRow]:
    """Return one issue action by id."""
    row = conn.execute(
        "SELECT * FROM issue_actions_log WHERE id = ?", (action_id,)
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    return IssueActionRow(
        id=d["id"],
        issue_id=d["issue_id"],
        occurred_at=datetime.fromisoformat(d["occurred_at"]),
        description=d["description"],
    )


def list_issue_actions(conn: sqlite3.Connection, issue_id: str) -> list[IssueActionRow]:
    """Return all actions for a given issue, newest first."""
    rows = conn.execute(
        "SELECT * FROM issue_actions_log WHERE issue_id = ? ORDER BY occurred_at DESC",
        (issue_id,),
    ).fetchall()
    return [
        IssueActionRow(
            id=r["id"],
            issue_id=r["issue_id"],
            occurred_at=datetime.fromisoformat(r["occurred_at"]),
            description=r["description"],
        )
        for r in rows
    ]
