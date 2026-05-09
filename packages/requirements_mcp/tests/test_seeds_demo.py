"""Tests for ``requirements_mcp.seeds.demo.apply_demo_data``."""

from __future__ import annotations

from sqlalchemy.orm import Session

from requirements_mcp.models import (
    Issue,
    IssueUpdate as IssueUpdateRow,
    Requirement,
    RequirementChange,
    RequirementIssueLink,
)
from requirements_mcp.seeds.demo import (
    DEMO_ISSUES,
    DEMO_LINKS,
    DEMO_REQUIREMENTS,
    apply_demo_data,
)


def test_apply_demo_data_inserts_expected_counts(seeded_session: Session) -> None:
    report = apply_demo_data(seeded_session)
    seeded_session.commit()

    assert report.skipped is False
    assert report.requirements == len(DEMO_REQUIREMENTS) == 10
    assert report.issues == len(DEMO_ISSUES) == 5
    assert report.links == len(DEMO_LINKS) == 3

    assert seeded_session.query(Requirement).count() == 10
    assert seeded_session.query(Issue).count() == 5
    assert seeded_session.query(RequirementIssueLink).count() == 3


def test_apply_demo_data_is_idempotent(seeded_session: Session) -> None:
    apply_demo_data(seeded_session)
    seeded_session.commit()

    second = apply_demo_data(seeded_session)
    seeded_session.commit()

    assert second.skipped is True
    assert second.requirements == 0
    assert second.issues == 0
    assert second.links == 0
    # Counts unchanged on the second run.
    assert seeded_session.query(Requirement).count() == 10
    assert seeded_session.query(Issue).count() == 5


def test_each_demo_requirement_has_creation_audit_row(
    seeded_session: Session,
) -> None:
    apply_demo_data(seeded_session)
    seeded_session.commit()

    for req in seeded_session.query(Requirement).all():
        creation = (
            seeded_session.query(RequirementChange)
            .filter(RequirementChange.requirement_id == req.id)
            .filter(RequirementChange.change_description == "created")
            .one_or_none()
        )
        assert creation is not None, f"missing creation audit row for {req.id}"


def test_each_demo_issue_has_creation_audit_row(seeded_session: Session) -> None:
    apply_demo_data(seeded_session)
    seeded_session.commit()

    for issue in seeded_session.query(Issue).all():
        creation = (
            seeded_session.query(IssueUpdateRow)
            .filter(IssueUpdateRow.issue_id == issue.id)
            .filter(IssueUpdateRow.update_type_code == "created")
            .one_or_none()
        )
        assert creation is not None, f"missing creation audit row for {issue.id}"


def test_links_join_to_real_records(seeded_session: Session) -> None:
    apply_demo_data(seeded_session)
    seeded_session.commit()

    for link in seeded_session.query(RequirementIssueLink).all():
        assert seeded_session.get(Requirement, link.requirement_id) is not None
        assert seeded_session.get(Issue, link.issue_id) is not None
