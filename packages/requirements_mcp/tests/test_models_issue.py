"""Tests for ``Issue``, ``IssueUpdate``, and ``RequirementIssueLink`` ORM."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from requirements_mcp.models import (
    Issue,
    IssueUpdate,
    Requirement,
    RequirementIssueLink,
)
from requirements_mcp.seeds.apply import apply_seeds


@pytest.fixture()
def seeded_session(db_session: Session) -> Session:
    apply_seeds(db_session)
    db_session.commit()
    return db_session


def _make_issue(**overrides: object) -> Issue:
    defaults: dict[str, object] = dict(
        title="Login flow ambiguous",
        description="Login behaviour for SSO is unclear.",
        issue_type_code="AMB",
        status_code="open",
        priority_code="MED",
        created_by="agent",
    )
    defaults.update(overrides)
    return Issue(**defaults)


def test_issue_creation_and_update_log(seeded_session: Session) -> None:
    issue = _make_issue()
    seeded_session.add(issue)
    seeded_session.commit()

    seeded_session.add(
        IssueUpdate(
            issue_id=issue.id,
            update_type_code="created",
            description="Issue created",
            author="agent",
        )
    )
    seeded_session.commit()

    seeded_session.refresh(issue)
    assert len(issue.updates) == 1
    assert issue.updates[0].update_type_code == "created"


def test_issue_rejects_unknown_priority(seeded_session: Session) -> None:
    issue = _make_issue(priority_code="XYZ")
    seeded_session.add(issue)
    with pytest.raises(IntegrityError):
        seeded_session.commit()


def test_requirement_issue_link_round_trip(seeded_session: Session) -> None:
    req = Requirement(
        title="x",
        requirement_statement="x",
        type_code="FUN",
        status_code="draft",
        author="alice",
    )
    issue = _make_issue()
    seeded_session.add_all([req, issue])
    seeded_session.commit()

    link = RequirementIssueLink(
        requirement_id=req.id,
        issue_id=issue.id,
        link_type="clarifies",
        rationale="ambiguity in requirement statement",
    )
    seeded_session.add(link)
    seeded_session.commit()

    seeded_session.refresh(issue)
    assert len(issue.requirement_links) == 1
    assert issue.requirement_links[0].link_type == "clarifies"


def test_issue_update_cascade_on_issue_delete(seeded_session: Session) -> None:
    issue = _make_issue()
    seeded_session.add(issue)
    seeded_session.commit()
    seeded_session.add(
        IssueUpdate(
            issue_id=issue.id,
            update_type_code="created",
            description="x",
            author="agent",
        )
    )
    seeded_session.commit()

    seeded_session.delete(issue)
    seeded_session.commit()

    assert seeded_session.query(IssueUpdate).count() == 0
