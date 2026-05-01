"""Issue CRUD and linking.

Issues can be linked to multiple requirements and multiple update records
to track regressions, bugs, or concerns arising from specific changes.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from loguru import logger

from ..models import (
    IssueActionIn,
    IssueActionRow,
    IssueIn,
    IssuePriority,
    IssueRow,
    IssueStatus,
    UpdateRecord,
)
from .updates import write_update


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

    write_update(
        conn,
        UpdateRecord(
            entity_type="issue",
            entity_id=issue_id,
            changed_by=created_by,
            summary="Issue created.",
            diffs=[],
            full_snapshot=None,
        ),
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


def get_issue_full(conn: sqlite3.Connection, issue_id: str) -> Optional[dict]:
    """Return one issue with all its linked data, including updates.

    Returns a dict with IssueRow model dump plus 'updates' list.
    """
    from .updates import _row_to_record

    row = get_issue(conn, issue_id)
    if not row:
        return None

    # Fetch full update records
    updates = []
    if row.update_ids:
        placeholders = ", ".join("?" for _ in row.update_ids)
        upd_rows = conn.execute(
            f"SELECT * FROM updates WHERE id IN ({placeholders})",  # nosec B608
            row.update_ids,
        ).fetchall()
        updates = [_row_to_record(dict(r)).model_dump(mode="json") for r in upd_rows]

    # Fetch actions
    actions = [a.model_dump(mode="json") for a in list_issue_actions(conn, issue_id)]

    res = row.model_dump(mode="json")
    res["updates"] = updates
    res["actions"] = actions
    return res


def search_issues(
    conn: sqlite3.Connection,
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    owner: Optional[str] = None,
    requirement_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    updated_since: Optional[datetime] = None,
    updated_until: Optional[datetime] = None,
    sort_by: str = "created_at",
    desc: bool = True,
    **extra_filters: Any,
) -> list[IssueRow]:
    """Search issues with comprehensive filters and sorting.

    Args:
        conn: Open DB connection.
        status: Filter by status value.
        priority: Filter by priority value.
        owner: Filter by owner identifier.
        requirement_id: Filter by linked requirement.
        since: Created at or after this date.
        until: Created at or before this date.
        updated_since: Updated at or after this date.
        updated_until: Updated at or before this date.
        sort_by: Column to sort by (created_at, updated_at, status, priority).
        desc: Sort descending if True.
        **extra_filters: Key-value pairs for exact matches on other columns.

    Returns:
        List of matching IssueRow instances.
    """
    clauses = ["1=1"]
    params: dict[str, Any] = {}

    if status:
        clauses.append("status = :status")
        params["status"] = status
    if priority:
        clauses.append("priority = :priority")
        params["priority"] = priority
    if owner:
        clauses.append("owner = :owner")
        params["owner"] = owner

    if requirement_id:
        clauses.append(
            "id IN (SELECT issue_id FROM issue_requirements WHERE requirement_id = :req_id)"
        )
        params["req_id"] = requirement_id

    if since:
        clauses.append("created_at >= :since")
        params["since"] = since.isoformat()
    if until:
        clauses.append("created_at <= :until")
        params["until"] = until.isoformat()
    if updated_since:
        clauses.append("updated_at >= :upd_since")
        params["upd_since"] = updated_since.isoformat()
    if updated_until:
        clauses.append("updated_at <= :upd_until")
        params["upd_until"] = updated_until.isoformat()

    # Allowed columns for dynamic filtering
    ALLOWED_COLS = {"title", "description"}
    for k, v in extra_filters.items():
        if k in ALLOWED_COLS:
            clauses.append(f"{k} = :{k}")
            params[k] = v

    order = "DESC" if desc else "ASC"
    # Whitelist sort_by to prevent injection
    SAFE_SORT = {"created_at", "updated_at", "status", "priority", "title"}
    sort_col = sort_by if sort_by in SAFE_SORT else "created_at"

    sql = f"SELECT id FROM issues WHERE {' AND '.join(clauses)} ORDER BY {sort_col} {order}"  # nosec B608
    rows = conn.execute(sql, params).fetchall()
    results = []
    for r in rows:
        obj = get_issue(conn, r["id"])
        if obj:
            results.append(obj)
    return results


def fts_search_issues(
    conn: sqlite3.Connection,
    query: str,
) -> list[IssueRow]:
    """Search issues using FTS5 across records, updates, and actions.

    Args:
        conn: Open DB connection.
        query: FTS5 query string.

    Returns:
        List of matching IssueRow instances.
    """
    sql = """
        SELECT id FROM fts_issues WHERE fts_issues MATCH :query
        UNION
        SELECT entity_id FROM fts_updates
        WHERE entity_type = 'issue' AND fts_updates MATCH :query
        UNION
        SELECT issue_id FROM fts_issue_actions
        WHERE fts_issue_actions MATCH :query
    """
    rows = conn.execute(sql, {"query": query}).fetchall()
    # IDs are in the first column regardless of the select source in UNION
    ids = [r[0] for r in rows]

    results = []
    for issue_id in ids:
        obj = get_issue(conn, issue_id)
        if obj:
            results.append(obj)
    return results


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
    return search_issue_actions(conn, issue_id=issue_id)


def search_issue_actions(
    conn: sqlite3.Connection,
    *,
    issue_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    keyword: Optional[str] = None,
    sort_by: str = "occurred_at",
    desc: bool = True,
) -> list[IssueActionRow]:
    """Search issue actions with comprehensive filters.

    Args:
        conn: Open DB connection.
        issue_id: Filter by parent issue.
        since: Occurred at/after (datetime).
        until: Occurred before/at (datetime).
        keyword: Substring match on description.
        sort_by: Column to sort by (occurred_at).
        desc: Sort descending if True.

    Returns:
        List of matching IssueActionRow instances.
    """
    clauses = ["1=1"]
    params: dict[str, Any] = {}

    if issue_id:
        clauses.append("issue_id = :issue_id")
        params["issue_id"] = issue_id
    if since:
        clauses.append("occurred_at >= :since")
        params["since"] = since.isoformat()
    if until:
        clauses.append("occurred_at <= :until")
        params["until"] = until.isoformat()
    if keyword:
        clauses.append("description LIKE :kw")
        params["kw"] = f"%{keyword}%"

    order = "DESC" if desc else "ASC"
    SAFE_SORT = {"occurred_at", "issue_id"}
    sort_col = sort_by if sort_by in SAFE_SORT else "occurred_at"

    sql = f"SELECT * FROM issue_actions_log WHERE {' AND '.join(clauses)} ORDER BY {sort_col} {order}"  # nosec B608
    rows = conn.execute(sql, params).fetchall()
    return [
        IssueActionRow(
            id=r["id"],
            issue_id=r["issue_id"],
            occurred_at=datetime.fromisoformat(r["occurred_at"]),
            description=r["description"],
        )
        for r in rows
    ]
