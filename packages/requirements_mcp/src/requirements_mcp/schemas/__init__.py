"""Pydantic boundary models for MCP tool inputs and outputs.

The schema layer is the validation boundary between the agent (or any
other MCP client) and the persistence layer. ORM classes carry database
concerns; these schemas carry tool-call concerns. Inputs use
``extra="forbid"`` so a misspelled field name surfaces as a clear
validation error instead of silently being ignored.
"""

from requirements_mcp.schemas.issues import (
    IssueCreate,
    IssueOut,
    IssuePriorityCode,
    IssuePriorityOut,
    IssueSearchHit,
    IssueSearchQuery,
    IssueStatusCode,
    IssueStatusOut,
    IssueTypeCode,
    IssueTypeOut,
    IssueUpdate,
    IssueUpdateAdd,
    IssueUpdateOut,
    IssueUpdateTypeCode,
    RequirementIssueLinkCreate,
    RequirementIssueLinkOut,
    RequirementIssueLinkType,
)
from requirements_mcp.schemas.reports import (
    FullReportOut,
    IssueInReport,
    ReportSummary,
    RequirementInReport,
)
from requirements_mcp.schemas.requirements import (
    RequirementChangeOut,
    RequirementCreate,
    RequirementOut,
    RequirementSearchHit,
    RequirementSearchQuery,
    RequirementStatusCode,
    RequirementStatusOut,
    RequirementTypeCode,
    RequirementTypeOut,
    RequirementUpdate,
)

__all__ = [
    "FullReportOut",
    "IssueCreate",
    "IssueInReport",
    "IssueOut",
    "IssuePriorityCode",
    "IssuePriorityOut",
    "IssueSearchHit",
    "IssueSearchQuery",
    "IssueStatusCode",
    "IssueStatusOut",
    "IssueTypeCode",
    "IssueTypeOut",
    "IssueUpdate",
    "IssueUpdateAdd",
    "IssueUpdateOut",
    "IssueUpdateTypeCode",
    "ReportSummary",
    "RequirementChangeOut",
    "RequirementCreate",
    "RequirementInReport",
    "RequirementIssueLinkCreate",
    "RequirementIssueLinkOut",
    "RequirementIssueLinkType",
    "RequirementOut",
    "RequirementSearchHit",
    "RequirementSearchQuery",
    "RequirementStatusCode",
    "RequirementStatusOut",
    "RequirementTypeCode",
    "RequirementTypeOut",
    "RequirementUpdate",
]
