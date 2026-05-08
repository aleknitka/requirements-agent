"""Service functions for the issue subsystem.

Each function takes an active SQLAlchemy :class:`Session` and does not
commit; the caller (the tool layer in :mod:`requirements_mcp.tools.issues`,
the Gradio app, or a test fixture) owns the transaction boundary. This
matches the pattern established for requirements in
:mod:`requirements_mcp.services.requirements`.

The hard invariant: every successful issue mutation produces a matching
row in ``issue_updates`` in the same transaction. ``create_issue``,
``update_issue``, ``add_issue_update``, ``link_issue_to_requirement``,
and ``unlink_issue_from_requirement`` all enforce this.

The Pydantic schema :class:`IssueUpdate` collides with the SQLAlchemy
ORM class of the same name, so this module imports the ORM class as
``IssueUpdateRow``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from loguru import logger
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from requirements_mcp.models import (
    Issue,
    IssuePriority,
    IssueStatus,
    IssueType,
    Requirement,
    RequirementIssueLink,
)
from requirements_mcp.models import IssueUpdate as IssueUpdateRow
from requirements_mcp.schemas.issues import (
    IssueCreate,
    IssueSearchQuery,
    IssueUpdate,
    IssueUpdateAdd,
    RequirementIssueLinkCreate,
)
from requirements_mcp.services.diff import ISSUE_DIFFABLE_FIELDS, compute_diff
from requirements_mcp.services.requirements import RequirementNotFoundError

__all__ = [
    "IssueNotFoundError",
    "RequirementIssueLinkAlreadyExistsError",
    "RequirementIssueLinkNotFoundError",
    "add_issue_update",
    "create_issue",
    "get_issue",
    "link_issue_to_requirement",
    "list_blocking_issues",
    "list_issue_priorities",
    "list_issue_statuses",
    "list_issue_types",
    "list_issue_updates",
    "list_open_issues",
    "search_issues",
    "unlink_issue_from_requirement",
    "update_issue",
]


class IssueNotFoundError(LookupError):
    """Raised when an operation references an issue id that does not exist."""


class RequirementIssueLinkNotFoundError(LookupError):
    """Raised when ``unlink_issue_from_requirement`` cannot find the link."""


class RequirementIssueLinkAlreadyExistsError(ValueError):
    """Raised when ``link_issue_to_requirement`` finds an existing link."""


_SEARCHABLE_TEXT_COLUMNS = (Issue.title, Issue.description)


def _now() -> datetime:
    """Return the current UTC time. Wrapped so tests can monkeypatch if needed."""
    return datetime.now(timezone.utc)


def _classify_update_type(diff_keys: set[str]) -> str:
    """Pick an ``update_type_code`` for an Issue update from the diff keys.

    Args:
        diff_keys: The set of field names that changed in this update.

    Returns:
        ``"status_changed"`` if only ``status_code`` changed,
        ``"priority_changed"`` if only ``priority_code`` changed, and
        ``"field_changed"`` for any other (possibly multi-field) change.
    """
    if diff_keys == {"status_code"}:
        return "status_changed"
    if diff_keys == {"priority_code"}:
        return "priority_changed"
    return "field_changed"


def create_issue(session: Session, payload: IssueCreate) -> Issue:
    """Insert a new issue and its initial audit-log row.

    The initial :class:`IssueUpdateRow` records the creation event with
    ``update_type_code="created"`` and ``diff={}``. Its ``author`` is
    taken from ``payload.created_by``. The id is assigned eagerly so the
    audit row can reference it without an early ``session.flush()``.

    Args:
        session: Active SQLAlchemy session. The caller commits.
        payload: Validated input model.

    Returns:
        The newly inserted (uncommitted) :class:`Issue` instance.
    """
    data = payload.model_dump()
    issue = Issue(id=str(uuid.uuid4()), **data)
    session.add(issue)
    session.add(
        IssueUpdateRow(
            issue_id=issue.id,
            update_type_code="created",
            description="created",
            diff={},
            action_taken="",
            action_result="",
            author=payload.created_by,
            date=_now(),
        )
    )
    logger.info(
        "Created issue {} (type={}, status={}, priority={})",
        issue.id,
        issue.issue_type_code,
        issue.status_code,
        issue.priority_code,
    )
    return issue


def update_issue(
    session: Session,
    issue_id: str,
    payload: IssueUpdate,
) -> Issue:
    """Apply an update and write the matching audit-log row.

    Steps:

    1. Load the issue; raise :class:`IssueNotFoundError` if absent.
    2. Filter the supplied fields to :data:`ISSUE_DIFFABLE_FIELDS`.
       ``owner`` is special-cased: an explicit ``None`` is a meaningful
       clear (the column is nullable). All other ``None`` values are
       filtered out so a caller cannot accidentally NULL a NOT NULL
       column.
    3. Compute the diff. If empty, return without writing anything.
    4. Apply the new values. If ``status_code`` changed, set or clear
       ``date_closed`` based on the new status's ``is_terminal`` flag.
       ``date_closed`` is **not** included in the audit diff.
    5. Insert an :class:`IssueUpdateRow` with the diff, the supplied
       ``change_description`` and ``author``, and an
       ``update_type_code`` derived from the diff keys.

    Args:
        session: Active SQLAlchemy session. The caller commits.
        issue_id: Primary key of the issue to mutate.
        payload: Validated update model.

    Returns:
        The mutated issue (or the unchanged one for a no-op).

    Raises:
        IssueNotFoundError: If ``issue_id`` does not exist.
    """
    issue = session.get(Issue, issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    submitted = payload.model_dump(exclude_unset=True)
    updates: dict[str, Any] = {}
    for field in ISSUE_DIFFABLE_FIELDS:
        if field not in submitted:
            continue
        value = submitted[field]
        # ``owner`` is the only nullable diffable column; passing None
        # there is a meaningful clear. For every other diffable column
        # None must be filtered out.
        if value is None and field != "owner":
            continue
        updates[field] = value

    diff = compute_diff(issue, updates, ISSUE_DIFFABLE_FIELDS)
    if not diff:
        logger.debug("No-op update on issue {} (no diffable fields changed)", issue.id)
        return issue

    for field, new_value in updates.items():
        setattr(issue, field, new_value)

    if "status_code" in diff:
        new_status = session.get(IssueStatus, issue.status_code)
        if new_status is not None:
            if new_status.is_terminal and issue.date_closed is None:
                issue.date_closed = _now()
            elif not new_status.is_terminal and issue.date_closed is not None:
                issue.date_closed = None

    update_type = _classify_update_type(set(diff))

    session.add(
        IssueUpdateRow(
            issue_id=issue.id,
            update_type_code=update_type,
            description=payload.change_description,
            diff=diff,
            action_taken="",
            action_result="",
            author=payload.author,
            date=_now(),
        )
    )
    logger.info(
        "Updated issue {} (kind={}, fields={}, status={})",
        issue.id,
        update_type,
        sorted(diff.keys()),
        issue.status_code,
    )
    return issue


def add_issue_update(
    session: Session,
    issue_id: str,
    payload: IssueUpdateAdd,
) -> IssueUpdateRow:
    """Append an action-log entry without changing Issue fields.

    Inserts an :class:`IssueUpdateRow` with empty ``diff`` and the
    user-supplied ``update_type_code``, ``description``,
    ``action_taken``, ``action_result``, and ``author``. Also bumps
    ``issue.date_updated`` so the parent row reflects the activity (the
    SQLAlchemy ``onupdate`` hook does not fire on child inserts).

    Args:
        session: Active SQLAlchemy session. The caller commits.
        issue_id: Primary key of the issue whose log to append.
        payload: Validated input.

    Returns:
        The newly inserted :class:`IssueUpdateRow`.

    Raises:
        IssueNotFoundError: If ``issue_id`` does not exist.
    """
    issue = session.get(Issue, issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    now = _now()
    row = IssueUpdateRow(
        issue_id=issue.id,
        update_type_code=payload.update_type_code,
        description=payload.description,
        diff={},
        action_taken=payload.action_taken,
        action_result=payload.action_result,
        author=payload.author,
        date=now,
    )
    session.add(row)
    issue.date_updated = now

    logger.info(
        "Appended issue update {} (kind={}, author={})",
        issue.id,
        payload.update_type_code,
        payload.author,
    )
    return row


def get_issue(session: Session, issue_id: str) -> Issue | None:
    """Return the issue with the given id, or ``None`` if missing.

    Args:
        session: Active SQLAlchemy session.
        issue_id: Primary key to look up.

    Returns:
        The :class:`Issue` row, or ``None`` if no row matches.
    """
    return session.get(Issue, issue_id)


def search_issues(
    session: Session,
    query: IssueSearchQuery,
) -> Sequence[Issue]:
    """Search issues by free text and optional code / owner filters.

    The free-text ``query`` is whitespace-tokenised. Every token must
    appear (case-insensitively, via SQL ``LIKE``) in either ``title``
    or ``description``. The remaining filters apply as documented on
    :class:`IssueSearchQuery`.

    Args:
        session: Active SQLAlchemy session.
        query: Validated search input.

    Returns:
        A sequence of matching :class:`Issue` rows ordered by
        ``date_updated`` descending.
    """
    stmt = select(Issue)

    for token in query.query.split():
        like = f"%{token}%"
        stmt = stmt.where(
            or_(*(column.ilike(like) for column in _SEARCHABLE_TEXT_COLUMNS))
        )

    if query.status_codes:
        stmt = stmt.where(Issue.status_code.in_(query.status_codes))
    if query.type_codes:
        stmt = stmt.where(Issue.issue_type_code.in_(query.type_codes))
    if query.priority_codes:
        stmt = stmt.where(Issue.priority_code.in_(query.priority_codes))
    if query.owner is not None:
        stmt = stmt.where(Issue.owner == query.owner)
    if query.created_by is not None:
        stmt = stmt.where(Issue.created_by == query.created_by)

    stmt = (
        stmt.order_by(Issue.date_updated.desc()).limit(query.limit).offset(query.offset)
    )

    rows = session.execute(stmt).scalars().all()
    logger.debug(
        "Searched issues: {} hits (query={!r}, statuses={}, types={}, "
        "priorities={}, owner={}, created_by={})",
        len(rows),
        query.query,
        query.status_codes,
        query.type_codes,
        query.priority_codes,
        query.owner,
        query.created_by,
    )
    return rows


def list_issue_updates(
    session: Session,
    issue_id: str,
    *,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[IssueUpdateRow]:
    """Return audit-log rows for one issue, oldest first.

    Args:
        session: Active SQLAlchemy session.
        issue_id: Primary key whose history is requested.
        limit: Maximum number of rows to return.
        offset: Number of rows to skip from the start.

    Returns:
        A sequence of :class:`IssueUpdateRow` rows ordered by ``date``
        ascending, with ``id`` as a secondary sort for stable
        pagination.

    Raises:
        IssueNotFoundError: If ``issue_id`` does not exist.
    """
    if session.get(Issue, issue_id) is None:
        raise IssueNotFoundError(issue_id)

    stmt = (
        select(IssueUpdateRow)
        .where(IssueUpdateRow.issue_id == issue_id)
        .order_by(IssueUpdateRow.date.asc(), IssueUpdateRow.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return session.execute(stmt).scalars().all()


def list_open_issues(session: Session) -> Sequence[Issue]:
    """Return every issue whose status is non-terminal.

    Joins :class:`IssueStatus` so the filter follows the seed data: as
    soon as a new status row is added with ``is_terminal=True``, this
    query reflects the change without code edits.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A sequence of open :class:`Issue` rows ordered by
        ``date_updated`` descending.
    """
    stmt = (
        select(Issue)
        .join(IssueStatus, IssueStatus.code == Issue.status_code)
        .where(IssueStatus.is_terminal.is_(False))
        .order_by(Issue.date_updated.desc())
    )
    return session.execute(stmt).scalars().all()


def list_blocking_issues(session: Session) -> Sequence[Issue]:
    """Return every non-terminal issue whose type is ``"BLK"``.

    A *blocking* issue is one classified as a blocker (issue type
    ``BLK``) and not yet in a terminal status. Ordering is by
    :class:`IssuePriority.severity_order` descending, then by
    ``date_updated`` descending so the most severe and most recent
    blockers surface first.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A sequence of blocking :class:`Issue` rows.
    """
    stmt = (
        select(Issue)
        .join(IssueStatus, IssueStatus.code == Issue.status_code)
        .join(IssuePriority, IssuePriority.code == Issue.priority_code)
        .where(Issue.issue_type_code == "BLK")
        .where(IssueStatus.is_terminal.is_(False))
        .order_by(
            IssuePriority.severity_order.desc(),
            Issue.date_updated.desc(),
        )
    )
    return session.execute(stmt).scalars().all()


def link_issue_to_requirement(
    session: Session,
    issue_id: str,
    payload: RequirementIssueLinkCreate,
) -> RequirementIssueLink:
    """Link an issue to a requirement and record the action.

    Args:
        session: Active SQLAlchemy session. The caller commits.
        issue_id: Primary key of the issue.
        payload: Validated link payload (carrying ``requirement_id``,
            ``link_type``, ``rationale``, ``author``).

    Returns:
        The newly inserted :class:`RequirementIssueLink` row.

    Raises:
        IssueNotFoundError: If ``issue_id`` does not exist.
        RequirementNotFoundError: If ``payload.requirement_id`` does
            not exist.
        RequirementIssueLinkAlreadyExistsError: If the link is already
            present.
    """
    if session.get(Issue, issue_id) is None:
        raise IssueNotFoundError(issue_id)
    if session.get(Requirement, payload.requirement_id) is None:
        raise RequirementNotFoundError(payload.requirement_id)

    existing = session.get(RequirementIssueLink, (payload.requirement_id, issue_id))
    if existing is not None:
        raise RequirementIssueLinkAlreadyExistsError(
            f"Link already exists between requirement={payload.requirement_id} "
            f"and issue={issue_id}"
        )

    link = RequirementIssueLink(
        requirement_id=payload.requirement_id,
        issue_id=issue_id,
        link_type=payload.link_type,
        rationale=payload.rationale,
        date_created=_now(),
    )
    session.add(link)

    description = (
        f"Linked to requirement {payload.requirement_id} as '{payload.link_type}'"
    )
    if payload.rationale:
        description = f"{description}: {payload.rationale}"
    session.add(
        IssueUpdateRow(
            issue_id=issue_id,
            update_type_code="requirement_linked",
            description=description,
            diff={},
            action_taken="",
            action_result="",
            author=payload.author,
            date=_now(),
        )
    )

    logger.info(
        "Linked issue {} to requirement {} (type={})",
        issue_id,
        payload.requirement_id,
        payload.link_type,
    )
    return link


def unlink_issue_from_requirement(
    session: Session,
    issue_id: str,
    requirement_id: str,
    *,
    author: str,
    rationale: str = "",
) -> None:
    """Remove a requirement-issue link and record the action.

    Args:
        session: Active SQLAlchemy session. The caller commits.
        issue_id: Primary key of the issue half of the link.
        requirement_id: Primary key of the requirement half of the link.
        author: Who is performing the unlink (for the audit row).
        rationale: Optional human-readable note about why.

    Raises:
        RequirementIssueLinkNotFoundError: If no link matches.
    """
    link = session.get(RequirementIssueLink, (requirement_id, issue_id))
    if link is None:
        raise RequirementIssueLinkNotFoundError(
            f"No link between requirement={requirement_id} and issue={issue_id}"
        )

    session.delete(link)

    description = f"Unlinked from requirement {requirement_id}"
    if rationale:
        description = f"{description}: {rationale}"
    session.add(
        IssueUpdateRow(
            issue_id=issue_id,
            update_type_code="requirement_unlinked",
            description=description,
            diff={},
            action_taken="",
            action_result="",
            author=author,
            date=_now(),
        )
    )

    logger.info(
        "Unlinked issue {} from requirement {} (author={})",
        issue_id,
        requirement_id,
        author,
    )


def list_issue_statuses(session: Session) -> Sequence[IssueStatus]:
    """Return every issue status ordered by ``sort_order``.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        Sequence of :class:`IssueStatus` rows.
    """
    stmt = select(IssueStatus).order_by(IssueStatus.sort_order.asc())
    return session.execute(stmt).scalars().all()


def list_issue_types(session: Session) -> Sequence[IssueType]:
    """Return every issue type ordered by ``sort_order``.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        Sequence of :class:`IssueType` rows.
    """
    stmt = select(IssueType).order_by(IssueType.sort_order.asc())
    return session.execute(stmt).scalars().all()


def list_issue_priorities(session: Session) -> Sequence[IssuePriority]:
    """Return every issue priority ordered by ``sort_order``.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        Sequence of :class:`IssuePriority` rows.
    """
    stmt = select(IssuePriority).order_by(IssuePriority.sort_order.asc())
    return session.execute(stmt).scalars().all()
