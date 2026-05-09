"""Tests for ``Requirement`` and ``RequirementChange`` ORM behaviour."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from requirements_mcp.ids import new_requirement_id
from requirements_mcp.models import Requirement, RequirementChange
from requirements_mcp.seeds.apply import apply_seeds


@pytest.fixture()
def seeded_session(db_session: Session) -> Session:
    apply_seeds(db_session)
    db_session.commit()
    return db_session


def _make_requirement(**overrides: object) -> Requirement:
    defaults: dict[str, object] = dict(
        title="Stakeholder login",
        requirement_statement="The system shall let users authenticate.",
        type_code="FUN",
        status_code="draft",
        author="alice",
        users=["end_user"],
        triggers=["user_visits_login"],
        preconditions=["browser_available"],
        postconditions=["session_token_issued"],
        inputs=["username", "password"],
        outputs=["session_token"],
        business_logic=["validate_credentials"],
        exception_handling=["invalid_credentials"],
        acceptance_criteria=["valid login succeeds"],
    )
    defaults.update(overrides)
    type_code = str(defaults["type_code"])
    defaults.setdefault("id", new_requirement_id(type_code))
    return Requirement(**defaults)


def test_requirement_round_trip_preserves_json_lists(
    seeded_session: Session,
) -> None:
    req = _make_requirement()
    seeded_session.add(req)
    seeded_session.commit()
    req_id = req.id

    seeded_session.expire_all()
    fetched = seeded_session.get(Requirement, req_id)

    assert fetched is not None
    assert fetched.users == ["end_user"]
    assert fetched.acceptance_criteria == ["valid login succeeds"]
    assert fetched.version == 1
    assert fetched.date_created is not None


def test_requirement_rejects_unknown_status_code(
    seeded_session: Session,
) -> None:
    req = _make_requirement(status_code="bogus")
    seeded_session.add(req)
    with pytest.raises(IntegrityError):
        seeded_session.commit()


def test_requirement_rejects_unknown_type_code(
    seeded_session: Session,
) -> None:
    req = _make_requirement(type_code="ZZZ")
    seeded_session.add(req)
    with pytest.raises(IntegrityError):
        seeded_session.commit()


def test_requirement_change_links_back_to_requirement(
    seeded_session: Session,
) -> None:
    req = _make_requirement()
    seeded_session.add(req)
    seeded_session.commit()

    change = RequirementChange(
        requirement_id=req.id,
        change_description="status to approved",
        diff={"status_code": {"from": "draft", "to": "approved"}},
        author="bob",
    )
    seeded_session.add(change)
    seeded_session.commit()

    seeded_session.refresh(req)
    assert len(req.changes) == 1
    assert req.changes[0].diff["status_code"]["to"] == "approved"


def test_requirement_change_cascade_on_delete(
    seeded_session: Session,
) -> None:
    req = _make_requirement()
    seeded_session.add(req)
    seeded_session.commit()
    seeded_session.add(
        RequirementChange(
            requirement_id=req.id,
            change_description="x",
            diff={},
            author="bob",
        )
    )
    seeded_session.commit()

    seeded_session.delete(req)
    seeded_session.commit()

    assert seeded_session.query(RequirementChange).count() == 0
