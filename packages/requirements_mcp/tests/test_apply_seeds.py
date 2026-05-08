"""Tests for ``requirements_mcp.seeds.apply.apply_seeds``."""

from __future__ import annotations

from sqlalchemy.orm import Session

from requirements_mcp.models import (
    IssuePriority,
    IssueStatus,
    IssueType,
    RequirementStatus,
    RequirementType,
)
from requirements_mcp.seeds.apply import apply_seeds


def test_first_call_inserts_all_rows(db_session: Session) -> None:
    report = apply_seeds(db_session)
    db_session.commit()

    assert report.inserted["requirement_statuses"] == 11
    assert report.inserted["requirement_types"] == 19
    assert report.inserted["issue_statuses"] == 10
    assert report.inserted["issue_types"] == 11
    assert report.inserted["issue_priorities"] == 4

    assert db_session.query(RequirementStatus).count() == 11
    assert db_session.query(RequirementType).count() == 19
    assert db_session.query(IssueStatus).count() == 10
    assert db_session.query(IssueType).count() == 11
    assert db_session.query(IssuePriority).count() == 4


def test_second_call_is_idempotent(db_session: Session) -> None:
    apply_seeds(db_session)
    db_session.commit()

    second = apply_seeds(db_session)
    db_session.commit()

    assert sum(second.inserted.values()) == 0
    assert second.skipped["requirement_statuses"] == 11
    assert second.skipped["issue_priorities"] == 4


def test_existing_row_is_not_overwritten(db_session: Session) -> None:
    apply_seeds(db_session)
    db_session.commit()

    row = db_session.get(IssueStatus, "open")
    assert row is not None
    row.description = "locally edited"
    db_session.commit()

    apply_seeds(db_session)
    db_session.commit()

    refreshed = db_session.get(IssueStatus, "open")
    assert refreshed is not None
    assert refreshed.description == "locally edited"
