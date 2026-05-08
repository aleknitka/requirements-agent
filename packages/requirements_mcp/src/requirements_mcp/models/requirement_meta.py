"""ORM models for requirement-related controlled vocabularies.

These tables hold the small, mostly-static lookup data that classifies
each requirement: its lifecycle status (``draft``, ``approved``,
``verified``, ...) and its kind (``functional``, ``security``,
``compliance``, ...). The corresponding seed lists in
:mod:`requirements_mcp.seeds` are the source of truth for the rows in
these tables; the :func:`requirements_mcp.seeds.apply.apply_seeds`
helper keeps them in sync.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from requirements_mcp.db.base import Base


class RequirementStatus(Base):
    """Lifecycle status assignable to a requirement.

    The natural primary key is the lowercase ``code`` (for example
    ``"draft"`` or ``"in_review"``), which is referenced by
    ``requirements.status_code``. The ``is_terminal`` flag distinguishes
    states from which a requirement cannot transition further (such as
    ``"verified"`` or ``"rejected"``); the ``is_active`` flag indicates
    whether a status is still part of the normal authoring flow versus
    a retired or archival state. ``sort_order`` controls display order
    in user interfaces.
    """

    __tablename__ = "requirement_statuses"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class RequirementType(Base):
    """Classification assignable to a requirement.

    The natural primary key is the three-letter uppercase ``code`` (for
    example ``"FUN"`` for functional or ``"SEC"`` for security), which
    is referenced by ``requirements.type_code``. The ``key`` field
    stores a human-readable slug (``"functional"``, ``"security"``)
    intended for use in URLs, search filters, and user interfaces where
    the terse three-letter code would be unfriendly.
    """

    __tablename__ = "requirement_types"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


__all__ = ["RequirementStatus", "RequirementType"]
