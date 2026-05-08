"""Smoke tests for the Gradio + MCP app in :mod:`requirements_mcp.app`.

Avoids spinning up a live HTTP server. Verifies that:

* ``build_app(session_factory)`` constructs without raising and yields a
  Gradio Blocks instance.
* The set of API endpoints registered on that Blocks instance matches
  :data:`REGISTERED_TOOLS` exactly.
* The argument parser accepts the documented flags.
"""

from __future__ import annotations

import gradio as gr

from requirements_mcp.app import REGISTERED_TOOLS, _build_parser, build_app
from requirements_mcp.tools import issues as issue_tools
from requirements_mcp.tools import requirements as req_tools


def _registered_api_names(app: gr.Blocks) -> set[str]:
    """Return the set of api_name strings registered on a Gradio Blocks app.

    Pulls from each ``Dependency``'s ``api_name`` attribute. The
    representation matches what Gradio publishes via its API and MCP
    introspection, so this is the same surface an MCP client would see.
    """
    names: set[str] = set()
    for dep in app.fns.values():
        api_name = getattr(dep, "api_name", None)
        if isinstance(api_name, str):
            names.add(api_name)
    return names


def test_build_app_returns_blocks(seeded_session_factory) -> None:
    app = build_app(seeded_session_factory)
    assert isinstance(app, gr.Blocks)


def test_all_seventeen_tools_registered(seeded_session_factory) -> None:
    app = build_app(seeded_session_factory)
    registered = _registered_api_names(app)
    assert set(REGISTERED_TOOLS).issubset(registered), (
        f"missing: {set(REGISTERED_TOOLS) - registered}"
    )


def test_registered_tools_count() -> None:
    assert len(REGISTERED_TOOLS) == 17
    assert len(set(REGISTERED_TOOLS)) == 17


def test_tool_modules_export_expected_callables() -> None:
    """The tool modules must export the seventeen functions REGISTERED_TOOLS lists."""
    requirement_tools = {
        "create_requirement",
        "update_requirement",
        "get_requirement",
        "search_requirements",
        "list_requirement_changes",
        "list_requirement_statuses",
        "list_requirement_types",
    }
    issue_tool_names = {
        "create_issue",
        "update_issue",
        "get_issue",
        "search_issues",
        "list_issue_updates",
        "list_open_issues",
        "list_blocking_issues",
        "add_issue_update",
        "link_issue_to_requirement",
        "unlink_issue_from_requirement",
    }
    for name in requirement_tools:
        assert callable(getattr(req_tools, name))
    for name in issue_tool_names:
        assert callable(getattr(issue_tools, name))
    assert requirement_tools | issue_tool_names == set(REGISTERED_TOOLS)


def test_parser_accepts_documented_flags() -> None:
    parser = _build_parser()
    args = parser.parse_args(
        [
            "--db",
            "/tmp/x.db",
            "--log-level",
            "DEBUG",
            "--no-init",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--share",
        ]
    )
    assert args.db == "/tmp/x.db"
    assert args.log_level == "DEBUG"
    assert args.no_init is True
    assert args.host == "0.0.0.0"
    assert args.port == 8000
    assert args.share is True


def test_parser_defaults() -> None:
    args = _build_parser().parse_args([])
    assert args.db is None
    assert args.log_level == "INFO"
    assert args.no_init is False
    assert args.host == "127.0.0.1"
    assert args.port == 7860
    assert args.share is False
