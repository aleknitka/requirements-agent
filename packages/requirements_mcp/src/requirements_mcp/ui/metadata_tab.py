"""Gradio tab listing the controlled vocabularies (read-only).

Shows requirement statuses, requirement types, issue statuses, issue
types, and issue priorities as plain dataframes. Useful as a quick
reference when filling in the forms on other tabs and when the user
wants to confirm a code is valid.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from sqlalchemy.orm import Session, sessionmaker

from requirements_mcp.tools import issues as issue_tools
from requirements_mcp.tools import requirements as req_tools

__all__ = ["build_metadata_tab"]


def _to_table(rows: list[Any], columns: list[str]) -> list[list[Any]]:
    """Project Pydantic Out-models to a Dataframe payload."""
    return [[getattr(row, col, None) for col in columns] for row in rows]


def build_metadata_tab(session_factory: sessionmaker[Session]) -> None:
    """Build the Metadata tab in the current Blocks scope.

    Tables are populated lazily by a Refresh button rather than at app
    construction time, so the UI builds even if the database hasn't
    been seeded yet.

    Args:
        session_factory: Active session factory bound to the target DB.
    """
    gr.Markdown(
        "Read-only view of the controlled vocabularies. Click **Refresh** to load."
    )
    refresh = gr.Button("Refresh", variant="primary")

    with gr.Tabs():
        with gr.Tab("Requirement statuses"):
            req_status_table = gr.Dataframe(
                headers=[
                    "code",
                    "label",
                    "is_active",
                    "is_terminal",
                    "sort_order",
                    "description",
                ],
                interactive=False,
                wrap=True,
            )
        with gr.Tab("Requirement types"):
            req_type_table = gr.Dataframe(
                headers=["code", "key", "label", "sort_order", "description"],
                interactive=False,
                wrap=True,
            )
        with gr.Tab("Issue statuses"):
            issue_status_table = gr.Dataframe(
                headers=[
                    "code",
                    "label",
                    "is_terminal",
                    "sort_order",
                    "description",
                ],
                interactive=False,
                wrap=True,
            )
        with gr.Tab("Issue types"):
            issue_type_table = gr.Dataframe(
                headers=["code", "key", "label", "sort_order", "description"],
                interactive=False,
                wrap=True,
            )
        with gr.Tab("Issue priorities"):
            issue_priority_table = gr.Dataframe(
                headers=[
                    "code",
                    "label",
                    "severity_order",
                    "sort_order",
                    "description",
                ],
                interactive=False,
                wrap=True,
            )

    def _refresh() -> tuple[
        list[list[Any]],
        list[list[Any]],
        list[list[Any]],
        list[list[Any]],
        list[list[Any]],
    ]:
        return (
            _to_table(
                req_tools.list_requirement_statuses(session_factory),
                [
                    "code",
                    "label",
                    "is_active",
                    "is_terminal",
                    "sort_order",
                    "description",
                ],
            ),
            _to_table(
                req_tools.list_requirement_types(session_factory),
                ["code", "key", "label", "sort_order", "description"],
            ),
            _to_table(
                issue_tools.list_issue_statuses(session_factory),
                ["code", "label", "is_terminal", "sort_order", "description"],
            ),
            _to_table(
                issue_tools.list_issue_types(session_factory),
                ["code", "key", "label", "sort_order", "description"],
            ),
            _to_table(
                issue_tools.list_issue_priorities(session_factory),
                ["code", "label", "severity_order", "sort_order", "description"],
            ),
        )

    refresh.click(
        _refresh,
        outputs=[
            req_status_table,
            req_type_table,
            issue_status_table,
            issue_type_table,
            issue_priority_table,
        ],
    )
