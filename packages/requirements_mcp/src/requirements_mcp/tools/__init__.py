"""MCP tool handlers for the requirements MCP package.

Tools are thin adapters around :mod:`requirements_mcp.services`:
validate the input via the matching Pydantic model, open a session,
call the service, convert the ORM result back into a Pydantic output
model, commit (or roll back), and return. The MCP server module wires
these handlers into a stdio transport.
"""

from requirements_mcp.tools.issues import (
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
from requirements_mcp.tools.reports import get_full_report
from requirements_mcp.tools.requirements import (
    create_requirement,
    get_requirement,
    list_requirement_changes,
    list_requirement_statuses,
    list_requirement_types,
    search_requirements,
    update_requirement,
)

__all__ = [
    "add_issue_update",
    "create_issue",
    "create_requirement",
    "get_full_report",
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
