"""Idempotent application of every controlled-vocabulary seed list.

The single public entry point is :func:`apply_seeds`. It walks each
seed list in turn, inserts any rows whose primary key is missing from
the corresponding metadata table, and leaves existing rows alone. The
caller is responsible for committing the session, which keeps seeding
composable with other write operations performed in the same
transaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from sqlalchemy.orm import Session

from requirements_mcp.db.base import Base
from requirements_mcp.models.issue_meta import (
    IssuePriority,
    IssueStatus,
    IssueType,
)
from requirements_mcp.models.requirement_meta import (
    RequirementStatus,
    RequirementType,
)
from requirements_mcp.seeds._base import SeedBase
from requirements_mcp.seeds.issue_priorities import ISSUE_PRIORITIES
from requirements_mcp.seeds.issue_statuses import ISSUE_STATUSES
from requirements_mcp.seeds.issue_types import ISSUE_TYPES
from requirements_mcp.seeds.requirement_statuses import REQUIREMENT_STATUSES
from requirements_mcp.seeds.requirement_types import REQUIREMENT_TYPES


@dataclass
class SeedReport:
    """Per-table summary of a single :func:`apply_seeds` invocation.

    Both fields map a SQLAlchemy ``__tablename__`` (for example
    ``"requirement_statuses"``) to a count. ``inserted`` records how
    many rows were newly added because their primary key was not
    present; ``skipped`` records how many rows were left untouched
    because they already existed. The CLI prints these counts after
    initialisation; tests assert on them to verify idempotence.
    """

    inserted: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, int] = field(default_factory=dict)


def _upsert(
    session: Session,
    model: type[Base],
    seeds: Iterable[SeedBase],
    report: SeedReport,
) -> None:
    """Insert any missing seed rows for one metadata table.

    Each seed instance is matched against the database by its ``code``
    primary key. Rows that already exist are left exactly as they are
    on disk, so locally-edited descriptions or display orders are not
    silently reverted on subsequent invocations.

    Args:
        session: Active SQLAlchemy session. The function neither commits
            nor rolls back; the caller is responsible for transaction
            boundaries.
        model: ORM class corresponding to the table being seeded. Must
            expose a primary-key ``code`` column compatible with
            :meth:`Session.get`.
        seeds: Iterable of Pydantic seed instances to upsert. Each
            instance must have a ``code`` attribute.
        report: :class:`SeedReport` accumulator updated in place with
            inserted and skipped counts for ``model.__tablename__``.
    """
    table_name = model.__tablename__
    inserted = 0
    skipped = 0
    for seed in seeds:
        data = seed.model_dump()
        existing = session.get(model, data["code"])
        if existing is None:
            session.add(model(**data))
            inserted += 1
        else:
            skipped += 1
    report.inserted[table_name] = inserted
    report.skipped[table_name] = skipped


def apply_seeds(session: Session) -> SeedReport:
    """Upsert every controlled-vocabulary seed list into its table.

    Walks the seed lists for requirement statuses, requirement types,
    issue statuses, issue types, and issue priorities in that order.
    For each list, rows whose primary key is missing from the
    corresponding table are inserted; rows already present are left
    untouched. Calling the function repeatedly is safe and produces no
    spurious updates or duplicate rows.

    The function does not commit. The caller decides when to flush —
    typically immediately after the call in standalone initialisation,
    or as part of a larger transaction in services that combine seeding
    with other operations.

    Args:
        session: Active SQLAlchemy session bound to the target
            database. Must have the schema already created (for example
            by :func:`requirements_mcp.db.init.init_db`).

    Returns:
        A :class:`SeedReport` whose ``inserted`` and ``skipped`` maps
        describe what changed per table. Useful for logging, CLI
        output, and test assertions on idempotence.
    """
    report = SeedReport()
    _upsert(session, RequirementStatus, REQUIREMENT_STATUSES, report)
    _upsert(session, RequirementType, REQUIREMENT_TYPES, report)
    _upsert(session, IssueStatus, ISSUE_STATUSES, report)
    _upsert(session, IssueType, ISSUE_TYPES, report)
    _upsert(session, IssuePriority, ISSUE_PRIORITIES, report)
    return report


__all__ = ["SeedReport", "apply_seeds"]
