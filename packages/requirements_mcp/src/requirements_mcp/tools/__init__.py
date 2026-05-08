"""MCP tool handlers for the requirements MCP package.

Tools are thin adapters around :mod:`requirements_mcp.services`:
validate the input via the matching Pydantic model, open a session,
call the service, convert the ORM result back into a Pydantic output
model, commit (or roll back), and return. The MCP server module wires
these handlers into a stdio transport.
"""

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
    "create_requirement",
    "get_requirement",
    "list_requirement_changes",
    "list_requirement_statuses",
    "list_requirement_types",
    "search_requirements",
    "update_requirement",
]
