"""Tests for :mod:`requirements_mcp.services.requirements`.

Covers the audit-trail invariant: every successful create/update emits a
matching ``requirements_changes`` row.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from requirements_mcp.models import RequirementChange
from requirements_mcp.schemas.requirements import (
    RequirementCreate,
    RequirementSearchQuery,
    RequirementUpdate,
)
from requirements_mcp.services.requirements import (
    RequirementNotFoundError,
    create_requirement,
    get_requirement,
    list_requirement_changes,
    list_requirement_statuses,
    list_requirement_types,
    search_requirements,
    update_requirement,
)


def _create_payload(**overrides: object) -> RequirementCreate:
    base: dict[str, object] = dict(
        title="Login flow",
        requirement_statement="Users can log in with credentials.",
        type_code="FUN",
        author="alice",
        users=["end_user"],
        acceptance_criteria=["valid login succeeds"],
    )
    base.update(overrides)
    return RequirementCreate(**base)


def _change_count(session: Session, requirement_id: str) -> int:
    return (
        session.query(RequirementChange)
        .filter(RequirementChange.requirement_id == requirement_id)
        .count()
    )


class TestCreateRequirement:
    def test_inserts_requirement_and_initial_change(
        self, seeded_session: Session
    ) -> None:
        req = create_requirement(seeded_session, _create_payload())
        seeded_session.commit()

        assert req.id
        assert req.version == 1
        assert _change_count(seeded_session, req.id) == 1

        change = (
            seeded_session.query(RequirementChange)
            .filter(RequirementChange.requirement_id == req.id)
            .one()
        )
        assert change.change_description == "created"
        assert change.diff == {}
        assert change.author == "alice"


class TestUpdateRequirement:
    def test_updates_field_and_logs_change(self, seeded_session: Session) -> None:
        req = create_requirement(seeded_session, _create_payload())
        seeded_session.commit()
        original_version = req.version

        updated = update_requirement(
            seeded_session,
            req.id,
            RequirementUpdate(
                author="bob",
                change_description="approve",
                status_code="approved",
            ),
        )
        seeded_session.commit()

        assert updated.status_code == "approved"
        assert updated.version == original_version + 1
        assert _change_count(seeded_session, req.id) == 2

        latest = (
            seeded_session.query(RequirementChange)
            .filter(RequirementChange.requirement_id == req.id)
            .order_by(RequirementChange.date.desc())
            .first()
        )
        assert latest is not None
        assert latest.change_description == "approve"
        assert latest.author == "bob"
        assert latest.diff == {"status_code": {"from": "draft", "to": "approved"}}

    def test_no_op_update_writes_no_change_row(self, seeded_session: Session) -> None:
        req = create_requirement(seeded_session, _create_payload(title="t"))
        seeded_session.commit()
        before = _change_count(seeded_session, req.id)
        original_version = req.version

        updated = update_requirement(
            seeded_session,
            req.id,
            RequirementUpdate(author="bob", change_description="no-op", title="t"),
        )
        seeded_session.commit()

        assert updated.version == original_version
        assert _change_count(seeded_session, req.id) == before

    def test_unknown_id_raises(self, seeded_session: Session) -> None:
        with pytest.raises(RequirementNotFoundError):
            update_requirement(
                seeded_session,
                "missing",
                RequirementUpdate(author="bob", change_description="x", title="t"),
            )

    def test_list_field_update_recorded(self, seeded_session: Session) -> None:
        req = create_requirement(
            seeded_session, _create_payload(acceptance_criteria=["a"])
        )
        seeded_session.commit()

        update_requirement(
            seeded_session,
            req.id,
            RequirementUpdate(
                author="bob",
                change_description="extend AC",
                acceptance_criteria=["a", "b"],
            ),
        )
        seeded_session.commit()

        latest = (
            seeded_session.query(RequirementChange)
            .filter(RequirementChange.requirement_id == req.id)
            .order_by(RequirementChange.date.desc())
            .first()
        )
        assert latest is not None
        assert latest.diff == {"acceptance_criteria": {"from": ["a"], "to": ["a", "b"]}}

    @pytest.mark.parametrize(
        "field,initial,changed",
        [
            ("title", "t", "T2"),
            ("requirement_statement", "s", "S2"),
            ("status_code", "draft", "approved"),
            ("type_code", "FUN", "NFR"),
            ("extended_description", "", "more detail"),
            ("users", [], ["u1"]),
            ("acceptance_criteria", ["a"], ["a", "b"]),
        ],
    )
    def test_audit_invariant_per_field(
        self,
        seeded_session: Session,
        field: str,
        initial: object,
        changed: object,
    ) -> None:
        """Each diffable field, when changed, must produce exactly one new change row."""
        req = create_requirement(seeded_session, _create_payload(**{field: initial}))
        seeded_session.commit()
        before = _change_count(seeded_session, req.id)

        update_requirement(
            seeded_session,
            req.id,
            RequirementUpdate(
                author="bob",
                change_description=f"update {field}",
                **{field: changed},
            ),  # type: ignore[arg-type]
        )
        seeded_session.commit()

        assert _change_count(seeded_session, req.id) == before + 1


class TestGetRequirement:
    def test_returns_existing(self, seeded_session: Session) -> None:
        req = create_requirement(seeded_session, _create_payload())
        seeded_session.commit()
        assert get_requirement(seeded_session, req.id) is req

    def test_returns_none_for_missing(self, seeded_session: Session) -> None:
        assert get_requirement(seeded_session, "missing") is None


class TestSearchRequirements:
    def test_token_and_match(self, seeded_session: Session) -> None:
        create_requirement(
            seeded_session, _create_payload(title="Stakeholder login flow")
        )
        create_requirement(
            seeded_session, _create_payload(title="Data export pipeline")
        )
        seeded_session.commit()

        hits = search_requirements(
            seeded_session, RequirementSearchQuery(query="login flow")
        )
        assert len(hits) == 1
        assert "login" in hits[0].title.lower()

    def test_filter_by_status(self, seeded_session: Session) -> None:
        a = create_requirement(seeded_session, _create_payload(title="A"))
        create_requirement(seeded_session, _create_payload(title="B"))
        seeded_session.commit()
        update_requirement(
            seeded_session,
            a.id,
            RequirementUpdate(
                author="bob", change_description="approve", status_code="approved"
            ),
        )
        seeded_session.commit()

        approved = search_requirements(
            seeded_session, RequirementSearchQuery(status_codes=["approved"])
        )
        assert {r.id for r in approved} == {a.id}

    def test_filter_by_type(self, seeded_session: Session) -> None:
        fun = create_requirement(
            seeded_session, _create_payload(title="FunOne", type_code="FUN")
        )
        create_requirement(
            seeded_session, _create_payload(title="NFROne", type_code="NFR")
        )
        seeded_session.commit()

        hits = search_requirements(
            seeded_session, RequirementSearchQuery(type_codes=["FUN"])
        )
        assert {r.id for r in hits} == {fun.id}

    def test_pagination(self, seeded_session: Session) -> None:
        for i in range(5):
            create_requirement(seeded_session, _create_payload(title=f"Item {i}"))
        seeded_session.commit()

        page1 = search_requirements(
            seeded_session, RequirementSearchQuery(query="Item", limit=2, offset=0)
        )
        page2 = search_requirements(
            seeded_session, RequirementSearchQuery(query="Item", limit=2, offset=2)
        )
        assert len(page1) == 2
        assert len(page2) == 2
        assert {r.id for r in page1}.isdisjoint({r.id for r in page2})

    def test_empty_query_returns_all_within_limit(
        self, seeded_session: Session
    ) -> None:
        for i in range(3):
            create_requirement(seeded_session, _create_payload(title=f"X{i}"))
        seeded_session.commit()
        hits = search_requirements(seeded_session, RequirementSearchQuery())
        assert len(hits) == 3


class TestListRequirementChanges:
    def test_orders_oldest_first(self, seeded_session: Session) -> None:
        req = create_requirement(seeded_session, _create_payload())
        seeded_session.commit()
        update_requirement(
            seeded_session,
            req.id,
            RequirementUpdate(
                author="bob", change_description="approve", status_code="approved"
            ),
        )
        seeded_session.commit()

        history = list_requirement_changes(seeded_session, req.id)
        assert len(history) == 2
        assert history[0].change_description == "created"
        assert history[1].diff == {"status_code": {"from": "draft", "to": "approved"}}

    def test_unknown_id_raises(self, seeded_session: Session) -> None:
        with pytest.raises(RequirementNotFoundError):
            list_requirement_changes(seeded_session, "missing")


class TestListMetadata:
    def test_statuses_sorted(self, seeded_session: Session) -> None:
        rows = list_requirement_statuses(seeded_session)
        sort_orders = [r.sort_order for r in rows]
        assert sort_orders == sorted(sort_orders)
        assert {r.code for r in rows} >= {"draft", "approved", "verified"}

    def test_types_sorted(self, seeded_session: Session) -> None:
        rows = list_requirement_types(seeded_session)
        sort_orders = [r.sort_order for r in rows]
        assert sort_orders == sorted(sort_orders)
        assert {r.code for r in rows} >= {"FUN", "NFR"}
