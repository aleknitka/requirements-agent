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
    ISSUE_DIFFABLE_FIELDS,
    REQUIREMENT_DIFFABLE_FIELDS,
    REQUIREMENT_JSON_LIST_FIELDS,
    REQUIREMENT_SCALAR_FIELDS,
    compute_diff,
)
from requirements_mcp.services.issues import (
    IssueNotFoundError,
    RequirementIssueLinkAlreadyExistsError,
    RequirementIssueLinkNotFoundError,
    add_issue_update,
    create_issue,
    get_issue,
    link_issue_to_requirement,
    list_blocking_issues,
    list_issue_priorities,
    list_issue_statuses,
    list_issue_types,
    list_issue_updates,
    list_open_issues,
    search_issues,
    unlink_issue_from_requirement,
    update_issue,
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
    "ISSUE_DIFFABLE_FIELDS",
    "IssueNotFoundError",
    "REQUIREMENT_DIFFABLE_FIELDS",
    "REQUIREMENT_JSON_LIST_FIELDS",
    "REQUIREMENT_SCALAR_FIELDS",
    "RequirementIssueLinkAlreadyExistsError",
    "RequirementIssueLinkNotFoundError",
    "RequirementNotFoundError",
    "add_issue_update",
    "compute_diff",
    "create_issue",
    "create_requirement",
    "get_issue",
    "get_requirement",
    "link_issue_to_requirement",
    "list_blocking_issues",
    "list_issue_priorities",
    "list_issue_statuses",
    "list_issue_types",
    "list_issue_updates",
    "list_open_issues",
    "list_requirement_changes",
    "list_requirement_statuses",
    "list_requirement_types",
    "search_issues",
    "search_requirements",
    "unlink_issue_from_requirement",
    "update_issue",
    "update_requirement",
]
