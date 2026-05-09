"""Gradio UI tabs for the requirements MCP app.

Each module here exposes a ``build_*_tab(session_factory)`` function
that constructs widgets and click handlers inside the current
:class:`gradio.Blocks` scope. Tab builders only consume the
:mod:`requirements_mcp.tools` layer; they never import services or
ORM classes directly. UI handlers are deliberately registered without
``api_name`` so they do not pollute the MCP tool surface — the only
canonical machine surface is the :func:`gradio.api` registrations in
:func:`requirements_mcp.app.build_app`.
"""

from requirements_mcp.ui.audit_tab import build_audit_tab
from requirements_mcp.ui.issues_tab import build_issues_tab
from requirements_mcp.ui.metadata_tab import build_metadata_tab
from requirements_mcp.ui.requirements_tab import build_requirements_tab

__all__ = [
    "build_audit_tab",
    "build_issues_tab",
    "build_metadata_tab",
    "build_requirements_tab",
]
