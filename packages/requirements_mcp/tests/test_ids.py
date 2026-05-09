"""Tests for the typed identifier helpers in :mod:`requirements_mcp.ids`."""

from __future__ import annotations

import re

from requirements_mcp.ids import (
    new_issue_id,
    new_issue_update_id,
    new_requirement_change_id,
    new_requirement_id,
)

_SUFFIX = r"[A-Za-z0-9]{6}"


def test_new_requirement_id_shape() -> None:
    rid = new_requirement_id("USR")
    assert re.fullmatch(rf"REQ-USR-{_SUFFIX}", rid)


def test_new_issue_id_shape() -> None:
    iid = new_issue_id("BLK")
    assert re.fullmatch(rf"ISSUE-BLK-{_SUFFIX}", iid)


def test_new_requirement_change_id_shape() -> None:
    cid = new_requirement_change_id()
    assert re.fullmatch(rf"REQ-UPDATE-{_SUFFIX}", cid)


def test_new_issue_update_id_shape() -> None:
    uid = new_issue_update_id()
    assert re.fullmatch(rf"ISSUE-UPDATE-{_SUFFIX}", uid)


def test_ids_are_unique_across_calls() -> None:
    ids = {new_requirement_id("FUN") for _ in range(200)}
    assert len(ids) == 200
