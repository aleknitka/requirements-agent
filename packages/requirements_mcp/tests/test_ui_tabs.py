"""Smoke tests for each Gradio tab builder in :mod:`requirements_mcp.ui`.

Each builder must be callable inside a fresh ``gr.Blocks`` scope
without raising. We do not exercise the Gradio launch — the goal is
to catch widget construction errors and import-time regressions.
"""

from __future__ import annotations

import gradio as gr
import pytest

from requirements_mcp.ui import (
    build_audit_tab,
    build_issues_tab,
    build_metadata_tab,
    build_requirements_tab,
)
from requirements_mcp.ui._helpers import (
    format_diff,
    lines_to_list,
    list_to_lines,
    safe_strip,
    selected_row_id,
)


class _TestableBuilder:
    """Wrap a tab builder so it can be called inside a Blocks scope."""

    def __init__(self, builder, factory) -> None:
        self.builder = builder
        self.factory = factory

    def run(self) -> gr.Blocks:
        with gr.Blocks() as scope:
            self.builder(self.factory)
        return scope


def test_requirements_tab_builds(seeded_session_factory) -> None:
    scope = _TestableBuilder(build_requirements_tab, seeded_session_factory).run()
    assert isinstance(scope, gr.Blocks)


def test_issues_tab_builds(seeded_session_factory) -> None:
    scope = _TestableBuilder(build_issues_tab, seeded_session_factory).run()
    assert isinstance(scope, gr.Blocks)


def test_audit_tab_builds(seeded_session_factory) -> None:
    scope = _TestableBuilder(build_audit_tab, seeded_session_factory).run()
    assert isinstance(scope, gr.Blocks)


def test_metadata_tab_builds(seeded_session_factory) -> None:
    scope = _TestableBuilder(build_metadata_tab, seeded_session_factory).run()
    assert isinstance(scope, gr.Blocks)


# ---- _helpers.py --------------------------------------------------------


def test_lines_to_list_strips_blanks() -> None:
    assert lines_to_list("a\n  \nb\n  c  ") == ["a", "b", "c"]
    assert lines_to_list("") == []
    assert lines_to_list(None) == []


def test_list_to_lines_roundtrip() -> None:
    assert list_to_lines(["a", "b"]) == "a\nb"
    assert list_to_lines([]) == ""
    assert list_to_lines(None) == ""


def test_safe_strip() -> None:
    assert safe_strip(" foo  ") == "foo"
    assert safe_strip(None) == ""
    assert safe_strip("") == ""


def test_format_diff_renders_each_field() -> None:
    diff = {
        "status_code": {"from": "draft", "to": "approved"},
        "users": {"from": ["a"], "to": ["a", "b"]},
    }
    rendered = format_diff(diff)
    assert "status_code: draft -> approved" in rendered
    assert 'users: ["a"] -> ["a", "b"]' in rendered


def test_format_diff_empty() -> None:
    assert format_diff({}) == "(no field changes)"


# ---- selected_row_id ----------------------------------------------------


class _FakeSelect:
    """Stand-in for ``gradio.SelectData`` carrying just the ``index`` attr."""

    def __init__(self, index) -> None:
        self.index = index


def test_selected_row_id_from_list_of_lists() -> None:
    table = [["REQ-FUN-aaaaaa", "title-1"], ["REQ-USR-bbbbbb", "title-2"]]
    assert selected_row_id(table, _FakeSelect([1, 0])) == "REQ-USR-bbbbbb"


def test_selected_row_id_from_pandas_dataframe() -> None:
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame(
        [["REQ-FUN-aaaaaa", "title-1"], ["REQ-USR-bbbbbb", "title-2"]],
        columns=["id", "title"],
    )
    # Regression for issue #8: clicking a row passed a DataFrame to the
    # callback and the old ``if not table`` truth-test crashed.
    assert selected_row_id(df, _FakeSelect([0, 0])) == "REQ-FUN-aaaaaa"


def test_selected_row_id_handles_empty_dataframe() -> None:
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame([], columns=["id"])
    assert selected_row_id(df, _FakeSelect([0, 0])) is None


def test_selected_row_id_handles_no_selection() -> None:
    assert selected_row_id([["x"]], _FakeSelect(None)) is None
    assert selected_row_id(None, _FakeSelect([0, 0])) is None
    assert selected_row_id([], _FakeSelect([0, 0])) is None


def test_selected_row_id_handles_empty_row() -> None:
    assert selected_row_id([[]], _FakeSelect([0, 0])) is None
