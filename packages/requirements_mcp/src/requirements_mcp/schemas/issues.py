"""Pydantic schemas for the issue MCP tools.

Mirrors the structure of :mod:`requirements_mcp.schemas.requirements`:

* **Input models** (``IssueCreate``, ``IssueUpdate``, ``IssueUpdateAdd``,
  ``RequirementIssueLinkCreate``, ``IssueSearchQuery``) validate
  incoming MCP tool arguments. ``extra="forbid"`` is set on each.
* **Output models** (``IssueOut``, ``IssueUpdateOut``,
  ``RequirementIssueLinkOut``, ``IssueSearchHit``, ``IssueStatusOut``,
  ``IssueTypeOut``, ``IssuePriorityOut``) are constructed from ORM rows
  via ``Model.model_validate(orm_obj)`` thanks to
  ``from_attributes=True``.
* **Closed-set Literals** for codes; each is paired with a guard test
  in ``tests/test_schemas_issues.py`` that asserts the Literal stays in
  lock-step with the matching seed list.

The Pydantic class :class:`IssueUpdate` is named to mirror Phase 2's
:class:`requirements_mcp.schemas.requirements.RequirementUpdate`. The
SQLAlchemy ORM class of the same name is imported with an alias
(``IssueUpdate as IssueUpdateRow``) only in
:mod:`requirements_mcp.services.issues`, the only place both are needed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Closed-set Literals — guarded against the seed lists by tests in
# tests/test_schemas_issues.py.

IssueStatusCode = Literal[
    "open",
    "triaged",
    "needs_clarification",
    "waiting_for_stakeholder",
    "in_progress",
    "blocked",
    "resolved",
    "closed",
    "reopened",
    "cancelled",
]
"""Closed set of issue status codes accepted by the MCP tool inputs."""

IssueTypeCode = Literal[
    "AMB",
    "GAP",
    "CNF",
    "RSK",
    "BLK",
    "QST",
    "DEC",
    "EVD",
    "VAL",
    "CHG",
    "MSC",
]
"""Closed set of issue type codes accepted by the MCP tool inputs."""

IssuePriorityCode = Literal["LOW", "MED", "HIG", "CRT"]
"""Closed set of issue priority codes accepted by the MCP tool inputs."""

RequirementIssueLinkType = Literal[
    "related",
    "blocks",
    "clarifies",
    "conflicts_with",
    "risk_for",
    "caused_by",
    "resolved_by",
]
"""Closed set of requirement-issue link kinds."""

IssueUpdateTypeCode = Literal[
    # Service-emitted, derived from action:
    "created",
    "field_changed",
    "status_changed",
    "priority_changed",
    "requirement_linked",
    "requirement_unlinked",
    # User-supplied via add_issue_update:
    "note",
    "email_sent",
    "email_received",
    "evidence_added",
    "requirement_updated",
    "stakeholder_question_asked",
    "resolution_proposed",
    "issue_resolved",
    "issue_reopened",
]
"""Closed set of update-type codes used in the issue audit log."""


__all__ = [
    "IssueCreate",
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
    "RequirementIssueLinkCreate",
    "RequirementIssueLinkOut",
    "RequirementIssueLinkType",
]


class IssueCreate(BaseModel):
    """Input payload for ``create_issue``.

    ``status_code`` defaults to ``"open"`` and ``priority_code`` to
    ``"MED"`` so the bare minimum a caller needs to supply is the title,
    description, type, and the user attributing the creation.
    """

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    issue_type_code: IssueTypeCode
    status_code: IssueStatusCode = "open"
    priority_code: IssuePriorityCode = "MED"
    impact: str = ""
    risk: str = ""
    proposed_resolution: str = ""
    owner: str | None = None
    created_by: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")


class IssueUpdate(BaseModel):
    """Input payload for ``update_issue``.

    Distinct from the SQLAlchemy ``IssueUpdate`` ORM class. Two
    non-diffable fields are required on every call so the audit row is
    self-explanatory: ``author`` records who is making the change and
    ``change_description`` is a short note about why. The audit row is
    written only when at least one diffable field actually changes; for
    a no-op update the caller's ``change_description`` is discarded.

    ``owner`` is special-cased: an explicit ``None`` is a meaningful
    clear (the column is nullable on the ORM). Other ``None`` values
    are filtered out by the service before the diff is computed.

    ``issue_type_code`` is intentionally absent: the type is encoded in
    the issue's id (``ISSUE-<TYPE>-<6>``) and must not change after
    creation. ``extra="forbid"`` causes attempts to update it to fail
    loudly at validation time.
    """

    author: str = Field(min_length=1, max_length=255)
    change_description: str = Field(min_length=1)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    status_code: IssueStatusCode | None = None
    priority_code: IssuePriorityCode | None = None
    impact: str | None = None
    risk: str | None = None
    proposed_resolution: str | None = None
    owner: str | None = None

    model_config = ConfigDict(extra="forbid")


class IssueUpdateAdd(BaseModel):
    """Input payload for ``add_issue_update``.

    Append an action-log entry without mutating Issue fields. Used for
    free-form notes, email correspondence records, evidence pointers,
    and other operational events that should appear in the issue's
    history.
    """

    update_type_code: IssueUpdateTypeCode
    description: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=255)
    action_taken: str = ""
    action_result: str = ""

    model_config = ConfigDict(extra="forbid")


class RequirementIssueLinkCreate(BaseModel):
    """Input payload for ``link_issue_to_requirement``.

    The ``link_type`` is drawn from a small closed vocabulary describing
    how the issue relates to the requirement. ``rationale`` is a short
    free-text note captured at link-creation time so the audit log
    stays self-explanatory; ``author`` attributes the link.
    """

    requirement_id: str = Field(min_length=1)
    link_type: RequirementIssueLinkType = "related"
    rationale: str = ""
    author: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")


class IssueSearchQuery(BaseModel):
    """Input payload for ``search_issues``.

    The ``query`` string is whitespace-tokenised; every token must be
    present (case-insensitively) in either ``title`` or ``description``.
    Code filters apply as OR-within / AND-between: e.g. setting both
    ``status_codes=["open"]`` and ``priority_codes=["HIG", "CRT"]``
    returns open issues that are also high or critical priority.
    """

    query: str = ""
    status_codes: list[IssueStatusCode] | None = None
    type_codes: list[IssueTypeCode] | None = None
    priority_codes: list[IssuePriorityCode] | None = None
    owner: str | None = None
    created_by: str | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(extra="forbid")


class IssueOut(BaseModel):
    """Read model returned by ``create_issue``, ``update_issue``, and ``get_issue``."""

    id: str
    title: str
    description: str
    issue_type_code: str
    status_code: str
    priority_code: str
    impact: str
    risk: str
    proposed_resolution: str
    owner: str | None
    created_by: str
    date_created: datetime
    date_updated: datetime
    date_closed: datetime | None

    model_config = ConfigDict(from_attributes=True)


class IssueUpdateOut(BaseModel):
    """Read model for one row of the issue audit log."""

    id: str
    issue_id: str
    update_type_code: str
    description: str
    diff: dict[str, Any]
    action_taken: str
    action_result: str
    author: str
    date: datetime

    model_config = ConfigDict(from_attributes=True)


class RequirementIssueLinkOut(BaseModel):
    """Read model for one row of the ``requirement_issues`` link table."""

    requirement_id: str
    issue_id: str
    link_type: str
    rationale: str
    date_created: datetime

    model_config = ConfigDict(from_attributes=True)


class IssueSearchHit(BaseModel):
    """Compact projection returned by ``search_issues``.

    Lighter than :class:`IssueOut` because search results often serve
    as picker lists; full detail is fetched separately via
    ``get_issue``.
    """

    id: str
    title: str
    issue_type_code: str
    status_code: str
    priority_code: str
    owner: str | None
    date_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class IssueStatusOut(BaseModel):
    """Read model for an issue status row."""

    code: str
    label: str
    description: str
    is_terminal: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class IssueTypeOut(BaseModel):
    """Read model for an issue type row."""

    code: str
    key: str
    label: str
    description: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class IssuePriorityOut(BaseModel):
    """Read model for an issue priority row."""

    code: str
    label: str
    description: str
    severity_order: int
    sort_order: int

    model_config = ConfigDict(from_attributes=True)
