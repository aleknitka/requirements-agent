"""ORM models for issue-related controlled vocabularies.

These tables hold the lookup data that classifies issues raised against
requirements: lifecycle status (``open``, ``triaged``, ``resolved``,
...), category (``ambiguity``, ``risk``, ``decision_needed``, ...), and
priority (``LOW``..``CRT``). The corresponding seed lists in
:mod:`requirements_mcp.seeds` are the source of truth and are reconciled
via :func:`requirements_mcp.seeds.apply.apply_seeds`.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from requirements_mcp.db.base import Base


class IssueStatus(Base):
    """Lifecycle status assignable to an issue.

    The natural primary key is the lowercase ``code`` (for example
    ``"open"`` or ``"waiting_for_stakeholder"``), which is referenced by
    ``issues.status_code``. ``is_terminal`` marks states (such as
    ``"closed"`` or ``"cancelled"``) from which the issue cannot
    transition further without being reopened. ``sort_order`` controls
    display order in user interfaces.
    """

    __tablename__ = "issue_statuses"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class IssueType(Base):
    """Classification of what an issue represents.

    The natural primary key is the three-letter uppercase ``code`` (for
    example ``"AMB"`` for an ambiguity, ``"GAP"`` for missing
    information, ``"RSK"`` for a risk). The ``key`` field provides a
    readable slug (``"ambiguity"``, ``"missing_information"``,
    ``"risk"``) for use in URLs and user interfaces.
    """

    __tablename__ = "issue_types"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class IssuePriority(Base):
    """Priority level assignable to an issue.

    The natural primary key is the three-letter uppercase ``code``
    (``"LOW"``, ``"MED"``, ``"HIG"``, ``"CRT"``), referenced by
    ``issues.priority_code``. Two ordering attributes are kept
    separately so that severity comparisons and display ordering can
    diverge if needed:

    * ``severity_order`` is the comparable severity weight; higher
      values denote more severe priorities and are intended for use in
      filters and sort-by-severity queries.
    * ``sort_order`` controls human-facing display order; by default it
      matches ``severity_order`` but can be tuned independently.
    """

    __tablename__ = "issue_priorities"

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    severity_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


__all__ = ["IssuePriority", "IssueStatus", "IssueType"]
