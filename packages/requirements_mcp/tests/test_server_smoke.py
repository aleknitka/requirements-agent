"""Smoke tests for the MCP server registration in :mod:`requirements_mcp.server`.

These tests do not exercise the stdio transport; they confirm that
``make_server`` registers every expected tool name without raising and
that the entry-point parser accepts the documented flags.
"""

from __future__ import annotations

import asyncio

from requirements_mcp.server import REGISTERED_TOOLS, _build_parser, make_server


def test_make_server_registers_all_tools(seeded_session_factory) -> None:
    server = make_server(seeded_session_factory)
    registered = {tool.name for tool in asyncio.run(server.list_tools())}
    assert set(REGISTERED_TOOLS).issubset(registered)


def test_registered_tools_count() -> None:
    assert len(REGISTERED_TOOLS) == 7
    assert len(set(REGISTERED_TOOLS)) == 7


def test_parser_accepts_documented_flags() -> None:
    parser = _build_parser()
    args = parser.parse_args(["--db", "/tmp/x.db", "--log-level", "DEBUG", "--no-init"])
    assert args.db == "/tmp/x.db"
    assert args.log_level == "DEBUG"
    assert args.no_init is True


def test_parser_defaults() -> None:
    args = _build_parser().parse_args([])
    assert args.db is None
    assert args.log_level == "INFO"
    assert args.no_init is False
