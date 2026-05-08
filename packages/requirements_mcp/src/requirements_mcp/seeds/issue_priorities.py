"""Seed data for the ``issue_priorities`` table.

Defines the four priority bands an issue can be assigned: ``LOW``,
``MED``, ``HIG``, and ``CRT`` (critical). Each entry carries a
``severity_order`` weight (higher means more severe) used for filters
and sort-by-severity queries, in addition to ``sort_order`` for
display.
"""

from __future__ import annotations

from pydantic import Field

from requirements_mcp.seeds._base import SeedBase


class IssuePrioritySeed(SeedBase):
    """Validated row template for an issue priority band.

    The ``code`` is constrained to exactly three uppercase ASCII
    letters. ``severity_order`` is the comparable severity weight
    (higher = more severe) and must be non-negative. ``sort_order``
    governs display order in user interfaces.
    """

    code: str = Field(pattern=r"^[A-Z]{3}$")
    label: str
    description: str
    severity_order: int = Field(ge=0)
    sort_order: int = Field(ge=0)


ISSUE_PRIORITIES: list[IssuePrioritySeed] = [
    IssuePrioritySeed(
        code="LOW",
        label="Low",
        description="Minor concern; address when convenient.",
        severity_order=10,
        sort_order=10,
    ),
    IssuePrioritySeed(
        code="MED",
        label="Medium",
        description="Noticeable concern; address in normal course of work.",
        severity_order=20,
        sort_order=20,
    ),
    IssuePrioritySeed(
        code="HIG",
        label="High",
        description="Significant concern; address promptly.",
        severity_order=30,
        sort_order=30,
    ),
    IssuePrioritySeed(
        code="CRT",
        label="Critical",
        description="Severe concern; address immediately.",
        severity_order=40,
        sort_order=40,
    ),
]


__all__ = ["ISSUE_PRIORITIES", "IssuePrioritySeed"]
