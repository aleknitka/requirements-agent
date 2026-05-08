"""Seed data for the ``issue_statuses`` table.

Defines the lifecycle of an issue from initial capture (``open``)
through triage, clarification, stakeholder communication, active work,
and resolution. ``resolved`` indicates that the issue has been
addressed but may still warrant follow-up; ``closed`` indicates that no
further action is required. ``cancelled`` is used when an issue is
abandoned without a substantive resolution.
"""

from __future__ import annotations

from pydantic import Field

from requirements_mcp.seeds._base import SeedBase


class IssueStatusSeed(SeedBase):
    """Validated row template for an issue status.

    The ``code`` is a lowercase identifier safe to embed in URLs and
    JSON payloads. ``is_terminal`` marks states from which the issue
    cannot transition further without being reopened. ``sort_order``
    determines display order in user interfaces and must be
    non-negative.
    """

    code: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str
    description: str
    is_terminal: bool = False
    sort_order: int = Field(ge=0)


ISSUE_STATUSES: list[IssueStatusSeed] = [
    IssueStatusSeed(
        code="open",
        label="Open",
        description="Newly raised, not yet triaged.",
        is_terminal=False,
        sort_order=10,
    ),
    IssueStatusSeed(
        code="triaged",
        label="Triaged",
        description="Reviewed and accepted into the backlog.",
        is_terminal=False,
        sort_order=20,
    ),
    IssueStatusSeed(
        code="needs_clarification",
        label="Needs Clarification",
        description="Awaiting additional detail before further action.",
        is_terminal=False,
        sort_order=30,
    ),
    IssueStatusSeed(
        code="waiting_for_stakeholder",
        label="Waiting for Stakeholder",
        description="Pending response or input from a stakeholder.",
        is_terminal=False,
        sort_order=40,
    ),
    IssueStatusSeed(
        code="in_progress",
        label="In Progress",
        description="Actively being worked on.",
        is_terminal=False,
        sort_order=50,
    ),
    IssueStatusSeed(
        code="blocked",
        label="Blocked",
        description="Progress halted by an external dependency or unresolved issue.",
        is_terminal=False,
        sort_order=60,
    ),
    IssueStatusSeed(
        code="resolved",
        label="Resolved",
        description="The agent believes the issue has been addressed.",
        is_terminal=False,
        sort_order=70,
    ),
    IssueStatusSeed(
        code="closed",
        label="Closed",
        description="No further action required.",
        is_terminal=True,
        sort_order=80,
    ),
    IssueStatusSeed(
        code="reopened",
        label="Reopened",
        description="Previously resolved or closed but requires more work.",
        is_terminal=False,
        sort_order=90,
    ),
    IssueStatusSeed(
        code="cancelled",
        label="Cancelled",
        description="Will not be pursued; closed without resolution.",
        is_terminal=True,
        sort_order=100,
    ),
]


__all__ = ["ISSUE_STATUSES", "IssueStatusSeed"]
