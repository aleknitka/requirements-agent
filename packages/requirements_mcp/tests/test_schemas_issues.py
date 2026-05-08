"""Tests for the Pydantic schemas in :mod:`requirements_mcp.schemas.issues`."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import get_args

import pytest
from pydantic import ValidationError

from requirements_mcp.schemas import (
    IssueCreate,
    IssueOut,
    IssuePriorityCode,
    IssuePriorityOut,
    IssueSearchHit,
    IssueSearchQuery,
    IssueStatusCode,
    IssueStatusOut,
    IssueTypeCode,
    IssueTypeOut,
    IssueUpdate,
    IssueUpdateAdd,
    IssueUpdateOut,
    IssueUpdateTypeCode,
    RequirementIssueLinkCreate,
    RequirementIssueLinkOut,
    RequirementIssueLinkType,
)
from requirements_mcp.seeds import (
    ISSUE_PRIORITIES,
    ISSUE_STATUSES,
    ISSUE_TYPES,
)


def _minimal_create_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        title="Login flow ambiguous",
        description="Whether SSO is in scope is unclear.",
        issue_type_code="AMB",
        created_by="agent",
    )
    base.update(overrides)
    return base


class TestIssueCreate:
    def test_minimum_fields_validate(self) -> None:
        payload = IssueCreate(**_minimal_create_kwargs())
        assert payload.status_code == "open"
        assert payload.priority_code == "MED"
        assert payload.owner is None

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            IssueCreate(**_minimal_create_kwargs(unknown="x"))

    def test_rejects_empty_title(self) -> None:
        with pytest.raises(ValidationError):
            IssueCreate(**_minimal_create_kwargs(title=""))

    def test_rejects_empty_description(self) -> None:
        with pytest.raises(ValidationError):
            IssueCreate(**_minimal_create_kwargs(description=""))

    def test_rejects_unknown_type_code(self) -> None:
        with pytest.raises(ValidationError):
            IssueCreate(**_minimal_create_kwargs(issue_type_code="ZZZ"))

    def test_rejects_unknown_status_code(self) -> None:
        with pytest.raises(ValidationError):
            IssueCreate(**_minimal_create_kwargs(status_code="not-a-status"))

    def test_rejects_unknown_priority_code(self) -> None:
        with pytest.raises(ValidationError):
            IssueCreate(**_minimal_create_kwargs(priority_code="ZZZ"))


class TestIssueUpdate:
    def test_author_and_change_description_required(self) -> None:
        with pytest.raises(ValidationError):
            IssueUpdate(title="x")  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            IssueUpdate(author="alice", title="x")  # type: ignore[call-arg]

    def test_minimal_legal_payload(self) -> None:
        payload = IssueUpdate(author="alice", change_description="why")
        assert payload.model_dump(exclude_unset=True) == {
            "author": "alice",
            "change_description": "why",
        }

    def test_rejects_empty_change_description(self) -> None:
        with pytest.raises(ValidationError):
            IssueUpdate(author="alice", change_description="")

    def test_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            IssueUpdate(  # type: ignore[call-arg]
                author="alice",
                change_description="why",
                unknown="x",
            )

    def test_rejects_unknown_status_code(self) -> None:
        with pytest.raises(ValidationError):
            IssueUpdate(author="alice", change_description="why", status_code="bogus")

    def test_rejects_unknown_priority_code(self) -> None:
        with pytest.raises(ValidationError):
            IssueUpdate(author="alice", change_description="why", priority_code="ZZ")


class TestIssueUpdateAdd:
    def test_minimal_legal_payload(self) -> None:
        payload = IssueUpdateAdd(
            update_type_code="note",
            description="Stakeholder confirmed scope.",
            author="alice",
        )
        assert payload.action_taken == ""
        assert payload.action_result == ""

    def test_rejects_empty_description(self) -> None:
        with pytest.raises(ValidationError):
            IssueUpdateAdd(update_type_code="note", description="", author="alice")

    def test_rejects_unknown_update_type(self) -> None:
        with pytest.raises(ValidationError):
            IssueUpdateAdd(
                update_type_code="invented",  # type: ignore[arg-type]
                description="x",
                author="alice",
            )


class TestRequirementIssueLinkCreate:
    def test_default_link_type(self) -> None:
        payload = RequirementIssueLinkCreate(requirement_id="req-1", author="alice")
        assert payload.link_type == "related"

    def test_rejects_unknown_link_type(self) -> None:
        with pytest.raises(ValidationError):
            RequirementIssueLinkCreate(
                requirement_id="req-1",
                link_type="invented",  # type: ignore[arg-type]
                author="alice",
            )


class TestIssueSearchQuery:
    def test_defaults(self) -> None:
        q = IssueSearchQuery()
        assert q.query == ""
        assert q.status_codes is None
        assert q.limit == 50
        assert q.offset == 0

    def test_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            IssueSearchQuery(limit=0)
        with pytest.raises(ValidationError):
            IssueSearchQuery(limit=501)

    def test_rejects_unknown_status_in_filter(self) -> None:
        with pytest.raises(ValidationError):
            IssueSearchQuery(status_codes=["bogus"])  # type: ignore[list-item]


def test_issue_status_literal_matches_seeds() -> None:
    assert set(get_args(IssueStatusCode)) == {s.code for s in ISSUE_STATUSES}


def test_issue_type_literal_matches_seeds() -> None:
    assert set(get_args(IssueTypeCode)) == {s.code for s in ISSUE_TYPES}


def test_issue_priority_literal_matches_seeds() -> None:
    assert set(get_args(IssuePriorityCode)) == {s.code for s in ISSUE_PRIORITIES}


def test_link_type_literal_is_documented_set() -> None:
    expected = {
        "related",
        "blocks",
        "clarifies",
        "conflicts_with",
        "risk_for",
        "caused_by",
        "resolved_by",
    }
    assert set(get_args(RequirementIssueLinkType)) == expected


def test_update_type_literal_includes_canonical_codes() -> None:
    expected_subset = {
        "created",
        "field_changed",
        "status_changed",
        "priority_changed",
        "requirement_linked",
        "requirement_unlinked",
        "note",
    }
    assert expected_subset.issubset(set(get_args(IssueUpdateTypeCode)))


class TestOutModelsRoundTrip:
    def test_issue_out_from_attributes(self) -> None:
        now = datetime.now(timezone.utc)

        class _Stub:
            id = "abc"
            title = "x"
            description = "y"
            issue_type_code = "AMB"
            status_code = "open"
            priority_code = "MED"
            impact = ""
            risk = ""
            proposed_resolution = ""
            owner = None
            created_by = "agent"
            date_created = now
            date_updated = now
            date_closed = None

        out = IssueOut.model_validate(_Stub())
        assert out.id == "abc"
        assert out.date_closed is None

    def test_update_out_from_attributes(self) -> None:
        now = datetime.now(timezone.utc)

        class _Stub:
            id = "u1"
            issue_id = "i1"
            update_type_code = "status_changed"
            description = "approved"
            diff = {"status_code": {"from": "open", "to": "resolved"}}
            action_taken = ""
            action_result = ""
            author = "alice"
            date = now

        out = IssueUpdateOut.model_validate(_Stub())
        assert out.diff["status_code"]["to"] == "resolved"

    def test_link_out_from_attributes(self) -> None:
        now = datetime.now(timezone.utc)

        class _Stub:
            requirement_id = "r1"
            issue_id = "i1"
            link_type = "blocks"
            rationale = "blocks login flow"
            date_created = now

        out = RequirementIssueLinkOut.model_validate(_Stub())
        assert out.link_type == "blocks"

    def test_search_hit_from_attributes(self) -> None:
        now = datetime.now(timezone.utc)

        class _Stub:
            id = "i1"
            title = "x"
            issue_type_code = "AMB"
            status_code = "open"
            priority_code = "MED"
            owner = None
            date_updated = now

        out = IssueSearchHit.model_validate(_Stub())
        assert out.priority_code == "MED"

    def test_metadata_out_from_attributes(self) -> None:
        class _StatusStub:
            code = "open"
            label = "Open"
            description = "x"
            is_terminal = False
            sort_order = 10

        class _TypeStub:
            code = "AMB"
            key = "ambiguity"
            label = "Ambiguity"
            description = "x"
            sort_order = 10

        class _PriorityStub:
            code = "LOW"
            label = "Low"
            description = "x"
            severity_order = 10
            sort_order = 10

        assert IssueStatusOut.model_validate(_StatusStub()).code == "open"
        assert IssueTypeOut.model_validate(_TypeStub()).key == "ambiguity"
        assert IssuePriorityOut.model_validate(_PriorityStub()).severity_order == 10
