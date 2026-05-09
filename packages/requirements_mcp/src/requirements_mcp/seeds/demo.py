"""Demo content for ``requirements-db-init --demo-data``.

A frozen list of ten realistic requirements, five issues, and a
handful of cross-links. Inserted through the regular service layer
(:mod:`requirements_mcp.services.requirements`,
:mod:`requirements_mcp.services.issues`) so each insert produces the
matching audit row — the demo data is indistinguishable from data
created by an interactive user, except for the ``"demo"`` author
attribution.

Idempotency: :func:`apply_demo_data` short-circuits when the
``requirements`` table already has at least one row. That makes
``--demo-data`` safe to re-run; combine with ``--reset --yes`` to wipe
the database first.
"""

from __future__ import annotations

from typing import NamedTuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from requirements_mcp.models import Requirement
from requirements_mcp.schemas.issues import (
    IssueCreate,
    RequirementIssueLinkCreate,
    RequirementIssueLinkType,
)
from requirements_mcp.schemas.requirements import RequirementCreate
from requirements_mcp.services.issues import (
    create_issue,
    link_issue_to_requirement,
)
from requirements_mcp.services.requirements import create_requirement

DEMO_AUTHOR = "demo"
"""Author attribution applied to every demo row."""


DEMO_REQUIREMENTS: list[RequirementCreate] = [
    RequirementCreate(
        title="User login with email and password",
        requirement_statement=(
            "The system shall let registered users authenticate with an "
            "email address and password."
        ),
        type_code="USR",
        author=DEMO_AUTHOR,
        users=["end_user"],
        triggers=["user_visits_login"],
        preconditions=["user_account_exists"],
        postconditions=["session_token_issued"],
        inputs=["email", "password"],
        outputs=["session_token"],
        acceptance_criteria=[
            "Valid credentials succeed and return a token.",
            "Invalid credentials return a clear error message.",
            "Three consecutive failures lock the account for 5 minutes.",
        ],
    ),
    RequirementCreate(
        title="Password hashing at rest",
        requirement_statement=(
            "The system shall store user passwords using a memory-hard "
            "hash (Argon2id) with per-user random salt."
        ),
        type_code="SEC",
        author=DEMO_AUTHOR,
        acceptance_criteria=[
            "No plain-text passwords appear in the database or in logs.",
            "Hash parameters are configurable and reviewed annually.",
        ],
    ),
    RequirementCreate(
        title="Search latency p95 under 250ms",
        requirement_statement=(
            "The Requirements search endpoint shall return results in "
            "under 250ms at p95 for queries against a 10k-row corpus."
        ),
        type_code="PER",
        author=DEMO_AUTHOR,
        acceptance_criteria=[
            "Synthetic load test sustains ≥ 50 RPS for 10 minutes.",
            "p95 latency stays under 250ms across the run.",
        ],
    ),
    RequirementCreate(
        title="Daily database backup",
        requirement_statement=(
            "The system shall produce an automatic daily backup of the "
            "SQLite database with at least 14 days of retention."
        ),
        type_code="OPS",
        author=DEMO_AUTHOR,
        acceptance_criteria=[
            "A backup is created at 02:00 local time every day.",
            "Restoring from any of the last 14 backups recovers the schema.",
        ],
    ),
    RequirementCreate(
        title="Audit trail for every requirement edit",
        requirement_statement=(
            "Every change to a requirement shall produce a structured "
            "diff entry in the requirements_changes table within the "
            "same transaction as the edit."
        ),
        type_code="NFR",
        author=DEMO_AUTHOR,
        acceptance_criteria=[
            "No code path mutates a requirement without writing a diff row.",
            "Diff JSON includes from/to values for each changed field.",
        ],
    ),
    RequirementCreate(
        title="Personal data export on request",
        requirement_statement=(
            "On a verified user request, the system shall produce a "
            "machine-readable export of all personal data stored about "
            "that user within 30 days."
        ),
        type_code="COM",
        author=DEMO_AUTHOR,
        acceptance_criteria=[
            "Export is delivered as JSON.",
            "Request log captures who requested and who fulfilled.",
        ],
    ),
    RequirementCreate(
        title="MCP tool surface stability",
        requirement_statement=(
            "The MCP server shall expose exactly the seventeen tools "
            "documented in the public README; UI handlers must not "
            "appear over MCP."
        ),
        type_code="INT",
        author=DEMO_AUTHOR,
        acceptance_criteria=[
            "A smoke test asserts the tool list matches REGISTERED_TOOLS.",
            "Adding a UI handler does not increase the MCP tool count.",
        ],
    ),
    RequirementCreate(
        title="Keyboard accessible Search tab",
        requirement_statement=(
            "Every interactive control on the Search tab shall be "
            "reachable and operable using only keyboard input, with a "
            "visible focus indicator."
        ),
        type_code="USB",
        author=DEMO_AUTHOR,
        acceptance_criteria=[
            "Tab order matches the visual reading order.",
            "All buttons can be activated with Enter or Space.",
        ],
    ),
    RequirementCreate(
        title="Schema migrations via Alembic",
        requirement_statement=(
            "Future schema changes shall be expressed as Alembic "
            "migrations; ad-hoc ALTER TABLE statements are forbidden."
        ),
        type_code="DAT",
        author=DEMO_AUTHOR,
        acceptance_criteria=[
            "Initial Alembic environment exists in the repository.",
            "`alembic upgrade head` reproduces the live schema.",
        ],
    ),
    RequirementCreate(
        title="Issue link to multiple requirements",
        requirement_statement=(
            "An issue shall be linkable to one or more requirements with "
            "a typed relationship and a free-text rationale."
        ),
        type_code="FUN",
        author=DEMO_AUTHOR,
        users=["agent", "analyst"],
        triggers=["issue_classification_complete"],
        acceptance_criteria=[
            "A single issue can have N >= 1 links.",
            "Each link records link_type, rationale, and date_created.",
        ],
    ),
]
"""Ten demo requirements covering ten different type codes."""


DEMO_ISSUES: list[IssueCreate] = [
    IssueCreate(
        title='What does "verified user request" mean for export?',
        description=(
            "REQ on personal data export is unclear about what counts as "
            "verification (email round-trip? government id?)."
        ),
        issue_type_code="AMB",
        priority_code="MED",
        created_by=DEMO_AUTHOR,
        impact="Cannot finalise compliance section.",
    ),
    IssueCreate(
        title="Backup retention numbers not finalised",
        description=(
            "OPS team needs to confirm whether 14 days of retention is "
            "enough for the regulated tier."
        ),
        issue_type_code="GAP",
        priority_code="HIG",
        created_by=DEMO_AUTHOR,
        impact="Could trigger compliance findings if the window is too short.",
    ),
    IssueCreate(
        title="Argon2id parameters tuned for laptop, not server",
        description=(
            "Current parameters were measured on a developer laptop. "
            "Need to re-tune for production hardware."
        ),
        issue_type_code="RSK",
        priority_code="MED",
        created_by=DEMO_AUTHOR,
        risk="Logins could become unacceptably slow under load.",
    ),
    IssueCreate(
        title="Search index missing on requirement_statement",
        description=(
            "Search latency target cannot be met without an index on "
            "the requirement_statement column."
        ),
        issue_type_code="BLK",
        priority_code="CRT",
        created_by=DEMO_AUTHOR,
        impact="Blocks acceptance of the search latency requirement.",
    ),
    IssueCreate(
        title="Should issues track effort estimates?",
        description=(
            "Stakeholder question: do we want story-point estimates on "
            "issues, or do we keep them lightweight?"
        ),
        issue_type_code="QST",
        priority_code="LOW",
        created_by=DEMO_AUTHOR,
    ),
]
"""Five demo issues, one per main type, varied priorities."""


DEMO_LINKS: list[tuple[int, int, RequirementIssueLinkType, str]] = [
    (
        5,
        0,
        "clarifies",
        "Clarifying the verification policy for the data-export requirement.",
    ),
    (3, 1, "blocks", "Retention window is required input for the backup requirement."),
    (
        2,
        3,
        "blocks",
        "Latency requirement cannot pass acceptance until the index lands.",
    ),
]
"""Three demo links: ``(req_index, issue_index, link_type, rationale)``."""


class DemoReport(NamedTuple):
    """Outcome of an :func:`apply_demo_data` run.

    Attributes:
        requirements: Number of requirement rows inserted.
        issues: Number of issue rows inserted.
        links: Number of requirement-issue links inserted.
        skipped: ``True`` when the function returned early because the
            database already contained requirements (idempotent path).
    """

    requirements: int
    issues: int
    links: int
    skipped: bool


def apply_demo_data(session: Session) -> DemoReport:
    """Populate the database with the demo requirements, issues, and links.

    Idempotent: if the ``requirements`` table already holds any rows the
    function returns ``DemoReport(0, 0, 0, skipped=True)`` without
    touching the database. Otherwise it inserts every entry from
    :data:`DEMO_REQUIREMENTS` and :data:`DEMO_ISSUES`, then creates the
    cross-links from :data:`DEMO_LINKS`. The caller is responsible for
    committing the session.

    Each insert flows through the regular service layer so the audit
    trail invariants (a ``requirements_changes`` row per requirement,
    an ``issue_updates`` row per issue, plus link audit rows) are
    upheld automatically.

    Args:
        session: Active SQLAlchemy session bound to the target database.
            The caller commits.

    Returns:
        A :class:`DemoReport` summarising what was inserted, or noting
        that the run was skipped.
    """
    existing = session.scalar(select(func.count()).select_from(Requirement)) or 0
    if existing > 0:
        return DemoReport(requirements=0, issues=0, links=0, skipped=True)

    requirement_ids: list[str] = []
    for payload in DEMO_REQUIREMENTS:
        req = create_requirement(session, payload)
        # ``create_requirement`` assigns the id eagerly so it is
        # readable before commit.
        requirement_ids.append(req.id)

    issue_ids: list[str] = []
    for payload in DEMO_ISSUES:
        issue = create_issue(session, payload)
        issue_ids.append(issue.id)

    links_inserted = 0
    for req_idx, issue_idx, link_type, rationale in DEMO_LINKS:
        link_issue_to_requirement(
            session,
            issue_ids[issue_idx],
            RequirementIssueLinkCreate(
                requirement_id=requirement_ids[req_idx],
                link_type=link_type,
                rationale=rationale,
                author=DEMO_AUTHOR,
            ),
        )
        links_inserted += 1

    return DemoReport(
        requirements=len(requirement_ids),
        issues=len(issue_ids),
        links=links_inserted,
        skipped=False,
    )


__all__ = [
    "DEMO_AUTHOR",
    "DEMO_ISSUES",
    "DEMO_LINKS",
    "DEMO_REQUIREMENTS",
    "DemoReport",
    "apply_demo_data",
]
