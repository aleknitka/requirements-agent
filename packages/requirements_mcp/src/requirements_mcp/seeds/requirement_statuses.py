"""Seed data for the ``requirement_statuses`` table.

Defines the lifecycle states a requirement can occupy as it moves from
initial capture (``draft``) through review and approval, into
implementation, and finally to a verified, rejected, deferred,
deprecated, or removed terminal state. The list ordering is reflected
in the ``sort_order`` column.
"""

from __future__ import annotations

from pydantic import Field

from requirements_mcp.seeds._base import SeedBase


class RequirementStatusSeed(SeedBase):
    """Validated row template for a requirement status.

    The ``code`` is constrained to a lowercase identifier (letters,
    digits, underscores) so it is safe to embed in URLs and JSON
    payloads. ``is_active`` flags whether the status is part of the
    current authoring flow versus an archival or retired state;
    ``is_terminal`` flags states from which a requirement does not
    transition further. ``sort_order`` determines display order in user
    interfaces and must be non-negative.
    """

    code: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str
    description: str
    is_active: bool = True
    is_terminal: bool = False
    sort_order: int = Field(ge=0)


REQUIREMENT_STATUSES: list[RequirementStatusSeed] = [
    RequirementStatusSeed(
        code="draft",
        label="Draft",
        description="Captured but not yet reviewed.",
        is_active=True,
        is_terminal=False,
        sort_order=10,
    ),
    RequirementStatusSeed(
        code="in_review",
        label="In Review",
        description="Being reviewed by stakeholders.",
        is_active=True,
        is_terminal=False,
        sort_order=20,
    ),
    RequirementStatusSeed(
        code="needs_clarification",
        label="Needs Clarification",
        description=(
            "Requirement is incomplete, ambiguous, or awaiting more information."
        ),
        is_active=True,
        is_terminal=False,
        sort_order=30,
    ),
    RequirementStatusSeed(
        code="approved",
        label="Approved",
        description="Accepted and ready for implementation.",
        is_active=True,
        is_terminal=False,
        sort_order=40,
    ),
    RequirementStatusSeed(
        code="in_progress",
        label="In Progress",
        description="Currently being implemented.",
        is_active=True,
        is_terminal=False,
        sort_order=50,
    ),
    RequirementStatusSeed(
        code="implemented",
        label="Implemented",
        description="Implemented but not yet formally verified.",
        is_active=True,
        is_terminal=False,
        sort_order=60,
    ),
    RequirementStatusSeed(
        code="verified",
        label="Verified",
        description=("Verified against acceptance criteria or formally accepted."),
        is_active=False,
        is_terminal=True,
        sort_order=70,
    ),
    RequirementStatusSeed(
        code="rejected",
        label="Rejected",
        description="Explicitly rejected by stakeholders.",
        is_active=False,
        is_terminal=True,
        sort_order=80,
    ),
    RequirementStatusSeed(
        code="deferred",
        label="Deferred",
        description="Valid requirement postponed for later consideration.",
        is_active=False,
        is_terminal=False,
        sort_order=90,
    ),
    RequirementStatusSeed(
        code="deprecated",
        label="Deprecated",
        description=(
            "Previously valid but no longer recommended for use or implementation."
        ),
        is_active=False,
        is_terminal=True,
        sort_order=100,
    ),
    RequirementStatusSeed(
        code="removed",
        label="Removed",
        description=("Removed from active scope while preserving audit history."),
        is_active=False,
        is_terminal=True,
        sort_order=110,
    ),
]


__all__ = ["REQUIREMENT_STATUSES", "RequirementStatusSeed"]
