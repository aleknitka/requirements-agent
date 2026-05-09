"""Gradio tab for browsing the audit log of a requirement or an issue.

The Requirements and Issues tabs already render history inline next to
the row they're showing. This tab is for the case where you have an id
in hand (from a chat transcript, an email, an MCP client) and want to
see its full change history without going through the search list.
"""

from __future__ import annotations

from typing import Any

import gradio as gr
from sqlalchemy.orm import Session, sessionmaker

from requirements_mcp.services.issues import IssueNotFoundError
from requirements_mcp.services.requirements import RequirementNotFoundError
from requirements_mcp.tools import issues as issue_tools
from requirements_mcp.tools import requirements as req_tools
from requirements_mcp.ui._helpers import format_diff, safe_strip

__all__ = ["build_audit_tab"]


def build_audit_tab(session_factory: sessionmaker[Session]) -> None:
    """Build the Audit tab in the current Blocks scope.

    Args:
        session_factory: Active session factory bound to the target DB.
    """
    gr.Markdown("Look up the full change history of a requirement or issue by id.")

    with gr.Row():
        kind = gr.Radio(
            choices=["requirement", "issue"],
            value="requirement",
            label="Subject",
        )
        target_id = gr.Textbox(label="Id")
        load_button = gr.Button("Load history", variant="primary")
    history = gr.Dataframe(
        headers=["date", "kind / change", "author", "description", "diff"],
        label="History",
        interactive=False,
        wrap=True,
    )
    status_box = gr.Markdown()

    def _load(subject: str, identifier: str) -> tuple[list[list[Any]], str]:
        ident = safe_strip(identifier)
        if not ident:
            return [], "❌ Provide an id to look up."
        try:
            if subject == "requirement":
                rows = req_tools.list_requirement_changes(session_factory, ident)
                table = [
                    [
                        row.date.isoformat() if row.date else "",
                        "change",
                        row.author,
                        row.change_description,
                        format_diff(row.diff),
                    ]
                    for row in rows
                ]
                return table, (f"✅ {len(rows)} entries for requirement `{ident}`.")
            rows = issue_tools.list_issue_updates(session_factory, ident)
            table = [
                [
                    row.date.isoformat() if row.date else "",
                    row.update_type_code,
                    row.author,
                    row.description,
                    format_diff(row.diff),
                ]
                for row in rows
            ]
            return table, f"✅ {len(rows)} entries for issue `{ident}`."
        except RequirementNotFoundError:
            return [], f"❌ Requirement `{ident}` not found."
        except IssueNotFoundError:
            return [], f"❌ Issue `{ident}` not found."

    load_button.click(_load, inputs=[kind, target_id], outputs=[history, status_box])
