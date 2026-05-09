"""MCP tool handler for the full project report.

Thin wrapper around :func:`requirements_mcp.services.reports.build_full_report`:
opens a session from the supplied factory, calls the service with the
caller's flag values, returns the Pydantic model. The session is
read-only by design — no commit is needed.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from requirements_mcp.schemas.reports import FullReportOut
from requirements_mcp.services.reports import build_full_report

__all__ = ["get_full_report"]


def get_full_report(
    session_factory: sessionmaker[Session],
    include_issues: bool = True,
    include_closed_requirements: bool = True,
) -> FullReportOut:
    """Return a complete project snapshot as a JSON-friendly model.

    Default call returns everything: every requirement (regardless of
    status), every audit row, every attached issue with its updates,
    and every unattached issue with its updates.

    Args:
        session_factory: SQLAlchemy session factory bound to the
            project database.
        include_issues: When ``False``, both nested ``issues`` lists
            and the top-level ``unattached_issues`` are empty.
        include_closed_requirements: When ``False``, omit requirements
            whose status row has ``is_terminal=True``.

    Returns:
        A :class:`FullReportOut`. Serialise via
        ``result.model_dump(mode="json")`` for ReportLab ``json2pdf``.
    """
    with session_factory() as session:
        return build_full_report(
            session,
            include_issues=include_issues,
            include_closed_requirements=include_closed_requirements,
        )
