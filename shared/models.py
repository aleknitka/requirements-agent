"""
models.py — Pydantic validation models.
Nothing here touches the database. Every write goes through these first.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════

class RequirementStatus(str, Enum):
    OPEN        = "open"
    IN_PROGRESS = "in-progress"
    DONE        = "done"
    REJECTED    = "rejected"


class RequirementPriority(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class RequirementType(str, Enum):
    CORE       = "CORE"
    DATA       = "DATA"
    MODEL      = "MODEL"
    INFRA      = "INFRA"
    OPS        = "OPS"
    UX         = "UX"
    COMPLIANCE = "COMPLIANCE"

    @property
    def id_prefix(self) -> str:
        return self.value


class ProjectPhase(str, Enum):
    DISCOVERY   = "discovery"
    DEFINITION  = "definition"
    DEVELOPMENT = "development"
    TESTING     = "testing"
    DEPLOYMENT  = "deployment"
    OPERATIONS  = "operations"
    CLOSED      = "closed"


class MeetingSource(str, Enum):
    TEAMS     = "teams"
    SLACK     = "slack"
    DIRECT    = "direct"
    EMAIL     = "email"
    ZOOM      = "zoom"
    IN_PERSON = "in-person"
    OTHER     = "other"


class DecisionStatus(str, Enum):
    OPEN       = "open"
    ACTIONED   = "actioned"
    SUPERSEDED = "superseded"
    DEFERRED   = "deferred"


# ═══════════════════════════════════════════════════════════════════════════════
# Shared value objects
# ═══════════════════════════════════════════════════════════════════════════════

class ExternalLink(BaseModel):
    system: str
    label:  str
    url:    Optional[str] = None


class Dependency(BaseModel):
    kind: Literal["internal", "external"]
    ref:  str
    url:  Optional[str] = None
    note: Optional[str] = None


class Stakeholder(BaseModel):
    name:    str
    role:    Literal["requestor", "sponsor", "approver", "reviewer", "informed"]
    contact: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Requirements
# ═══════════════════════════════════════════════════════════════════════════════

def make_req_id(req_type: RequirementType) -> str:
    return f"REQ-{req_type.id_prefix}-{str(uuid.uuid4())[:8].upper()}"


class RequirementIn(BaseModel):
    """Validated input for creating a requirement."""
    req_type:       RequirementType    = RequirementType.CORE
    title:          str
    description:    str                = ""
    status:         RequirementStatus  = RequirementStatus.OPEN
    priority:       RequirementPriority = RequirementPriority.MEDIUM
    owner:          Optional[str]      = None
    stakeholders:   list[Stakeholder]  = Field(default_factory=list)
    predecessors:   list[Dependency]   = Field(default_factory=list)
    dependencies:   list[Dependency]   = Field(default_factory=list)
    external_links: list[ExternalLink] = Field(default_factory=list)
    tags:           list[str]          = Field(default_factory=list)
    # FRET-structured description (populated by refine-requirements skill)
    fret_statement: Optional[str]      = None
    fret_fields:    Optional[dict]     = None  # scope/condition/component/timing/response


class RequirementRow(RequirementIn):
    """Full DB row — adds id and timestamps."""
    id:            str
    created_at:    datetime
    updated_at:    datetime
    has_embedding: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# Updates
# ═══════════════════════════════════════════════════════════════════════════════

class FieldDiff(BaseModel):
    field:     str
    old_value: Any
    new_value: Any


class UpdateRecord(BaseModel):
    id:             str      = Field(default_factory=lambda: str(uuid.uuid4()))
    requirement_id: str
    changed_at:     datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    changed_by:     str
    summary:        str
    diffs:          list[FieldDiff] = Field(default_factory=list)
    full_snapshot:  Optional[dict]  = None


# ═══════════════════════════════════════════════════════════════════════════════
# Minutes
# ═══════════════════════════════════════════════════════════════════════════════

class Decision(BaseModel):
    decision_id:  str      = Field(default_factory=lambda: f"DEC-{str(uuid.uuid4())[:8].upper()}")
    title:        str
    detail:       str      = ""
    made_by:      list[str] = Field(default_factory=list)
    status:       DecisionStatus = DecisionStatus.OPEN
    affects_reqs: list[str] = Field(default_factory=list)
    action_owner: Optional[str] = None
    due_date:     Optional[date] = None
    notes:        str      = ""


class ActionItem(BaseModel):
    action_id:   str = Field(default_factory=lambda: f"ACT-{str(uuid.uuid4())[:8].upper()}")
    description: str
    owner:       Optional[str] = None
    due_date:    Optional[date] = None
    done:        bool = False


class MinuteIn(BaseModel):
    title:        str
    source:       MeetingSource = MeetingSource.OTHER
    source_url:   Optional[str] = None
    occurred_at:  datetime      = Field(default_factory=lambda: datetime.now(timezone.utc))
    logged_by:    str
    attendees:    list[str]     = Field(default_factory=list)
    summary:      str           = ""
    raw_notes:    str           = ""
    decisions:    list[Decision]   = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)


class MinuteRow(MinuteIn):
    id:                     str
    logged_at:              datetime
    integrated_into_status: bool               = False
    integrated_at:          Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Project metadata
# ═══════════════════════════════════════════════════════════════════════════════

class ProjectMeta(BaseModel):
    project_id:        str      = Field(default_factory=lambda: str(uuid.uuid4()))
    slug:              str      = ""   # derived from name, used for filenames
    name:              str
    code:              Optional[str]    = None
    phase:             ProjectPhase     = ProjectPhase.DISCOVERY
    objective:         str              = ""
    business_case:     str              = ""
    success_criteria:  list[str]        = Field(default_factory=list)
    out_of_scope:      list[str]        = Field(default_factory=list)
    project_owner:     Optional[str]    = None
    sponsor:           Optional[str]    = None
    stakeholders:      list[Stakeholder]   = Field(default_factory=list)
    start_date:        Optional[date]   = None
    target_date:       Optional[date]   = None
    actual_end_date:   Optional[date]   = None
    external_links:    list[ExternalLink]  = Field(default_factory=list)
    status_summary:    str              = ""
    status_updated_at: Optional[datetime] = None
    created_at:        datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:        datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
