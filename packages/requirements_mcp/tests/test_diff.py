"""Tests for :mod:`requirements_mcp.services.diff`."""

from __future__ import annotations

from requirements_mcp.models import Requirement
from requirements_mcp.services.diff import (
    DIFFABLE_FIELDS,
    JSON_LIST_FIELDS,
    SCALAR_FIELDS,
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


def test_constants_are_consistent() -> None:
    assert set(DIFFABLE_FIELDS) == set(SCALAR_FIELDS) | set(JSON_LIST_FIELDS)
    assert len(DIFFABLE_FIELDS) == len(SCALAR_FIELDS) + len(JSON_LIST_FIELDS)


def test_empty_updates_produces_empty_diff() -> None:
    assert compute_diff(_stub_requirement(), {}) == {}


def test_no_change_produces_empty_diff() -> None:
    req = _stub_requirement(title="hello")
    assert compute_diff(req, {"title": "hello"}) == {}


def test_scalar_change_recorded() -> None:
    req = _stub_requirement(status_code="draft")
    diff = compute_diff(req, {"status_code": "approved"})
    assert diff == {"status_code": {"from": "draft", "to": "approved"}}


def test_list_change_recorded() -> None:
    req = _stub_requirement(acceptance_criteria=["a"])
    diff = compute_diff(req, {"acceptance_criteria": ["a", "b"]})
    assert diff == {
        "acceptance_criteria": {"from": ["a"], "to": ["a", "b"]},
    }


def test_partial_diff_only_includes_changed_fields() -> None:
    req = _stub_requirement(title="t", status_code="draft")
    diff = compute_diff(req, {"title": "t", "status_code": "approved"})
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
    )
    assert diff == {"title": {"from": "t", "to": "new title"}}


def test_does_not_mutate_inputs() -> None:
    req = _stub_requirement(users=["u1"])
    updates = {"users": ["u1", "u2"]}
    compute_diff(req, updates)
    assert req.users == ["u1"]
    assert updates == {"users": ["u1", "u2"]}
