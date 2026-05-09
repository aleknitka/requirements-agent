"""Service backing the ``get_full_report`` MCP tool.

Builds a single, consistent snapshot of the database — every
requirement (by default, including terminal ones) with its audit log
and the issues linked to it, plus the issues that are not linked to
any requirement. All reads happen inside the caller's session, so the
caller controls the transaction boundary.

Two filter knobs are supported, both default ``True`` (include
everything):

* ``include_issues`` — when ``False``, all issue lists in the result
  are empty. Requirement audit history is unaffected.
* ``include_closed_requirements`` — when ``False``, requirements whose
  status is ``is_terminal`` are skipped. Driven by the seed table, not
  a hard-coded list.

Bare call returns the complete dataset.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from requirements_mcp.constants import PROJECT_NAME
from requirements_mcp.models import (
    Issue,
    IssuePriority,
    IssueStatus,
    Requirement,
    RequirementChange,
    RequirementIssueLink,
    RequirementStatus,
)
from requirements_mcp.models import IssueUpdate as IssueUpdateRow
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
        issue: The ORM row. ``issue.updates`` is read; tests must
            ensure the relationship is loaded or accept the lazy load.
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
    payload.updates = [
        IssueUpdateOut.model_validate(row)
        for row in sorted(issue.updates, key=lambda u: (u.date, u.id))
    ]
    return payload


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
            status row has ``is_terminal=True`` are omitted. Defaults
            to ``True``.

    Returns:
        A :class:`FullReportOut` with stable, JSON-friendly fields. Use
        ``model.model_dump(mode="json")`` for the canonical
        serialisation.
    """
    requirements = _load_requirements(
        session,
        include_closed_requirements=include_closed_requirements,
    )

    requirement_payloads: list[RequirementInReport] = []
    attached_count = 0
    for req in requirements:
        changes = (
            session.execute(
                select(RequirementChange)
                .where(RequirementChange.requirement_id == req.id)
                .order_by(RequirementChange.date.asc(), RequirementChange.id.asc())
            )
            .scalars()
            .all()
        )

        if include_issues:
            attached = _load_attached_issues(session, req.id)
            attached_count += len(attached)
            issue_payloads = [
                _build_issue_in_report(
                    issue,
                    link_type=link_type,
                    rationale=rationale,
                )
                for issue, link_type, rationale in attached
            ]
        else:
            issue_payloads = []

        payload = RequirementInReport.model_validate(req)
        payload.changes = [RequirementChangeOut.model_validate(c) for c in changes]
        payload.issues = issue_payloads
        requirement_payloads.append(payload)

    if include_issues:
        unattached = _load_unattached_issues(session)
        unattached_payloads = [_build_issue_in_report(issue) for issue in unattached]
    else:
        unattached_payloads = []

    summary = ReportSummary(
        requirement_count=len(requirement_payloads),
        issue_count=attached_count + len(unattached_payloads),
        attached_issue_count=attached_count,
        unattached_issue_count=len(unattached_payloads),
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
    """Load requirements ordered by status sort_order, newest-updated first.

    Args:
        session: Active session.
        include_closed_requirements: When ``False``, omit rows whose
            status is terminal.

    Returns:
        List of :class:`Requirement` ORM rows.
    """
    stmt = (
        select(Requirement)
        .join(RequirementStatus, RequirementStatus.code == Requirement.status_code)
        .order_by(
            RequirementStatus.sort_order.asc(),
            Requirement.date_updated.desc(),
            Requirement.id.asc(),
        )
    )
    if not include_closed_requirements:
        stmt = stmt.where(RequirementStatus.is_terminal.is_(False))
    return list(session.execute(stmt).scalars().all())


def _load_attached_issues(
    session: Session,
    requirement_id: str,
) -> list[tuple[Issue, str, str]]:
    """Return ``(issue, link_type, rationale)`` for issues linked to ``requirement_id``.

    Sorted by issue priority severity descending, then status sort
    order, then date_updated descending so the most severe and most
    recently active items surface first.

    Args:
        session: Active session.
        requirement_id: Primary key of the parent requirement.

    Returns:
        A list of three-tuples ready to be projected via
        :func:`_build_issue_in_report`.
    """
    stmt = (
        select(Issue, RequirementIssueLink.link_type, RequirementIssueLink.rationale)
        .join(RequirementIssueLink, RequirementIssueLink.issue_id == Issue.id)
        .join(IssuePriority, IssuePriority.code == Issue.priority_code)
        .join(IssueStatus, IssueStatus.code == Issue.status_code)
        .where(RequirementIssueLink.requirement_id == requirement_id)
        .order_by(
            IssuePriority.severity_order.desc(),
            IssueStatus.sort_order.asc(),
            Issue.date_updated.desc(),
            Issue.id.asc(),
        )
    )
    rows = session.execute(stmt).all()
    return [(issue, link_type, rationale) for issue, link_type, rationale in rows]


def _load_unattached_issues(session: Session) -> list[Issue]:
    """Return issues that are not linked to any requirement, severity-first."""
    # Subquery: every issue id that has at least one link.
    linked_ids = select(RequirementIssueLink.issue_id).distinct()
    stmt = (
        select(Issue)
        .join(IssuePriority, IssuePriority.code == Issue.priority_code)
        .join(IssueStatus, IssueStatus.code == Issue.status_code)
        .where(Issue.id.notin_(linked_ids))
        .order_by(
            IssuePriority.severity_order.desc(),
            IssueStatus.sort_order.asc(),
            Issue.date_updated.desc(),
            Issue.id.asc(),
        )
    )
    return list(session.execute(stmt).scalars().all())


# Suppress unused-import warning: ``IssueUpdateRow`` is imported only
# so the relationship is registered before lazy access.
_ = IssueUpdateRow
