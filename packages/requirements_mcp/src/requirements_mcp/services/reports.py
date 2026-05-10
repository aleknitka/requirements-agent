"""Service backing the ``get_full_report`` MCP tool.

Builds a single, consistent snapshot of the database — every
requirement (by default, including terminal ones) with its audit log
and the issues linked to it, plus the issues that are not linked to
any *visible* requirement. All reads happen inside the caller's
session, so the caller controls the transaction boundary.

Two filter knobs are supported, both default ``True`` (include
everything):

* ``include_issues`` — when ``False``, all issue lists in the result
  are empty. Requirement audit history is unaffected.
* ``include_closed_requirements`` — when ``False``, requirements whose
  status is ``is_terminal`` are skipped. Driven by the seed table, not
  a hard-coded list.

When ``include_closed_requirements`` filters out a requirement, any
issue that was linked *only* to that filtered-out requirement falls
through into ``unattached_issues`` so the report never silently drops
a real issue with its history.

Bare call returns the complete dataset.

The implementation is intentionally bulk-friendly:

* ``Requirement.changes`` is loaded with ``selectinload`` in one extra
  round-trip rather than per-requirement;
* attached ``(link, issue)`` pairs are pulled with one query keyed by
  the visible requirement set, with ``Issue.updates`` eager-loaded;
* unattached issues use the same eager-load.

Sorting is then done in Python from cached priority/status order
dictionaries — one round-trip apiece — so adding more sort tiers does
not multiply the database work.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from requirements_mcp.constants import PROJECT_NAME
from requirements_mcp.models import (
    Issue,
    IssuePriority,
    IssueStatus,
    Requirement,
    RequirementIssueLink,
    RequirementStatus,
)
from requirements_mcp.schemas.issues import IssueUpdateOut
from requirements_mcp.schemas.reports import (
    FullReportOut,
    IssueInReport,
    ReportSummary,
    RequirementInReport,
)
from requirements_mcp.schemas.requirements import RequirementChangeOut

__all__ = ["build_full_report"]


def _build_issue_in_report(
    issue: Issue,
    *,
    link_type: str | None = None,
    rationale: str | None = None,
) -> IssueInReport:
    """Project an :class:`Issue` ORM row into an :class:`IssueInReport`.

    Args:
        issue: ORM row. ``issue.updates`` should already be eager-loaded
            by the caller (`selectinload`) — the relationship is
            iterated here.
        link_type: Optional link kind when the issue is nested under a
            requirement. ``None`` for unattached entries.
        rationale: Optional link rationale. ``None`` for unattached.

    Returns:
        A populated :class:`IssueInReport` ready to be embedded in a
        :class:`FullReportOut`.
    """
    payload = IssueInReport.model_validate(issue)
    payload.link_type = link_type
    payload.rationale = rationale
    # The Issue.updates relationship is declared with order_by=date,
    # so the rows arrive sorted; the explicit sort here is defensive
    # and tie-breaks on id when two updates share a timestamp.
    payload.updates = [
        IssueUpdateOut.model_validate(row)
        for row in sorted(issue.updates, key=lambda u: (u.date, u.id))
    ]
    return payload


def _issue_sort_key(
    issue: Issue,
    priority_order: dict[str, int],
    status_order: dict[str, int],
) -> tuple[Any, ...]:
    """Sort key matching the SQL ordering used by the previous implementation.

    Tuple, in order: priority severity descending, status sort_order
    ascending, ``date_updated`` descending, then ``id`` ascending for a
    stable tiebreaker. Unknown codes sort last, never crash.
    """
    return (
        -priority_order.get(issue.priority_code, 0),
        status_order.get(issue.status_code, 10**9),
        -issue.date_updated.timestamp() if issue.date_updated else 0,
        issue.id,
    )


def build_full_report(
    session: Session,
    *,
    include_issues: bool = True,
    include_closed_requirements: bool = True,
) -> FullReportOut:
    """Return a complete project snapshot for downstream PDF rendering.

    Args:
        session: Active SQLAlchemy session. The caller controls
            transaction boundaries; this function only reads.
        include_issues: When ``False``, every ``issues`` list (nested
            under requirements and the top-level ``unattached_issues``)
            is left empty. Defaults to ``True``.
        include_closed_requirements: When ``False``, requirements whose
            status row has ``is_terminal=True`` are omitted; any issue
            linked only to those filtered-out requirements is surfaced
            under ``unattached_issues`` so it is never silently lost.
            Defaults to ``True``.

    Returns:
        A :class:`FullReportOut` with stable, JSON-friendly fields. Use
        ``model.model_dump(mode="json")`` for the canonical
        serialisation.
    """
    requirements = _load_requirements(
        session,
        include_closed_requirements=include_closed_requirements,
    )
    visible_req_ids: set[str] = {r.id for r in requirements}

    if include_issues:
        priority_order = _load_priority_order(session)
        status_order = _load_status_order(session)
        attached_by_req = _load_attached_by_requirement(
            session, visible_req_ids, priority_order, status_order
        )
        unattached = _load_unattached_issues(
            session, visible_req_ids, priority_order, status_order
        )
    else:
        attached_by_req = {}
        unattached = []

    distinct_attached_ids: set[str] = set()
    requirement_payloads: list[RequirementInReport] = []
    for req in requirements:
        nested: list[IssueInReport] = []
        if include_issues:
            for issue, link_type, rationale in attached_by_req.get(req.id, []):
                nested.append(
                    _build_issue_in_report(
                        issue, link_type=link_type, rationale=rationale
                    )
                )
                distinct_attached_ids.add(issue.id)
        payload = RequirementInReport.model_validate(req)
        # ``Requirement.changes`` is eager-loaded via selectinload above
        # and the relationship is declared with order_by=date.
        payload.changes = [RequirementChangeOut.model_validate(c) for c in req.changes]
        payload.issues = nested
        requirement_payloads.append(payload)

    unattached_payloads = [_build_issue_in_report(issue) for issue in unattached]

    summary = ReportSummary(
        requirement_count=len(requirement_payloads),
        attached_issue_count=len(distinct_attached_ids),
        unattached_issue_count=len(unattached_payloads),
        # `issue_count` is the number of *distinct* issues across both
        # buckets — it is not the sum of nested-list lengths, because
        # one issue may legitimately appear under multiple requirements.
        issue_count=len(distinct_attached_ids) + len(unattached_payloads),
        included_issues=include_issues,
        included_closed_requirements=include_closed_requirements,
    )

    return FullReportOut(
        generated_at=datetime.now(timezone.utc),
        project_name=PROJECT_NAME,
        summary=summary,
        requirements=requirement_payloads,
        unattached_issues=unattached_payloads,
    )


def _load_requirements(
    session: Session,
    *,
    include_closed_requirements: bool,
) -> list[Requirement]:
    """Load requirements ordered by status sort_order, with changes eager-loaded.

    Uses ``selectinload(Requirement.changes)`` so the per-requirement
    audit log arrives in one extra round-trip rather than N.

    Args:
        session: Active session.
        include_closed_requirements: When ``False``, omit rows whose
            status is terminal.

    Returns:
        List of :class:`Requirement` ORM rows with ``.changes``
        prefetched.
    """
    stmt = (
        select(Requirement)
        .join(RequirementStatus, RequirementStatus.code == Requirement.status_code)
        .options(selectinload(Requirement.changes))
        .order_by(
            RequirementStatus.sort_order.asc(),
            Requirement.date_updated.desc(),
            Requirement.id.asc(),
        )
    )
    if not include_closed_requirements:
        stmt = stmt.where(RequirementStatus.is_terminal.is_(False))
    return list(session.execute(stmt).scalars().all())


def _load_priority_order(session: Session) -> dict[str, int]:
    """Return ``{priority_code: severity_order}`` from the seed table."""
    return {
        row.code: row.severity_order
        for row in session.scalars(select(IssuePriority)).all()
    }


def _load_status_order(session: Session) -> dict[str, int]:
    """Return ``{status_code: sort_order}`` from the issue-status seed table."""
    return {
        row.code: row.sort_order for row in session.scalars(select(IssueStatus)).all()
    }


def _load_attached_by_requirement(
    session: Session,
    visible_req_ids: set[str],
    priority_order: dict[str, int],
    status_order: dict[str, int],
) -> dict[str, list[tuple[Issue, str, str]]]:
    """Bulk-load every (issue, link_type, rationale) for the visible requirements.

    Eager-loads ``Issue.updates`` via ``selectinload`` so the per-issue
    audit log does not trigger N extra queries when the report is
    rendered. Returns a dict keyed by ``requirement_id`` with each
    list pre-sorted by :func:`_issue_sort_key`.

    Args:
        session: Active session.
        visible_req_ids: Set of requirement ids that survived the
            terminal-status filter. Empty when there are no
            requirements; the function returns an empty dict in that
            case without issuing the query.
        priority_order: Map produced by :func:`_load_priority_order`.
        status_order: Map produced by :func:`_load_status_order`.

    Returns:
        ``{requirement_id: [(issue, link_type, rationale), ...]}`` —
        ready for direct consumption inside the requirement loop.
    """
    if not visible_req_ids:
        return {}

    stmt = (
        select(RequirementIssueLink, Issue)
        .join(Issue, Issue.id == RequirementIssueLink.issue_id)
        .options(selectinload(Issue.updates))
        .where(RequirementIssueLink.requirement_id.in_(visible_req_ids))
    )
    rows = session.execute(stmt).all()

    grouped: dict[str, list[tuple[Issue, str, str]]] = defaultdict(list)
    for link, issue in rows:
        grouped[link.requirement_id].append((issue, link.link_type, link.rationale))

    for entries in grouped.values():
        entries.sort(
            key=lambda tup: _issue_sort_key(tup[0], priority_order, status_order)
        )
    return grouped


def _load_unattached_issues(
    session: Session,
    visible_req_ids: set[str],
    priority_order: dict[str, int],
    status_order: dict[str, int],
) -> list[Issue]:
    """Return issues not linked to any *visible* requirement.

    An issue counts as "unattached" when it has zero links into the
    visible requirement set. That includes:

    * issues with no rows in ``requirement_issues`` at all, and
    * issues whose only links point at requirements that were filtered
      out by ``include_closed_requirements=False``.

    The latter case is what guarantees the report never silently drops
    an issue and its update history when the closed-requirement filter
    hides its parent.

    ``Issue.updates`` is eager-loaded via ``selectinload``.
    """
    if visible_req_ids:
        linked_to_visible = (
            select(RequirementIssueLink.issue_id)
            .where(RequirementIssueLink.requirement_id.in_(visible_req_ids))
            .distinct()
        )
        stmt = (
            select(Issue)
            .options(selectinload(Issue.updates))
            .where(Issue.id.notin_(linked_to_visible))
        )
    else:
        # No visible requirements at all → every issue is "unattached"
        # for the purposes of this report.
        stmt = select(Issue).options(selectinload(Issue.updates))

    rows = list(session.execute(stmt).scalars().all())
    rows.sort(key=lambda issue: _issue_sort_key(issue, priority_order, status_order))
    return rows
