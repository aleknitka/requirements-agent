"""ORM models for requirements and their append-only audit log.

A :class:`Requirement` row stores the *current* state of a requirement.
Every meaningful update — a status transition, a wording change, an
addition or removal in one of the structured list fields — must be
accompanied by a :class:`RequirementChange` row in the same transaction.
This pairing is what makes the audit trail trustworthy: there is no
supported path that mutates a requirement without also recording the
diff.

The list-shaped fields (``users``, ``triggers``, ``preconditions``,
``postconditions``, ``inputs``, ``outputs``, ``business_logic``,
``exception_handling``, ``acceptance_criteria``) use the
:class:`requirements_mcp.models.types.JSONList` column type, so they are
stored as JSON arrays but always present as Python lists to application
code.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from requirements_mcp.db.base import Base
from requirements_mcp.models.types import JSONList


def _new_id() -> str:
    """Generate a fresh opaque UUID4 string used as a primary-key value.

    Returns:
        A 36-character UUID4 string. Opaque identifiers are preferred
        over autoincrement integers so that requirement ids can be
        safely shared across environments without collisions and never
        leak ordering or row-count information.
    """
    return str(uuid.uuid4())


class Requirement(Base):
    """The current state of one requirement.

    A requirement carries a free-text title and statement, a foreign-key
    classification (``type_code``, ``status_code``), the originating
    author, monotonically incrementing ``version`` (bumped on each
    update), and a set of structured list fields that capture the
    formal anatomy of the requirement (users, triggers, preconditions,
    and so on).

    The ``changes`` relationship walks the audit log for this
    requirement in chronological order; cascading delete is enabled so
    that removing a requirement also removes its history (used for test
    teardown and explicit ``--reset`` operations).
    """

    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    requirement_statement: Mapped[str] = mapped_column(String, nullable=False)
    type_code: Mapped[str] = mapped_column(
        String(8), ForeignKey("requirement_types.code"), nullable=False, index=True
    )
    status_code: Mapped[str] = mapped_column(
        String(64), ForeignKey("requirement_statuses.code"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    date_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    date_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    extended_description: Mapped[str] = mapped_column(
        String, nullable=False, default=""
    )

    users: Mapped[list[str]] = mapped_column(JSONList, nullable=False, default=list)
    triggers: Mapped[list[str]] = mapped_column(JSONList, nullable=False, default=list)
    preconditions: Mapped[list[str]] = mapped_column(
        JSONList, nullable=False, default=list
    )
    postconditions: Mapped[list[str]] = mapped_column(
        JSONList, nullable=False, default=list
    )
    inputs: Mapped[list[str]] = mapped_column(JSONList, nullable=False, default=list)
    outputs: Mapped[list[str]] = mapped_column(JSONList, nullable=False, default=list)
    business_logic: Mapped[list[str]] = mapped_column(
        JSONList, nullable=False, default=list
    )
    exception_handling: Mapped[list[str]] = mapped_column(
        JSONList, nullable=False, default=list
    )
    acceptance_criteria: Mapped[list[str]] = mapped_column(
        JSONList, nullable=False, default=list
    )

    changes: Mapped[list["RequirementChange"]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan",
        order_by="RequirementChange.date",
    )


class RequirementChange(Base):
    """Append-only audit-log entry for one update to a requirement.

    The ``diff`` column stores a machine-readable JSON object whose keys
    are the field names that changed and whose values are
    ``{"from": <old>, "to": <new>}`` objects. Service-layer code is
    responsible for computing the diff before inserting the row so the
    log faithfully captures what happened, even if multiple fields
    change in one update. The ``change_description`` column carries an
    optional human-readable note (a commit-message-style summary of the
    edit).

    Rows are immutable by convention: services should never update or
    delete a :class:`RequirementChange` after it has been written.
    """

    __tablename__ = "requirements_changes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    requirement_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    change_description: Mapped[str] = mapped_column(String, nullable=False, default="")
    diff: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    requirement: Mapped[Requirement] = relationship(back_populates="changes")


__all__ = ["Requirement", "RequirementChange"]
