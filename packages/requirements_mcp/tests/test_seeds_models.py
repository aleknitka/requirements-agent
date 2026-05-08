"""Tests for the Pydantic seed models and seed list integrity."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from requirements_mcp.seeds import (
    ISSUE_PRIORITIES,
    ISSUE_STATUSES,
    ISSUE_TYPES,
    REQUIREMENT_STATUSES,
    REQUIREMENT_TYPES,
    IssuePrioritySeed,
    IssueStatusSeed,
    RequirementStatusSeed,
    RequirementTypeSeed,
)


def test_seed_counts_match_spec() -> None:
    assert len(REQUIREMENT_STATUSES) == 11
    assert len(REQUIREMENT_TYPES) == 19
    assert len(ISSUE_STATUSES) == 10
    assert len(ISSUE_TYPES) == 11
    assert len(ISSUE_PRIORITIES) == 4


def test_seed_codes_are_unique() -> None:
    for seeds in (
        REQUIREMENT_STATUSES,
        REQUIREMENT_TYPES,
        ISSUE_STATUSES,
        ISSUE_TYPES,
        ISSUE_PRIORITIES,
    ):
        codes = [s.code for s in seeds]
        assert len(codes) == len(set(codes)), (
            f"duplicate codes in {seeds[0].__class__.__name__}"
        )


def test_requirement_status_rejects_uppercase_code() -> None:
    with pytest.raises(ValidationError):
        RequirementStatusSeed(code="DRAFT", label="x", description="x", sort_order=0)


def test_requirement_type_rejects_non_three_letter_code() -> None:
    with pytest.raises(ValidationError):
        RequirementTypeSeed(
            code="FUNCTIONAL",
            key="functional",
            label="x",
            description="x",
            sort_order=0,
        )


def test_issue_priority_rejects_negative_severity() -> None:
    with pytest.raises(ValidationError):
        IssuePrioritySeed(
            code="LOW", label="x", description="x", severity_order=-1, sort_order=0
        )


def test_seed_models_are_frozen() -> None:
    seed = IssueStatusSeed(code="open", label="Open", description="x", sort_order=0)
    with pytest.raises(ValidationError):
        seed.label = "Other"  # type: ignore[misc]


def test_issue_types_have_required_codes() -> None:
    expected = {
        "AMB",
        "GAP",
        "CNF",
        "RSK",
        "BLK",
        "QST",
        "DEC",
        "EVD",
        "VAL",
        "CHG",
        "MSC",
    }
    actual = {s.code for s in ISSUE_TYPES}
    assert actual == expected
