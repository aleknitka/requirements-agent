"""Seed data for the ``issue_types`` table.

Defines the categories an issue can be classified as: ambiguity,
missing information, conflict, risk, blocker, stakeholder question,
decision needed, evidence needed, validation issue, change request, and
miscellaneous. Each entry has a stable three-letter code and a
readable lowercase slug for use in user interfaces.
"""

from __future__ import annotations

from pydantic import Field

from requirements_mcp.seeds._base import SeedBase


class IssueTypeSeed(SeedBase):
    """Validated row template for an issue type.

    The ``code`` is constrained to exactly three uppercase ASCII
    letters; the ``key`` is the matching lowercase slug. ``sort_order``
    determines display order in user interfaces and must be
    non-negative.
    """

    code: str = Field(pattern=r"^[A-Z]{3}$")
    key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str
    description: str
    sort_order: int = Field(ge=0)


ISSUE_TYPES: list[IssueTypeSeed] = [
    IssueTypeSeed(
        code="AMB",
        key="ambiguity",
        label="Ambiguity",
        description="Unclear or imprecise requirement wording.",
        sort_order=10,
    ),
    IssueTypeSeed(
        code="GAP",
        key="missing_information",
        label="Missing Information",
        description="A required detail has not yet been captured.",
        sort_order=20,
    ),
    IssueTypeSeed(
        code="CNF",
        key="conflict",
        label="Conflict",
        description="Two or more requirements contradict each other.",
        sort_order=30,
    ),
    IssueTypeSeed(
        code="RSK",
        key="risk",
        label="Risk",
        description="A potential threat to scope, schedule, quality, or compliance.",
        sort_order=40,
    ),
    IssueTypeSeed(
        code="BLK",
        key="blocker",
        label="Blocker",
        description="An obstacle preventing further progress.",
        sort_order=50,
    ),
    IssueTypeSeed(
        code="QST",
        key="stakeholder_question",
        label="Stakeholder Question",
        description="A question awaiting a stakeholder response.",
        sort_order=60,
    ),
    IssueTypeSeed(
        code="DEC",
        key="decision_needed",
        label="Decision Needed",
        description="A decision is required before work can proceed.",
        sort_order=70,
    ),
    IssueTypeSeed(
        code="EVD",
        key="evidence_needed",
        label="Evidence Needed",
        description="Supporting evidence must be gathered or attached.",
        sort_order=80,
    ),
    IssueTypeSeed(
        code="VAL",
        key="validation_issue",
        label="Validation Issue",
        description="A requirement fails validation against acceptance criteria.",
        sort_order=90,
    ),
    IssueTypeSeed(
        code="CHG",
        key="change_request",
        label="Change Request",
        description="A formal request to alter an existing requirement.",
        sort_order=100,
    ),
    IssueTypeSeed(
        code="MSC",
        key="miscellaneous",
        label="Miscellaneous",
        description="Other issue type that does not fit established categories.",
        sort_order=110,
    ),
]


__all__ = ["ISSUE_TYPES", "IssueTypeSeed"]
