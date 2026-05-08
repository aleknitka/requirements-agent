"""Pydantic schemas for the requirement MCP tools.

Three model families live here:

* **Input models** (``RequirementCreate``, ``RequirementUpdate``,
  ``RequirementSearchQuery``) — validate incoming MCP tool arguments.
  ``extra="forbid"`` is set on each so unknown keys fail loud.
* **Output models** (``RequirementOut``, ``RequirementChangeOut``,
  ``RequirementStatusOut``, ``RequirementTypeOut``,
  ``RequirementSearchHit``) — Pydantic representations of ORM rows.
  Constructed via ``Model.model_validate(orm_obj)`` thanks to
  ``from_attributes=True``.
* No mutation logic lives in this module: schemas are pure data carriers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# These literal types must stay in lock-step with the seed lists in
# :mod:`requirements_mcp.seeds.requirement_types` and
# :mod:`requirements_mcp.seeds.requirement_statuses`. A test in
# ``tests/test_schemas_requirements.py`` enforces the synchronisation so
# adding a new code to a seed list without also updating the Literal here
# fails CI.
RequirementTypeCode = Literal[
    "FUN",
    "NFR",
    "BUS",
    "STK",
    "USR",
    "SYS",
    "INT",
    "DAT",
    "SEC",
    "PRV",
    "COM",
    "PER",
    "AVL",
    "USB",
    "OPS",
    "AIM",
    "REP",
    "CNS",
    "TRN",
]
"""Closed set of requirement type codes accepted by the MCP tool inputs."""

RequirementStatusCode = Literal[
    "draft",
    "in_review",
    "needs_clarification",
    "approved",
    "in_progress",
    "implemented",
    "verified",
    "rejected",
    "deferred",
    "deprecated",
    "removed",
]
"""Closed set of requirement status codes accepted by the MCP tool inputs."""

__all__ = [
    "RequirementChangeOut",
    "RequirementCreate",
    "RequirementOut",
    "RequirementSearchHit",
    "RequirementSearchQuery",
    "RequirementStatusCode",
    "RequirementStatusOut",
    "RequirementTypeCode",
    "RequirementTypeOut",
    "RequirementUpdate",
]


class RequirementCreate(BaseModel):
    """Input payload for ``create_requirement``.

    Every list-shaped field defaults to an empty list so callers may omit
    them when the requirement does not yet have, e.g., explicit
    preconditions. The default ``status_code`` is ``"draft"`` to match
    the lifecycle entry state.
    """

    title: str = Field(min_length=1, max_length=255)
    requirement_statement: str = Field(min_length=1)
    type_code: RequirementTypeCode
    status_code: RequirementStatusCode = "draft"
    author: str = Field(min_length=1, max_length=255)
    extended_description: str = ""
    users: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    business_logic: list[str] = Field(default_factory=list)
    exception_handling: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class RequirementUpdate(BaseModel):
    """Input payload for ``update_requirement``.

    Every diffable field is optional; only fields explicitly supplied by
    the caller participate in the diff. Two non-diffable fields are
    required on every call so the audit row is always self-explanatory:
    ``author`` records who is making the change and
    ``change_description`` is a short commit-message-style note about
    why. The audit row is only written when at least one diffable field
    actually changes; for a no-op update the caller's
    ``change_description`` is discarded.
    """

    author: str = Field(min_length=1, max_length=255)
    change_description: str = Field(min_length=1)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    requirement_statement: str | None = Field(default=None, min_length=1)
    type_code: RequirementTypeCode | None = None
    status_code: RequirementStatusCode | None = None
    extended_description: str | None = None
    users: list[str] | None = None
    triggers: list[str] | None = None
    preconditions: list[str] | None = None
    postconditions: list[str] | None = None
    inputs: list[str] | None = None
    outputs: list[str] | None = None
    business_logic: list[str] | None = None
    exception_handling: list[str] | None = None
    acceptance_criteria: list[str] | None = None

    model_config = ConfigDict(extra="forbid")


class RequirementOut(BaseModel):
    """Read model returned by ``create_requirement``, ``update_requirement``, and ``get_requirement``."""

    id: str
    title: str
    requirement_statement: str
    type_code: str
    status_code: str
    version: int
    author: str
    date_created: datetime
    date_updated: datetime
    extended_description: str
    users: list[str]
    triggers: list[str]
    preconditions: list[str]
    postconditions: list[str]
    inputs: list[str]
    outputs: list[str]
    business_logic: list[str]
    exception_handling: list[str]
    acceptance_criteria: list[str]

    model_config = ConfigDict(from_attributes=True)


class RequirementChangeOut(BaseModel):
    """Read model for one row of the requirement audit log."""

    id: str
    requirement_id: str
    change_description: str
    diff: dict[str, Any]
    author: str
    date: datetime

    model_config = ConfigDict(from_attributes=True)


class RequirementStatusOut(BaseModel):
    """Read model for a requirement status row."""

    code: str
    label: str
    description: str
    is_active: bool
    is_terminal: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class RequirementTypeOut(BaseModel):
    """Read model for a requirement type row."""

    code: str
    key: str
    label: str
    description: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class RequirementSearchQuery(BaseModel):
    """Input payload for ``search_requirements``.

    The ``query`` string is whitespace-tokenised; every token must be
    present (case-insensitively) in at least one of the searched
    columns. ``status_codes`` and ``type_codes`` apply as OR-within /
    AND-between filters, so ``status_codes=["draft", "in_review"]``
    selects requirements whose status is either of those.
    """

    query: str = ""
    status_codes: list[str] | None = None
    type_codes: list[str] | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(extra="forbid")


class RequirementSearchHit(BaseModel):
    """Compact projection returned by ``search_requirements``.

    Lighter than :class:`RequirementOut` because search results often
    serve as picker lists; full detail is fetched separately via
    ``get_requirement``.
    """

    id: str
    title: str
    type_code: str
    status_code: str
    version: int
    date_updated: datetime

    model_config = ConfigDict(from_attributes=True)
