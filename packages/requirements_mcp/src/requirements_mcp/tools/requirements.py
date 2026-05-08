"""MCP tool handlers for the requirement subsystem.

Each handler takes a :class:`sessionmaker` factory (so the tool layer
owns the session boundary, leaving the service layer transaction-free)
and the validated Pydantic input model. The pattern is identical
across handlers:

1. Open a session with ``with session_factory() as session:``.
2. Call the matching service function.
3. Convert the ORM result(s) into Pydantic output models with
   ``Model.model_validate(orm_obj)`` (works because the schemas set
   ``from_attributes=True``).
4. Commit before returning so callers observe persisted state. Roll
   back on exception by letting the context manager exit.

These handlers are plain functions, not coroutines: the MCP server
module wraps them for stdio dispatch.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from requirements_mcp.schemas.requirements import (
    RequirementChangeOut,
    RequirementCreate,
    RequirementOut,
    RequirementSearchHit,
    RequirementSearchQuery,
    RequirementStatusOut,
    RequirementTypeOut,
    RequirementUpdate,
)
from requirements_mcp.services import requirements as svc

__all__ = [
    "create_requirement",
    "get_requirement",
    "list_requirement_changes",
    "list_requirement_statuses",
    "list_requirement_types",
    "search_requirements",
    "update_requirement",
]


def _open(session_factory: sessionmaker[Session]) -> Session:
    """Open a new session from ``session_factory``.

    Args:
        session_factory: Factory configured by
            :func:`requirements_mcp.db.engine.make_session_factory`.

    Returns:
        A fresh :class:`Session` instance ready to be used as a context
        manager.
    """
    return session_factory()


def create_requirement(
    session_factory: sessionmaker[Session],
    payload: RequirementCreate,
) -> RequirementOut:
    """Create a new requirement and return its full state.

    Wraps :func:`requirements_mcp.services.requirements.create_requirement`
    in a session that commits on success.

    Args:
        session_factory: Active session factory bound to the target DB.
        payload: Validated input.

    Returns:
        The newly created requirement as a :class:`RequirementOut`.
    """
    with _open(session_factory) as session:
        requirement = svc.create_requirement(session, payload)
        session.commit()
        return RequirementOut.model_validate(requirement)


def update_requirement(
    session_factory: sessionmaker[Session],
    requirement_id: str,
    payload: RequirementUpdate,
) -> RequirementOut:
    """Apply an update to an existing requirement.

    Args:
        session_factory: Active session factory.
        requirement_id: Primary key to mutate.
        payload: Validated update model.

    Returns:
        The post-update requirement state. Note that for a no-op update
        the returned ``version`` is unchanged and the audit log is not
        appended to.

    Raises:
        requirements_mcp.services.requirements.RequirementNotFoundError:
            If the id is unknown.
    """
    with _open(session_factory) as session:
        requirement = svc.update_requirement(session, requirement_id, payload)
        session.commit()
        return RequirementOut.model_validate(requirement)


def get_requirement(
    session_factory: sessionmaker[Session],
    requirement_id: str,
) -> RequirementOut | None:
    """Return one requirement by id, or ``None`` if absent.

    Args:
        session_factory: Active session factory.
        requirement_id: Primary key to look up.

    Returns:
        :class:`RequirementOut` for the matching row, or ``None``.
    """
    with _open(session_factory) as session:
        requirement = svc.get_requirement(session, requirement_id)
        if requirement is None:
            return None
        return RequirementOut.model_validate(requirement)


def search_requirements(
    session_factory: sessionmaker[Session],
    query: RequirementSearchQuery,
) -> list[RequirementSearchHit]:
    """Search requirements by free text and code filters.

    Args:
        session_factory: Active session factory.
        query: Validated search payload.

    Returns:
        A list of compact :class:`RequirementSearchHit` projections,
        ordered most-recently-updated first.
    """
    with _open(session_factory) as session:
        rows = svc.search_requirements(session, query)
        return [RequirementSearchHit.model_validate(row) for row in rows]


def list_requirement_changes(
    session_factory: sessionmaker[Session],
    requirement_id: str,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[RequirementChangeOut]:
    """Return the audit log for one requirement, oldest first.

    Args:
        session_factory: Active session factory.
        requirement_id: Primary key whose history is requested.
        limit: Maximum number of rows to return.
        offset: Number of rows to skip.

    Returns:
        A list of :class:`RequirementChangeOut` rows, ordered by date
        ascending.

    Raises:
        requirements_mcp.services.requirements.RequirementNotFoundError:
            If ``requirement_id`` does not exist.
    """
    with _open(session_factory) as session:
        rows = svc.list_requirement_changes(
            session, requirement_id, limit=limit, offset=offset
        )
        return [RequirementChangeOut.model_validate(row) for row in rows]


def list_requirement_statuses(
    session_factory: sessionmaker[Session],
) -> list[RequirementStatusOut]:
    """Return all requirement statuses ordered by ``sort_order``.

    Args:
        session_factory: Active session factory.

    Returns:
        A list of :class:`RequirementStatusOut` rows.
    """
    with _open(session_factory) as session:
        rows = svc.list_requirement_statuses(session)
        return [RequirementStatusOut.model_validate(row) for row in rows]


def list_requirement_types(
    session_factory: sessionmaker[Session],
) -> list[RequirementTypeOut]:
    """Return all requirement types ordered by ``sort_order``.

    Args:
        session_factory: Active session factory.

    Returns:
        A list of :class:`RequirementTypeOut` rows.
    """
    with _open(session_factory) as session:
        rows = svc.list_requirement_types(session)
        return [RequirementTypeOut.model_validate(row) for row in rows]
