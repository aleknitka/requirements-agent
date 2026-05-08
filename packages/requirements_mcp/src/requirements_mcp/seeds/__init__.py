"""Pydantic seed models and controlled-vocabulary data.

The seed system is the source of truth for every controlled-vocabulary
table in the schema (requirement statuses and types; issue statuses,
types, and priorities). For each table there is a small Pydantic model
(extending :class:`SeedBase`) and a frozen list of seed instances
declared in code so the data is reviewed via pull request rather than
edited live in the database.

When the database is initialised — either from the
``requirements-db-init`` CLI or from a Python call to
:func:`requirements_mcp.db.init.init_db` — the
:func:`apply_seeds` helper walks every seed list and inserts any rows
whose primary key is missing. Existing rows are left untouched, so
locally-edited descriptions or display orders survive subsequent
init runs.
"""

from requirements_mcp.seeds._base import SeedBase
from requirements_mcp.seeds.apply import SeedReport, apply_seeds
from requirements_mcp.seeds.issue_priorities import (
    ISSUE_PRIORITIES,
    IssuePrioritySeed,
)
from requirements_mcp.seeds.issue_statuses import ISSUE_STATUSES, IssueStatusSeed
from requirements_mcp.seeds.issue_types import ISSUE_TYPES, IssueTypeSeed
from requirements_mcp.seeds.requirement_statuses import (
    REQUIREMENT_STATUSES,
    RequirementStatusSeed,
)
from requirements_mcp.seeds.requirement_types import (
    REQUIREMENT_TYPES,
    RequirementTypeSeed,
)

__all__ = [
    "ISSUE_PRIORITIES",
    "ISSUE_STATUSES",
    "ISSUE_TYPES",
    "IssuePrioritySeed",
    "IssueStatusSeed",
    "IssueTypeSeed",
    "REQUIREMENT_STATUSES",
    "REQUIREMENT_TYPES",
    "RequirementStatusSeed",
    "RequirementTypeSeed",
    "SeedBase",
    "SeedReport",
    "apply_seeds",
]
