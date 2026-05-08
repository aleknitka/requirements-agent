"""ORM models for the issue subsystem.

Issues are operational memory for the system: they capture
ambiguities, missing information, risks, blockers, conflicts,
stakeholder questions, decisions awaiting resolution, evidence gaps,
follow-up tasks, and any other open items the agent or a human user
needs to act on. They are decidedly *not* limited to bugs.

The shape mirrors the requirement subsystem: an :class:`Issue` row
holds the current state, an :class:`IssueUpdate` row records each
meaningful change or operational action (status transition, email
exchange, evidence attachment, resolution proposal), and a
:class:`RequirementIssueLink` row connects an issue to one or more
requirements with a typed relationship.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from requirements_mcp.db.base import Base


def _new_id() -> str:
    """Generate a fresh opaque UUID4 string used as a primary-key value.

    Returns:
        A 36-character UUID4 string. Mirrors the convention used by
        :class:`requirements_mcp.models.requirement.Requirement` so all
        primary keys in the schema look the same.
    """
    return str(uuid.uuid4())


class Issue(Base):
    """The current state of one issue.

    Captures the issue's title and description, its classification
    (``issue_type_code``, ``status_code``, ``priority_code``), the
    optional impact and risk narrative, a proposed resolution if one
    has been formulated, and bookkeeping fields (``owner``,
    ``created_by``, dates).

    The ``updates`` and ``requirement_links`` relationships expose the
    audit log and the cross-reference to requirements, respectively.
    Both cascade on delete so that removing an issue also removes its
    update history and link rows.
    """

    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    issue_type_code: Mapped[str] = mapped_column(
        String(8), ForeignKey("issue_types.code"), nullable=False, index=True
    )
    status_code: Mapped[str] = mapped_column(
        String(64), ForeignKey("issue_statuses.code"), nullable=False, index=True
    )
    priority_code: Mapped[str] = mapped_column(
        String(8), ForeignKey("issue_priorities.code"), nullable=False, index=True
    )
    impact: Mapped[str] = mapped_column(String, nullable=False, default="")
    risk: Mapped[str] = mapped_column(String, nullable=False, default="")
    proposed_resolution: Mapped[str] = mapped_column(String, nullable=False, default="")
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    date_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    date_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    date_closed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    updates: Mapped[list["IssueUpdate"]] = relationship(
        back_populates="issue",
        cascade="all, delete-orphan",
        order_by="IssueUpdate.date",
    )
    requirement_links: Mapped[list["RequirementIssueLink"]] = relationship(
        back_populates="issue",
        cascade="all, delete-orphan",
    )


class IssueUpdate(Base):
    """Append-only audit-log and action-log entry for one issue.

    Each row records something that happened to the issue: a status
    transition, a field edit, an email sent or received, evidence
    attached, a stakeholder question asked, a resolution proposed, or
    the issue itself being resolved or reopened. The ``update_type_code``
    discriminates between these categories. ``description`` is a
    human-readable summary; ``diff`` carries a structured field-level
    change object (same shape as :class:`RequirementChange.diff`) when
    the update represents one. ``action_taken`` and ``action_result``
    capture the operational side of the entry — what the agent or user
    did and what came back.
    """

    __tablename__ = "issue_updates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    issue_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    update_type_code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    diff: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    action_taken: Mapped[str] = mapped_column(String, nullable=False, default="")
    action_result: Mapped[str] = mapped_column(String, nullable=False, default="")
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    issue: Mapped[Issue] = relationship(back_populates="updates")


class RequirementIssueLink(Base):
    """Typed many-to-many association between requirements and issues.

    A single issue can affect any number of requirements, and the
    relationship has meaningful flavour beyond mere association. The
    ``link_type`` column stores that flavour as a short string from the
    set ``{"related", "blocks", "clarifies", "conflicts_with",
    "risk_for", "caused_by", "resolved_by"}``. The set is enforced at
    the service layer rather than via a database CHECK constraint so
    that new link kinds can be added without a schema migration.

    ``rationale`` is a short free-text explanation of why the link
    exists (for instance, ``"this ambiguity affects acceptance
    criterion 3 of REQ-014"``), captured at link-creation time so the
    audit trail stays self-explanatory.
    """

    __tablename__ = "requirement_issues"

    requirement_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        primary_key=True,
    )
    issue_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
    )
    link_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="related"
    )
    rationale: Mapped[str] = mapped_column(String, nullable=False, default="")
    date_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    issue: Mapped[Issue] = relationship(back_populates="requirement_links")


__all__ = ["Issue", "IssueUpdate", "RequirementIssueLink"]
