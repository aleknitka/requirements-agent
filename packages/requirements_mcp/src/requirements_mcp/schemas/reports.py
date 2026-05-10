"""Output schema for the ``get_full_report`` MCP tool.

The tool returns one tree-shaped JSON document covering every
requirement (with its audit trail and the issues linked to it) followed
by every issue not linked to any requirement. The shape is intentionally
ergonomic for downstream PDF rendering with ReportLab's ``json2pdf``
service: stable ``snake_case`` keys, ISO-8601 datetime strings under
``mode="json"``, no ``None`` sentinels in list slots, and a top-level
``summary`` block with pre-computed counts so a cover-page template can
render totals without iterating the body lists.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from requirements_mcp.schemas.issues import IssueOut, IssueUpdateOut
from requirements_mcp.schemas.requirements import (
    RequirementChangeOut,
    RequirementOut,
)

__all__ = [
    "FullReportOut",
    "IssueInReport",
    "ReportSummary",
    "RequirementInReport",
]


class IssueInReport(IssueOut):
    """An issue as it appears inside the full report.

    Adds three keys to :class:`IssueOut`:

    * ``link_type`` and ``rationale`` are populated when the issue is
      nested under a requirement; both are ``None`` for entries in
      :attr:`FullReportOut.unattached_issues`.
    * ``updates`` is the issue's audit / action log in chronological
      order.

    The keys are always present in the JSON so a ``json2pdf`` template
    can reference them unconditionally.
    """

    link_type: str | None = None
    rationale: str | None = None
    updates: list[IssueUpdateOut] = []

    model_config = ConfigDict(from_attributes=True)


class RequirementInReport(RequirementOut):
    """A requirement as it appears inside the full report.

    Adds the audit-log rows under ``changes`` and the linked issues
    under ``issues``. Both keys are always present (empty list when
    there is nothing to show) so templates can iterate without
    null-guards.
    """

    changes: list[RequirementChangeOut] = []
    issues: list[IssueInReport] = []

    model_config = ConfigDict(from_attributes=True)


class ReportSummary(BaseModel):
    """Pre-computed totals and filter echoes for the report header.

    A ReportLab ``json2pdf`` template can drop these onto the cover page
    without touching the (potentially large) body lists. The two
    ``included_*`` flags echo the call's parameters so the rendered PDF
    can show a "filters applied" line.
    """

    requirement_count: int
    issue_count: int
    attached_issue_count: int
    unattached_issue_count: int
    included_issues: bool
    included_closed_requirements: bool


class FullReportOut(BaseModel):
    """Full requirements + issues snapshot returned by ``get_full_report``.

    Top-level keys (always present):

    * ``generated_at`` — UTC timestamp of when the snapshot was built.
    * ``project_name`` — the project branding from
      :data:`requirements_mcp.constants.PROJECT_NAME`.
    * ``summary`` — pre-computed counts, see :class:`ReportSummary`.
    * ``requirements`` — every requirement (sorted by status) with
      embedded changes and attached issues. Empty when the database
      contains no requirements.
    * ``unattached_issues`` — issues that are not linked to any
      requirement, sorted by priority severity descending. Empty when
      every issue is linked, or when the call set ``include_issues=False``.

    Use ``model.model_dump(mode="json")`` for the canonical JSON
    serialisation: datetimes become ISO-8601 strings, every default is
    materialised, and the result is round-trippable through
    :func:`json.loads`/:func:`json.dumps`.
    """

    generated_at: datetime
    project_name: str
    summary: ReportSummary
    requirements: list[RequirementInReport] = []
    unattached_issues: list[IssueInReport] = []
