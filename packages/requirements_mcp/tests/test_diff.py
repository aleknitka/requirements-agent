"""Tests for :mod:`requirements_mcp.services.diff`."""

from __future__ import annotations

from requirements_mcp.models import Requirement
from requirements_mcp.services.diff import (
    ISSUE_DIFFABLE_FIELDS,
    REQUIREMENT_DIFFABLE_FIELDS,
    REQUIREMENT_JSON_LIST_FIELDS,
    REQUIREMENT_SCALAR_FIELDS,
    compute_diff,
)


def _stub_requirement(**overrides: object) -> Requirement:
    base = dict(
        id="r-1",
        title="t",
        requirement_statement="s",
        type_code="FUN",
        status_code="draft",
        author="alice",
        extended_description="",
        users=[],
        triggers=[],
        preconditions=[],
        postconditions=[],
        inputs=[],
        outputs=[],
        business_logic=[],
        exception_handling=[],
        acceptance_criteria=[],
    )
    base.update(overrides)
    return Requirement(**base)  # type: ignore[arg-type]


def test_requirement_constants_are_consistent() -> None:
    assert set(REQUIREMENT_DIFFABLE_FIELDS) == set(REQUIREMENT_SCALAR_FIELDS) | set(
        REQUIREMENT_JSON_LIST_FIELDS
    )
    assert len(REQUIREMENT_DIFFABLE_FIELDS) == len(REQUIREMENT_SCALAR_FIELDS) + len(
        REQUIREMENT_JSON_LIST_FIELDS
    )


def test_issue_diffable_fields_excludes_dates() -> None:
    """date_created/date_updated/date_closed are managed, not user-editable."""
    forbidden = {"date_created", "date_updated", "date_closed", "id", "created_by"}
    assert forbidden.isdisjoint(set(ISSUE_DIFFABLE_FIELDS))


def test_empty_updates_produces_empty_diff() -> None:
    assert compute_diff(_stub_requirement(), {}, REQUIREMENT_DIFFABLE_FIELDS) == {}


def test_no_change_produces_empty_diff() -> None:
    req = _stub_requirement(title="hello")
    assert compute_diff(req, {"title": "hello"}, REQUIREMENT_DIFFABLE_FIELDS) == {}


def test_scalar_change_recorded() -> None:
    req = _stub_requirement(status_code="draft")
    diff = compute_diff(req, {"status_code": "approved"}, REQUIREMENT_DIFFABLE_FIELDS)
    assert diff == {"status_code": {"from": "draft", "to": "approved"}}


def test_list_change_recorded() -> None:
    req = _stub_requirement(acceptance_criteria=["a"])
    diff = compute_diff(
        req,
        {"acceptance_criteria": ["a", "b"]},
        REQUIREMENT_DIFFABLE_FIELDS,
    )
    assert diff == {
        "acceptance_criteria": {"from": ["a"], "to": ["a", "b"]},
    }


def test_partial_diff_only_includes_changed_fields() -> None:
    req = _stub_requirement(title="t", status_code="draft")
    diff = compute_diff(
        req,
        {"title": "t", "status_code": "approved"},
        REQUIREMENT_DIFFABLE_FIELDS,
    )
    assert "title" not in diff
    assert "status_code" in diff


def test_unknown_fields_are_ignored() -> None:
    req = _stub_requirement()
    diff = compute_diff(
        req,
        {
            "title": "new title",
            "author": "should-be-ignored",
            "change_description": "should-be-ignored",
            "id": "should-be-ignored",
        },
        REQUIREMENT_DIFFABLE_FIELDS,
    )
    assert diff == {"title": {"from": "t", "to": "new title"}}


def test_does_not_mutate_inputs() -> None:
    req = _stub_requirement(users=["u1"])
    updates = {"users": ["u1", "u2"]}
    compute_diff(req, updates, REQUIREMENT_DIFFABLE_FIELDS)
    assert req.users == ["u1"]
    assert updates == {"users": ["u1", "u2"]}


def test_diffable_fields_whitelist_is_respected() -> None:
    """Passing ISSUE_DIFFABLE_FIELDS over a Requirement should mostly miss."""

    class _IssueLike:
        title = "old"
        status_code = "open"
        priority_code = "MED"

    diff = compute_diff(
        _IssueLike(),
        {"title": "new", "status_code": "closed", "priority_code": "HIG"},
        ISSUE_DIFFABLE_FIELDS,
    )
    assert set(diff) == {"title", "status_code", "priority_code"}
