"""Service layer for the requirements MCP package.

Service functions are pure SQLAlchemy business logic: they accept an
active :class:`sqlalchemy.orm.Session`, perform their work, and let the
caller manage transaction boundaries (commit / rollback). This mirrors
how :func:`requirements_mcp.seeds.apply.apply_seeds` is structured and
keeps the service layer trivially testable.

The MCP tool layer in :mod:`requirements_mcp.tools` is a thin wrapper
around these services that adds Pydantic input validation, output
serialisation, and transaction management around each call.
"""

from requirements_mcp.services.diff import (
    DIFFABLE_FIELDS,
    JSON_LIST_FIELDS,
    SCALAR_FIELDS,
    compute_diff,
)
from requirements_mcp.services.requirements import (
    RequirementNotFoundError,
    create_requirement,
    get_requirement,
    list_requirement_changes,
    list_requirement_statuses,
    list_requirement_types,
    search_requirements,
    update_requirement,
)

__all__ = [
    "DIFFABLE_FIELDS",
    "JSON_LIST_FIELDS",
    "RequirementNotFoundError",
    "SCALAR_FIELDS",
    "compute_diff",
    "create_requirement",
    "get_requirement",
    "list_requirement_changes",
    "list_requirement_statuses",
    "list_requirement_types",
    "search_requirements",
    "update_requirement",
]
