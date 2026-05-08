"""MCP tool handlers for the issue subsystem.

Each handler takes a :class:`sessionmaker` factory plus the validated
Pydantic input model. The pattern is identical to
:mod:`requirements_mcp.tools.requirements`:

1. Open a session via the factory.
2. Call the matching service function in
   :mod:`requirements_mcp.services.issues`.
3. Convert the ORM result into the matching Pydantic output model with
   ``Out.model_validate(orm_obj)`` (works because the schemas set
   ``from_attributes=True``).
4. Commit on success; the session context manager handles rollback on
   exception.

These plain functions are also what the Gradio app binds to UI
components and exposes as MCP tools.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from requirements_mcp.schemas.issues import (
    IssueCreate,
    IssueOut,
    IssuePriorityOut,
    IssueSearchHit,
    IssueSearchQuery,
    IssueStatusOut,
    IssueTypeOut,
    IssueUpdate,
    IssueUpdateAdd,
    IssueUpdateOut,
    RequirementIssueLinkCreate,
    RequirementIssueLinkOut,
)
from requirements_mcp.services import issues as svc

__all__ = [
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


def _open(session_factory: sessionmaker[Session]) -> Session:
    """Open a new session from ``session_factory``.

    Args:
        session_factory: Factory configured by
            :func:`requirements_mcp.db.engine.make_session_factory`.

    Returns:
        A fresh :class:`Session` ready for use as a context manager.
    """
    return session_factory()


def create_issue(
    session_factory: sessionmaker[Session],
    payload: IssueCreate,
) -> IssueOut:
    """Create a new issue and return its full state.

    Args:
        session_factory: Active session factory bound to the target DB.
        payload: Validated input.

    Returns:
        The newly created issue as a :class:`IssueOut`.
    """
    with _open(session_factory) as session:
        issue = svc.create_issue(session, payload)
        session.commit()
        return IssueOut.model_validate(issue)


def update_issue(
    session_factory: sessionmaker[Session],
    issue_id: str,
    payload: IssueUpdate,
) -> IssueOut:
    """Apply an update to an existing issue.

    Args:
        session_factory: Active session factory.
        issue_id: Primary key to mutate.
        payload: Validated update model.

    Returns:
        The post-update issue state. For a no-op update the returned
        ``date_updated`` is unchanged and no audit row is written.

    Raises:
        requirements_mcp.services.issues.IssueNotFoundError: If the id
            is unknown.
    """
    with _open(session_factory) as session:
        issue = svc.update_issue(session, issue_id, payload)
        session.commit()
        return IssueOut.model_validate(issue)


def add_issue_update(
    session_factory: sessionmaker[Session],
    issue_id: str,
    payload: IssueUpdateAdd,
) -> IssueUpdateOut:
    """Append an action-log entry to an issue without changing its fields.

    Args:
        session_factory: Active session factory.
        issue_id: Primary key whose audit log to append.
        payload: Validated input.

    Returns:
        The new audit-log row as a :class:`IssueUpdateOut`.

    Raises:
        requirements_mcp.services.issues.IssueNotFoundError: If the id
            is unknown.
    """
    with _open(session_factory) as session:
        row = svc.add_issue_update(session, issue_id, payload)
        session.commit()
        return IssueUpdateOut.model_validate(row)


def get_issue(
    session_factory: sessionmaker[Session],
    issue_id: str,
) -> IssueOut | None:
    """Return one issue by id, or ``None`` if absent.

    Args:
        session_factory: Active session factory.
        issue_id: Primary key to look up.

    Returns:
        :class:`IssueOut` for the matching row, or ``None``.
    """
    with _open(session_factory) as session:
        issue = svc.get_issue(session, issue_id)
        if issue is None:
            return None
        return IssueOut.model_validate(issue)


def search_issues(
    session_factory: sessionmaker[Session],
    query: IssueSearchQuery,
) -> list[IssueSearchHit]:
    """Search issues by free text and code/owner filters.

    Args:
        session_factory: Active session factory.
        query: Validated search payload.

    Returns:
        A list of compact :class:`IssueSearchHit` projections, ordered
        most-recently-updated first.
    """
    with _open(session_factory) as session:
        rows = svc.search_issues(session, query)
        return [IssueSearchHit.model_validate(row) for row in rows]


def list_issue_updates(
    session_factory: sessionmaker[Session],
    issue_id: str,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[IssueUpdateOut]:
    """Return the audit log for one issue, oldest first.

    Args:
        session_factory: Active session factory.
        issue_id: Primary key whose history is requested.
        limit: Maximum rows to return.
        offset: Rows to skip.

    Returns:
        A list of :class:`IssueUpdateOut` rows ordered ascending.

    Raises:
        requirements_mcp.services.issues.IssueNotFoundError: If the id
            is unknown.
    """
    with _open(session_factory) as session:
        rows = svc.list_issue_updates(session, issue_id, limit=limit, offset=offset)
        return [IssueUpdateOut.model_validate(row) for row in rows]


def list_open_issues(
    session_factory: sessionmaker[Session],
) -> list[IssueOut]:
    """Return every issue in a non-terminal status.

    Args:
        session_factory: Active session factory.

    Returns:
        A list of :class:`IssueOut` rows ordered by ``date_updated``
        descending.
    """
    with _open(session_factory) as session:
        rows = svc.list_open_issues(session)
        return [IssueOut.model_validate(row) for row in rows]


def list_blocking_issues(
    session_factory: sessionmaker[Session],
) -> list[IssueOut]:
    """Return every non-terminal blocker (issue type ``"BLK"``).

    Args:
        session_factory: Active session factory.

    Returns:
        A list of :class:`IssueOut` rows ordered by severity descending.
    """
    with _open(session_factory) as session:
        rows = svc.list_blocking_issues(session)
        return [IssueOut.model_validate(row) for row in rows]


def link_issue_to_requirement(
    session_factory: sessionmaker[Session],
    issue_id: str,
    payload: RequirementIssueLinkCreate,
) -> RequirementIssueLinkOut:
    """Create a typed link from an issue to a requirement.

    Args:
        session_factory: Active session factory.
        issue_id: Primary key of the issue.
        payload: Validated link payload.

    Returns:
        The new link row as :class:`RequirementIssueLinkOut`.

    Raises:
        requirements_mcp.services.issues.IssueNotFoundError: Unknown issue.
        requirements_mcp.services.requirements.RequirementNotFoundError:
            Unknown requirement.
        requirements_mcp.services.issues.RequirementIssueLinkAlreadyExistsError:
            Duplicate link.
    """
    with _open(session_factory) as session:
        link = svc.link_issue_to_requirement(session, issue_id, payload)
        session.commit()
        return RequirementIssueLinkOut.model_validate(link)


def unlink_issue_from_requirement(
    session_factory: sessionmaker[Session],
    issue_id: str,
    requirement_id: str,
    *,
    author: str,
    rationale: str = "",
) -> None:
    """Remove the link between an issue and a requirement.

    Args:
        session_factory: Active session factory.
        issue_id: Primary key of the issue side of the link.
        requirement_id: Primary key of the requirement side.
        author: Who is performing the unlink (audit attribution).
        rationale: Optional human-readable note.

    Raises:
        requirements_mcp.services.issues.RequirementIssueLinkNotFoundError:
            If no such link exists.
    """
    with _open(session_factory) as session:
        svc.unlink_issue_from_requirement(
            session,
            issue_id,
            requirement_id,
            author=author,
            rationale=rationale,
        )
        session.commit()


def list_issue_statuses(
    session_factory: sessionmaker[Session],
) -> list[IssueStatusOut]:
    """Return every issue status ordered by ``sort_order``.

    Args:
        session_factory: Active session factory.

    Returns:
        A list of :class:`IssueStatusOut` rows.
    """
    with _open(session_factory) as session:
        rows = svc.list_issue_statuses(session)
        return [IssueStatusOut.model_validate(row) for row in rows]


def list_issue_types(
    session_factory: sessionmaker[Session],
) -> list[IssueTypeOut]:
    """Return every issue type ordered by ``sort_order``.

    Args:
        session_factory: Active session factory.

    Returns:
        A list of :class:`IssueTypeOut` rows.
    """
    with _open(session_factory) as session:
        rows = svc.list_issue_types(session)
        return [IssueTypeOut.model_validate(row) for row in rows]


def list_issue_priorities(
    session_factory: sessionmaker[Session],
) -> list[IssuePriorityOut]:
    """Return every issue priority ordered by ``sort_order``.

    Args:
        session_factory: Active session factory.

    Returns:
        A list of :class:`IssuePriorityOut` rows.
    """
    with _open(session_factory) as session:
        rows = svc.list_issue_priorities(session)
        return [IssuePriorityOut.model_validate(row) for row in rows]
