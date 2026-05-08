"""Service functions for the requirement subsystem.

Each function in this module accepts an active SQLAlchemy
:class:`Session`, performs its work, and **does not commit** — the
caller (the MCP tool layer, the CLI, or a test fixture) owns the
transaction boundary. This mirrors the
:func:`requirements_mcp.seeds.apply.apply_seeds` pattern from Phase 1.

The hard invariant enforced here: every successful
:func:`create_requirement` and :func:`update_requirement` call inserts a
matching row in ``requirements_changes`` with a structured JSON diff,
in the same unit of work as the mutation itself. There is no supported
path that mutates a requirement without producing the audit row.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from loguru import logger
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from requirements_mcp.models import (
    Requirement,
    RequirementChange,
    RequirementStatus,
    RequirementType,
)
from requirements_mcp.schemas.requirements import (
    RequirementCreate,
    RequirementSearchQuery,
    RequirementUpdate,
)
from requirements_mcp.services.diff import (
    REQUIREMENT_DIFFABLE_FIELDS,
    compute_diff,
)

__all__ = [
    "RequirementNotFoundError",
    "create_requirement",
    "get_requirement",
    "list_requirement_changes",
    "list_requirement_statuses",
    "list_requirement_types",
    "search_requirements",
    "update_requirement",
]


class RequirementNotFoundError(LookupError):
    """Raised when an operation references a requirement id that does not exist."""


_SEARCHABLE_TEXT_COLUMNS = (
    Requirement.title,
    Requirement.requirement_statement,
    Requirement.extended_description,
)


def create_requirement(
    session: Session,
    payload: RequirementCreate,
) -> Requirement:
    """Insert a new requirement and its initial audit-log row.

    The initial :class:`RequirementChange` row records the creation
    event so that "list every event for this requirement" is a single
    query later. Its ``diff`` is intentionally empty (``{}``) and its
    ``change_description`` is ``"created"``: there is no prior state to
    diff against. ``version`` starts at 1.

    Args:
        session: Active SQLAlchemy session. The caller is responsible
            for committing.
        payload: Validated input model carrying the new requirement's
            fields.

    Returns:
        The newly inserted (but as yet uncommitted) :class:`Requirement`
        instance with attributes populated.
    """
    data = payload.model_dump()
    # Assign the UUID id eagerly so the audit row can reference it without
    # an early ``session.flush()``. Both inserts then happen in the same
    # flush, and FK violations surface at commit time rather than mid-call.
    requirement = Requirement(id=str(uuid.uuid4()), **data)
    session.add(requirement)
    session.add(
        RequirementChange(
            requirement_id=requirement.id,
            change_description="created",
            diff={},
            author=payload.author,
            date=datetime.now(timezone.utc),
        )
    )
    logger.info(
        "Created requirement {} (type={}, status={})",
        requirement.id,
        requirement.type_code,
        requirement.status_code,
    )
    return requirement


def update_requirement(
    session: Session,
    requirement_id: str,
    payload: RequirementUpdate,
) -> Requirement:
    """Apply an update and write the matching audit-log row.

    Steps performed inside the active session:

    1. Load the existing requirement; raise
       :class:`RequirementNotFoundError` if absent.
    2. Filter ``payload`` down to fields the caller explicitly supplied
       (``model_dump(exclude_unset=True)``) and to fields that are
       diffable (excluding bookkeeping fields ``author`` and
       ``change_description``).
    3. Compute the structured diff against the current row state.
    4. If the diff is non-empty: apply the new values, increment
       ``version``, and insert a :class:`RequirementChange` row with
       the diff and the supplied ``change_description``.
    5. If the diff is empty: this is a no-op update. Neither
       ``version`` nor any field is touched, and **no audit row is
       written** — the audit log records change events only.

    Args:
        session: Active SQLAlchemy session. The caller commits.
        requirement_id: Primary key of the requirement to mutate.
        payload: Validated update model. ``author`` is mandatory and
            attributed to the audit row when one is written.

    Returns:
        The mutated requirement (or the unchanged one for a no-op).

    Raises:
        RequirementNotFoundError: If ``requirement_id`` does not exist.
    """
    requirement = session.get(Requirement, requirement_id)
    if requirement is None:
        raise RequirementNotFoundError(requirement_id)

    submitted = payload.model_dump(exclude_unset=True)
    # Drop ``None`` values: every diffable column on Requirement is
    # NOT NULL, so a caller cannot meaningfully clear a field by passing
    # ``None``. Filtering here keeps the service from issuing an INSERT
    # that would only surface as a NOT-NULL IntegrityError at commit.
    updates: dict[str, Any] = {
        field: submitted[field]
        for field in REQUIREMENT_DIFFABLE_FIELDS
        if field in submitted and submitted[field] is not None
    }
    diff = compute_diff(requirement, updates, REQUIREMENT_DIFFABLE_FIELDS)

    if not diff:
        logger.debug(
            "No-op update on requirement {} (no diffable fields changed)",
            requirement.id,
        )
        return requirement

    for field, new_value in updates.items():
        setattr(requirement, field, new_value)
    requirement.version += 1

    session.add(
        RequirementChange(
            requirement_id=requirement.id,
            change_description=payload.change_description,
            diff=diff,
            author=payload.author,
            date=datetime.now(timezone.utc),
        )
    )

    logger.info(
        "Updated requirement {} -> v{} ({} fields changed)",
        requirement.id,
        requirement.version,
        len(diff),
    )
    return requirement


def get_requirement(session: Session, requirement_id: str) -> Requirement | None:
    """Return the requirement with the given id, or ``None`` if missing.

    Args:
        session: Active SQLAlchemy session.
        requirement_id: Primary key to look up.

    Returns:
        The :class:`Requirement` row, or ``None`` if no row matches.
    """
    return session.get(Requirement, requirement_id)


def search_requirements(
    session: Session,
    query: RequirementSearchQuery,
) -> Sequence[Requirement]:
    """Search requirements by free text and optional code filters.

    The free-text ``query`` is whitespace-tokenised. Every token must
    appear (case-insensitively, via SQL ``LIKE``) in at least one of
    the searched columns: ``title``, ``requirement_statement``, or
    ``extended_description``. ``status_codes`` and ``type_codes``
    apply as OR-within / AND-between filters: a result must match one
    of the statuses *and* one of the types when both filters are set.

    Results are ordered by ``date_updated`` descending so the most
    recently touched requirements appear first. Pagination is honoured
    via ``limit`` / ``offset``.

    Note:
        SQLite full-text search (FTS5) is a sensible follow-up for
        higher-quality ranking but adds a virtual table and triggers
        that are out of scope for this iteration. The LIKE-based
        approach is portable across SQLite and PostgreSQL.

    Args:
        session: Active SQLAlchemy session.
        query: Validated search input.

    Returns:
        A sequence of matching :class:`Requirement` rows.
    """
    stmt = select(Requirement)

    tokens = query.query.split()
    for token in tokens:
        like = f"%{token}%"
        stmt = stmt.where(
            or_(*(column.ilike(like) for column in _SEARCHABLE_TEXT_COLUMNS))
        )

    if query.status_codes:
        stmt = stmt.where(Requirement.status_code.in_(query.status_codes))
    if query.type_codes:
        stmt = stmt.where(Requirement.type_code.in_(query.type_codes))

    stmt = (
        stmt.order_by(Requirement.date_updated.desc())
        .limit(query.limit)
        .offset(query.offset)
    )

    rows = session.execute(stmt).scalars().all()
    logger.debug(
        "Searched requirements: {} hits (query={!r}, statuses={}, types={})",
        len(rows),
        query.query,
        query.status_codes,
        query.type_codes,
    )
    return rows


def list_requirement_changes(
    session: Session,
    requirement_id: str,
    *,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[RequirementChange]:
    """Return audit-log rows for one requirement, oldest first.

    Args:
        session: Active SQLAlchemy session.
        requirement_id: Primary key whose history is requested. The
            existence of the requirement is verified so callers cannot
            silently receive an empty list for a typo.
        limit: Maximum number of rows to return.
        offset: Number of rows to skip from the start of the ordered
            sequence.

    Returns:
        A sequence of :class:`RequirementChange` rows ordered by
        ``date`` ascending (creation, then each subsequent edit).

    Raises:
        RequirementNotFoundError: If ``requirement_id`` does not exist.
    """
    if session.get(Requirement, requirement_id) is None:
        raise RequirementNotFoundError(requirement_id)

    stmt = (
        select(RequirementChange)
        .where(RequirementChange.requirement_id == requirement_id)
        .order_by(RequirementChange.date.asc(), RequirementChange.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return session.execute(stmt).scalars().all()


def list_requirement_statuses(session: Session) -> Sequence[RequirementStatus]:
    """Return all requirement statuses ordered by ``sort_order`` ascending.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A sequence of :class:`RequirementStatus` rows.
    """
    stmt = select(RequirementStatus).order_by(RequirementStatus.sort_order.asc())
    return session.execute(stmt).scalars().all()


def list_requirement_types(session: Session) -> Sequence[RequirementType]:
    """Return all requirement types ordered by ``sort_order`` ascending.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        A sequence of :class:`RequirementType` rows.
    """
    stmt = select(RequirementType).order_by(RequirementType.sort_order.asc())
    return session.execute(stmt).scalars().all()
