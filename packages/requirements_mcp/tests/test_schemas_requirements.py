"""Tests for the Pydantic schemas in :mod:`requirements_mcp.schemas.requirements`."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import get_args

import pytest
from pydantic import ValidationError

from requirements_mcp.schemas import (
    RequirementChangeOut,
    RequirementCreate,
    RequirementOut,
    RequirementSearchHit,
    RequirementSearchQuery,
    RequirementStatusCode,
    RequirementStatusOut,
    RequirementTypeCode,
    RequirementTypeOut,
    RequirementUpdate,
)
from requirements_mcp.seeds import REQUIREMENT_STATUSES, REQUIREMENT_TYPES


def _minimal_create_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        title="Login flow",
        requirement_statement="Users can log in.",
        type_code="FUN",
        author="alice",
    )
    base.update(overrides)
    return base


class TestRequirementCreate:
    def test_minimum_fields_validate(self) -> None:
        payload = RequirementCreate(**_minimal_create_kwargs())
        assert payload.status_code == "draft"
        assert payload.users == []

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            RequirementCreate(**_minimal_create_kwargs(unknown="x"))

    def test_rejects_empty_title(self) -> None:
        with pytest.raises(ValidationError):
            RequirementCreate(**_minimal_create_kwargs(title=""))

    def test_rejects_empty_statement(self) -> None:
        with pytest.raises(ValidationError):
            RequirementCreate(**_minimal_create_kwargs(requirement_statement=""))

    def test_rejects_unknown_type_code(self) -> None:
        with pytest.raises(ValidationError):
            RequirementCreate(**_minimal_create_kwargs(type_code="ZZZ"))

    def test_rejects_unknown_status_code(self) -> None:
        with pytest.raises(ValidationError):
            RequirementCreate(**_minimal_create_kwargs(status_code="not-a-status"))


class TestRequirementUpdate:
    def test_author_and_change_description_required(self) -> None:
        with pytest.raises(ValidationError):
            RequirementUpdate(title="x")  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            RequirementUpdate(author="alice", title="x")  # type: ignore[call-arg]

    def test_minimal_legal_payload(self) -> None:
        payload = RequirementUpdate(author="alice", change_description="why")
        assert payload.model_dump(exclude_unset=True) == {
            "author": "alice",
            "change_description": "why",
        }

    def test_rejects_empty_change_description(self) -> None:
        with pytest.raises(ValidationError):
            RequirementUpdate(author="alice", change_description="")

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            RequirementUpdate(  # type: ignore[call-arg]
                author="alice",
                change_description="why",
                unknown="x",
            )

    def test_rejects_unknown_type_code(self) -> None:
        with pytest.raises(ValidationError):
            RequirementUpdate(author="alice", change_description="why", type_code="ZZZ")

    def test_rejects_unknown_status_code(self) -> None:
        with pytest.raises(ValidationError):
            RequirementUpdate(
                author="alice", change_description="why", status_code="bogus"
            )


def test_type_code_literal_matches_seeds() -> None:
    """Literal must list every seeded requirement type code, and only those."""
    assert set(get_args(RequirementTypeCode)) == {s.code for s in REQUIREMENT_TYPES}


def test_status_code_literal_matches_seeds() -> None:
    """Literal must list every seeded requirement status code, and only those."""
    assert set(get_args(RequirementStatusCode)) == {
        s.code for s in REQUIREMENT_STATUSES
    }


class TestRequirementSearchQuery:
    def test_defaults(self) -> None:
        q = RequirementSearchQuery()
        assert q.query == ""
        assert q.status_codes is None
        assert q.limit == 50
        assert q.offset == 0

    def test_limit_lower_bound(self) -> None:
        with pytest.raises(ValidationError):
            RequirementSearchQuery(limit=0)

    def test_limit_upper_bound(self) -> None:
        with pytest.raises(ValidationError):
            RequirementSearchQuery(limit=501)

    def test_offset_lower_bound(self) -> None:
        with pytest.raises(ValidationError):
            RequirementSearchQuery(offset=-1)

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            RequirementSearchQuery(extra=True)  # type: ignore[call-arg]


class TestOutModelsRoundTrip:
    """Out-models must construct cleanly from objects with matching attributes."""

    def test_status_out_from_attributes(self) -> None:
        class _Stub:
            code = "draft"
            label = "Draft"
            description = "x"
            is_active = True
            is_terminal = False
            sort_order = 10

        out = RequirementStatusOut.model_validate(_Stub())
        assert out.code == "draft"
        assert out.is_active is True

    def test_type_out_from_attributes(self) -> None:
        class _Stub:
            code = "FUN"
            key = "functional"
            label = "Functional"
            description = "x"
            sort_order = 10

        out = RequirementTypeOut.model_validate(_Stub())
        assert out.code == "FUN"
        assert out.key == "functional"

    def test_change_out_from_attributes(self) -> None:
        now = datetime.now(timezone.utc)

        class _Stub:
            id = "abc"
            requirement_id = "req"
            change_description = "edited"
            diff = {"title": {"from": "old", "to": "new"}}
            author = "alice"
            date = now

        out = RequirementChangeOut.model_validate(_Stub())
        assert out.diff["title"]["to"] == "new"

    def test_search_hit_from_attributes(self) -> None:
        now = datetime.now(timezone.utc)

        class _Stub:
            id = "abc"
            title = "x"
            type_code = "FUN"
            status_code = "draft"
            version = 2
            date_updated = now

        out = RequirementSearchHit.model_validate(_Stub())
        assert out.version == 2

    def test_requirement_out_from_attributes(self) -> None:
        now = datetime.now(timezone.utc)

        class _Stub:
            id = "abc"
            title = "x"
            requirement_statement = "x"
            type_code = "FUN"
            status_code = "draft"
            version = 1
            author = "alice"
            date_created = now
            date_updated = now
            extended_description = ""
            users = ["u1"]
            triggers = []
            preconditions = []
            postconditions = []
            inputs = []
            outputs = []
            business_logic = []
            exception_handling = []
            acceptance_criteria = []

        out = RequirementOut.model_validate(_Stub())
        assert out.users == ["u1"]
        assert out.version == 1
