"""
models.py — Pydantic validation models.
Nothing here touches the database. Every write goes through these first.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal, NamedTuple, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════

class RequirementStatus(str, Enum):
    BACKLOG     = "backlog"
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
    """Three-letter codes for requirement types. Value == code string."""
    BUS = "BUS"
    USR = "USR"
    FUN = "FUN"
    DAT = "DAT"
    MOD = "MOD"
    MLP = "MLP"
    MET = "MET"
    NFR = "NFR"
    PER = "PER"
    SCL = "SCL"
    SEC = "SEC"
    PRV = "PRV"
    COM = "COM"
    ETH = "ETH"
    EXP = "EXP"
    ROB = "ROB"
    OPS = "OPS"
    DEP = "DEP"
    INT = "INT"
    UIX = "UIX"
    TST = "TST"
    MON = "MON"
    AUD = "AUD"
    GOV = "GOV"
    LGL = "LGL"
    RES = "RES"
    ENV = "ENV"
    MAI = "MAI"
    REL = "REL"
    CON = "CON"
    ASM = "ASM"
    RSK = "RSK"
    DOC = "DOC"
    TRN = "TRN"


class RequirementTypeMeta(NamedTuple):
    code: str
    name: str
    description: str


REQUIREMENT_TYPE_METADATA: list[RequirementTypeMeta] = [
    RequirementTypeMeta("BUS", "Business",       "Business goals, expected value, success criteria, and strategic objectives."),
    RequirementTypeMeta("USR", "User",            "User needs, personas, workflows, pain points, and expected outcomes."),
    RequirementTypeMeta("FUN", "Functional",      "System behaviours and capabilities the solution must provide."),
    RequirementTypeMeta("DAT", "Data",            "Data sources, schema, quality, lineage, retention, ownership, and availability."),
    RequirementTypeMeta("MOD", "Model",           "Model outputs, behaviour, retraining expectations, and model-specific constraints."),
    RequirementTypeMeta("MLP", "ML Pipeline",     "Training, validation, feature engineering, orchestration, and deployment pipeline requirements."),
    RequirementTypeMeta("MET", "Metrics",         "Success metrics, evaluation measures, thresholds, and acceptance criteria."),
    RequirementTypeMeta("NFR", "Non-Functional",  "Cross-cutting quality attributes such as maintainability, usability, and operability."),
    RequirementTypeMeta("PER", "Performance",     "Latency, throughput, response times, training duration, and processing windows."),
    RequirementTypeMeta("SCL", "Scalability",     "Ability to handle growth in users, traffic, data volume, and compute demand."),
    RequirementTypeMeta("SEC", "Security",        "Authentication, authorisation, encryption, secret handling, and secure operations."),
    RequirementTypeMeta("PRV", "Privacy",         "PII handling, consent, anonymisation, minimisation, and privacy-preserving controls."),
    RequirementTypeMeta("COM", "Compliance",      "Regulatory, policy, audit, and standards obligations the solution must satisfy."),
    RequirementTypeMeta("ETH", "Ethics",          "Fairness, bias mitigation, transparency, accountability, and responsible AI considerations."),
    RequirementTypeMeta("EXP", "Explainability",  "Interpretability needs, explanations, reason codes, and user-facing transparency."),
    RequirementTypeMeta("ROB", "Robustness",      "Tolerance to noisy, missing, drifting, or adversarial inputs and changing conditions."),
    RequirementTypeMeta("OPS", "Operations",      "Run-time support, alerting, incident response, and service management expectations."),
    RequirementTypeMeta("DEP", "Deployment",      "Hosting, release process, environment promotion, and production rollout requirements."),
    RequirementTypeMeta("INT", "Integration",     "Interfaces, APIs, external dependencies, and interoperability with other systems."),
    RequirementTypeMeta("UIX", "User Experience", "Interface behaviour, usability, accessibility support, and workflow clarity."),
    RequirementTypeMeta("TST", "Testing",         "Testing strategy including unit, integration, data validation, and model validation requirements."),
    RequirementTypeMeta("MON", "Monitoring",      "Monitoring of service health, model drift, data drift, and business outcome signals."),
    RequirementTypeMeta("AUD", "Auditability",    "Traceability, reproducibility, versioning, and evidence for review or audit."),
    RequirementTypeMeta("GOV", "Governance",      "Ownership, stewardship, approval flows, and change-control responsibilities."),
    RequirementTypeMeta("LGL", "Legal",           "Legal obligations such as licensing, IP restrictions, and contractual constraints."),
    RequirementTypeMeta("RES", "Resources",       "Budget, staffing, infrastructure, storage, and compute resource requirements."),
    RequirementTypeMeta("ENV", "Environment",     "Development, test, staging, and production environment requirements and reproducibility."),
    RequirementTypeMeta("MAI", "Maintainability", "Ease of modification, supportability, documentation quality, and code health expectations."),
    RequirementTypeMeta("REL", "Reliability",     "Availability, fault tolerance, recoverability, and stability requirements."),
    RequirementTypeMeta("CON", "Constraints",     "Limits imposed by time, budget, architecture, technology, vendors, or policy."),
    RequirementTypeMeta("ASM", "Assumptions",     "Conditions believed to be true for planning, design, or estimation purposes."),
    RequirementTypeMeta("RSK", "Risks",           "Known uncertainties or threats affecting delivery, adoption, performance, or compliance."),
    RequirementTypeMeta("DOC", "Documentation",   "Documentation deliverables such as model cards, runbooks, user guides, and technical docs."),
    RequirementTypeMeta("TRN", "Training",        "Training and enablement needs for users, operators, or administrators."),
]


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

class RequirementIn(BaseModel):
    """Validated input for creating a requirement."""
    req_type:       RequirementType     = RequirementType.FUN
    title:          str
    description:    str                 = ""
    status:         RequirementStatus   = RequirementStatus.OPEN
    priority:       RequirementPriority = RequirementPriority.MEDIUM
    owner:          Optional[str]       = None
    stakeholders:   list[Stakeholder]   = Field(default_factory=list)
    predecessors:   list[Dependency]    = Field(default_factory=list)
    dependencies:   list[Dependency]    = Field(default_factory=list)
    external_links: list[ExternalLink]  = Field(default_factory=list)
    tags:           list[str]           = Field(default_factory=list)


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
