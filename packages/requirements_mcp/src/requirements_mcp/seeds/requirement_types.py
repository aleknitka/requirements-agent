"""Seed data for the ``requirement_types`` table.

Defines the kinds a requirement can be classified as: functional,
non-functional, business, stakeholder, user, system, interface, data,
security, privacy, compliance, performance, availability, usability,
operational, AI/ML, reporting, constraint, and transition. Each entry
has a stable three-letter code (used as the foreign-key value) and a
readable slug suitable for URLs and filters.
"""

from __future__ import annotations

from pydantic import Field

from requirements_mcp.seeds._base import SeedBase


class RequirementTypeSeed(SeedBase):
    """Validated row template for a requirement type.

    The ``code`` is constrained to exactly three uppercase ASCII
    letters so type codes are visually consistent across the codebase
    and short enough to use in compact identifiers. The ``key`` is the
    matching lowercase slug. ``sort_order`` determines display order in
    user interfaces and must be non-negative.
    """

    code: str = Field(pattern=r"^[A-Z]{3}$")
    key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str
    description: str
    sort_order: int = Field(ge=0)


REQUIREMENT_TYPES: list[RequirementTypeSeed] = [
    RequirementTypeSeed(
        code="FUN",
        key="functional",
        label="Functional",
        description="Describes system behaviour, features, or capabilities.",
        sort_order=10,
    ),
    RequirementTypeSeed(
        code="NFR",
        key="non_functional",
        label="Non-Functional",
        description=(
            "Defines quality attributes such as performance, "
            "reliability, scalability, or maintainability."
        ),
        sort_order=20,
    ),
    RequirementTypeSeed(
        code="BUS",
        key="business",
        label="Business",
        description="High-level business objective, rule, or organisational need.",
        sort_order=30,
    ),
    RequirementTypeSeed(
        code="STK",
        key="stakeholder",
        label="Stakeholder",
        description="Requirement originating from a stakeholder or stakeholder group.",
        sort_order=40,
    ),
    RequirementTypeSeed(
        code="USR",
        key="user",
        label="User",
        description="Requirement focused on end-user goals, tasks, or interactions.",
        sort_order=50,
    ),
    RequirementTypeSeed(
        code="SYS",
        key="system",
        label="System",
        description=(
            "Requirement concerning system-level behaviour, "
            "architecture, or integration."
        ),
        sort_order=60,
    ),
    RequirementTypeSeed(
        code="INT",
        key="interface",
        label="Interface",
        description=(
            "Requirement related to APIs, user interfaces, or external integrations."
        ),
        sort_order=70,
    ),
    RequirementTypeSeed(
        code="DAT",
        key="data",
        label="Data",
        description=(
            "Requirement concerning data models, storage, quality, "
            "lineage, governance, or processing."
        ),
        sort_order=80,
    ),
    RequirementTypeSeed(
        code="SEC",
        key="security",
        label="Security",
        description=(
            "Requirement related to authentication, authorisation, "
            "confidentiality, integrity, or auditing."
        ),
        sort_order=90,
    ),
    RequirementTypeSeed(
        code="PRV",
        key="privacy",
        label="Privacy",
        description=(
            "Requirement concerning personal data handling, consent, "
            "retention, or regulatory compliance."
        ),
        sort_order=100,
    ),
    RequirementTypeSeed(
        code="COM",
        key="compliance",
        label="Compliance",
        description=(
            "Requirement derived from legal, regulatory, industry, "
            "or organisational standards."
        ),
        sort_order=110,
    ),
    RequirementTypeSeed(
        code="PER",
        key="performance",
        label="Performance",
        description=(
            "Requirement concerning latency, throughput, resource usage, "
            "or responsiveness."
        ),
        sort_order=120,
    ),
    RequirementTypeSeed(
        code="AVL",
        key="availability",
        label="Availability",
        description=(
            "Requirement related to uptime, resiliency, fault tolerance, "
            "or disaster recovery."
        ),
        sort_order=130,
    ),
    RequirementTypeSeed(
        code="USB",
        key="usability",
        label="Usability",
        description=(
            "Requirement concerning accessibility, learnability, or ease of use."
        ),
        sort_order=140,
    ),
    RequirementTypeSeed(
        code="OPS",
        key="operational",
        label="Operational",
        description=(
            "Requirement concerning deployment, monitoring, maintenance, "
            "or operational support."
        ),
        sort_order=150,
    ),
    RequirementTypeSeed(
        code="AIM",
        key="ai_ml",
        label="AI/ML",
        description=(
            "Requirement specific to machine learning, LLMs, evaluation, "
            "training, inference, or model governance."
        ),
        sort_order=160,
    ),
    RequirementTypeSeed(
        code="REP",
        key="reporting",
        label="Reporting",
        description=(
            "Requirement related to reporting, dashboards, analytics, "
            "or business intelligence."
        ),
        sort_order=170,
    ),
    RequirementTypeSeed(
        code="CNS",
        key="constraint",
        label="Constraint",
        description=(
            "Requirement expressing a limitation, restriction, technology "
            "choice, or mandated dependency."
        ),
        sort_order=180,
    ),
    RequirementTypeSeed(
        code="TRN",
        key="transition",
        label="Transition",
        description=(
            "Temporary requirement related to migration, rollout, "
            "onboarding, or legacy replacement."
        ),
        sort_order=190,
    ),
]


__all__ = ["REQUIREMENT_TYPES", "RequirementTypeSeed"]
