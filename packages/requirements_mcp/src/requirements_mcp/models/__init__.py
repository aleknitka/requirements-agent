"""SQLAlchemy ORM models grouped by domain.

The package is organised so each module owns one cohesive concern:

- :mod:`requirements_mcp.models.requirement_meta` defines the controlled
  vocabularies that classify a requirement (status and type).
- :mod:`requirements_mcp.models.requirement` defines the requirement
  itself and its append-only audit log.
- :mod:`requirements_mcp.models.issue_meta` defines the controlled
  vocabularies that classify an issue (status, type, priority).
- :mod:`requirements_mcp.models.issue` defines the issue, its update
  log, and the link table joining issues to requirements.
- :mod:`requirements_mcp.models.types` defines reusable column types
  shared across the schema.

Importing this package as a side effect registers every ORM class with
``Base.metadata`` so that ``Base.metadata.create_all`` and Alembic
autogeneration see the full schema.
"""

from requirements_mcp.models.issue import (
    Issue,
    IssueUpdate,
    RequirementIssueLink,
)
from requirements_mcp.models.issue_meta import (
    IssuePriority,
    IssueStatus,
    IssueType,
)
from requirements_mcp.models.requirement import Requirement, RequirementChange
from requirements_mcp.models.requirement_meta import (
    RequirementStatus,
    RequirementType,
)
from requirements_mcp.models.types import JSONList

__all__ = [
    "Issue",
    "IssuePriority",
    "IssueStatus",
    "IssueType",
    "IssueUpdate",
    "JSONList",
    "Requirement",
    "RequirementChange",
    "RequirementIssueLink",
    "RequirementStatus",
    "RequirementType",
]
