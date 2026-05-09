"""Gradio tab for the requirement subsystem.

Layout:

* Left panel — search & list. Free-text query, status / type
  multi-select filters, and a results table. Selecting a row populates
  the right panel.
* Right panel — three sub-tabs: **View** (full detail + audit
  history), **Create** (form to add a new requirement), **Edit**
  (form prefilled from the selected row).

UI handlers reuse the :mod:`requirements_mcp.tools.requirements`
wrappers without giving them ``api_name``, so the MCP tool surface
remains exactly the seventeen registrations declared in
:func:`requirements_mcp.app.build_app`.
"""

from __future__ import annotations

from typing import Any, cast

import gradio as gr
from sqlalchemy.orm import Session, sessionmaker

from requirements_mcp.schemas.requirements import (
    RequirementCreate,
    RequirementSearchQuery,
    RequirementStatusCode,
    RequirementTypeCode,
    RequirementUpdate,
)
from requirements_mcp.seeds.requirement_statuses import REQUIREMENT_STATUSES
from requirements_mcp.seeds.requirement_types import REQUIREMENT_TYPES
from requirements_mcp.services.requirements import RequirementNotFoundError
from requirements_mcp.tools import requirements as tools
from requirements_mcp.ui._helpers import (
    format_diff,
    lines_to_list,
    list_to_lines,
    rows_to_table,
    safe_strip,
    selected_row_id,
)

__all__ = ["build_requirements_tab"]

_SEARCH_COLUMNS = [
    "id",
    "title",
    "type_code",
    "status_code",
    "version",
    "date_updated",
]


def build_requirements_tab(session_factory: sessionmaker[Session]) -> None:
    """Build the Requirements tab in the current Blocks scope.

    Args:
        session_factory: Active session factory bound to the target DB.
            Closures formed here capture it.
    """
    status_choices = [s.code for s in REQUIREMENT_STATUSES]
    type_choices = [t.code for t in REQUIREMENT_TYPES]

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Search")
            search_query = gr.Textbox(
                label="Free-text query",
                placeholder="space-separated tokens; AND across them",
            )
            with gr.Row():
                status_filter = gr.Dropdown(
                    choices=status_choices,
                    label="Status",
                    multiselect=True,
                )
                type_filter = gr.Dropdown(
                    choices=type_choices,
                    label="Type",
                    multiselect=True,
                )
            search_button = gr.Button("Search", variant="primary")
            results = gr.Dataframe(
                headers=_SEARCH_COLUMNS,
                datatype=["str"] * len(_SEARCH_COLUMNS),
                label="Results",
                interactive=False,
                wrap=True,
            )

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("View"):
                    view_id = gr.Textbox(label="Requirement id", interactive=False)
                    view_summary = gr.Markdown()
                    view_history = gr.Dataframe(
                        headers=["date", "author", "change_description", "diff"],
                        label="Audit history",
                        interactive=False,
                        wrap=True,
                    )
                    view_refresh = gr.Button("Reload")

                with gr.Tab("Create"):
                    c_title = gr.Textbox(label="Title")
                    c_statement = gr.Textbox(label="Statement", lines=3)
                    with gr.Row():
                        c_type = gr.Dropdown(
                            choices=type_choices, label="Type", value="FUN"
                        )
                        c_status = gr.Dropdown(
                            choices=status_choices,
                            label="Status",
                            value="draft",
                        )
                        c_author = gr.Textbox(label="Author")
                    c_extended = gr.Textbox(label="Extended description", lines=2)
                    with gr.Accordion(
                        "Structured fields (one item per line)", open=False
                    ):
                        c_users = gr.Textbox(label="Users", lines=2)
                        c_triggers = gr.Textbox(label="Triggers", lines=2)
                        c_pre = gr.Textbox(label="Preconditions", lines=2)
                        c_post = gr.Textbox(label="Postconditions", lines=2)
                        c_inputs = gr.Textbox(label="Inputs", lines=2)
                        c_outputs = gr.Textbox(label="Outputs", lines=2)
                        c_logic = gr.Textbox(label="Business logic", lines=2)
                        c_excs = gr.Textbox(label="Exception handling", lines=2)
                        c_acc = gr.Textbox(label="Acceptance criteria", lines=2)
                    c_submit = gr.Button("Create requirement", variant="primary")
                    c_status_box = gr.Markdown()

                with gr.Tab("Edit"):
                    e_id = gr.Textbox(
                        label="Requirement id (set from selected row)",
                        interactive=False,
                    )
                    e_title = gr.Textbox(label="Title")
                    e_statement = gr.Textbox(label="Statement", lines=3)
                    with gr.Row():
                        e_type = gr.Dropdown(choices=type_choices, label="Type")
                        e_status = gr.Dropdown(choices=status_choices, label="Status")
                    e_extended = gr.Textbox(label="Extended description", lines=2)
                    with gr.Accordion(
                        "Structured fields (one item per line)", open=False
                    ):
                        e_users = gr.Textbox(label="Users", lines=2)
                        e_triggers = gr.Textbox(label="Triggers", lines=2)
                        e_pre = gr.Textbox(label="Preconditions", lines=2)
                        e_post = gr.Textbox(label="Postconditions", lines=2)
                        e_inputs = gr.Textbox(label="Inputs", lines=2)
                        e_outputs = gr.Textbox(label="Outputs", lines=2)
                        e_logic = gr.Textbox(label="Business logic", lines=2)
                        e_excs = gr.Textbox(label="Exception handling", lines=2)
                        e_acc = gr.Textbox(label="Acceptance criteria", lines=2)
                    with gr.Row():
                        e_author = gr.Textbox(label="Editing author")
                        e_change_desc = gr.Textbox(label="Change description")
                    e_submit = gr.Button("Save changes", variant="primary")
                    e_status_box = gr.Markdown()

    # ---- Search ---------------------------------------------------------------

    def _do_search(
        query: str, statuses: list[str] | None, types: list[str] | None
    ) -> list[list[Any]]:
        payload = RequirementSearchQuery(
            query=safe_strip(query),
            status_codes=statuses or None,
            type_codes=types or None,
        )
        rows = tools.search_requirements(session_factory, payload)
        return rows_to_table(rows, _SEARCH_COLUMNS)

    search_button.click(
        _do_search,
        inputs=[search_query, status_filter, type_filter],
        outputs=results,
    )

    # ---- Selecting a row populates View and Edit -----------------------------

    def _empty_select() -> tuple:
        return (
            "",  # view_id
            "_No requirement selected._",
            [],
            # edit prefill (10 strings + 2 dropdowns)
            "",  # e_id
            "",  # e_title
            "",  # e_statement
            "FUN",  # e_type
            "draft",  # e_status
            "",  # e_extended
            "",  # e_users
            "",  # e_triggers
            "",  # e_pre
            "",  # e_post
            "",  # e_inputs
            "",  # e_outputs
            "",  # e_logic
            "",  # e_excs
            "",  # e_acc
        )

    def _select_row(evt: gr.SelectData, table: Any) -> tuple:
        row_id = selected_row_id(table, evt)
        if row_id is None:
            return _empty_select()
        return _load_detail(row_id)

    def _load_detail(req_id: str) -> tuple:
        req = tools.get_requirement(session_factory, req_id)
        if req is None:
            return (
                "",
                f"_Requirement `{req_id}` not found._",
                [],
                "",
                "",
                "",
                "FUN",
                "draft",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            )
        history = tools.list_requirement_changes(session_factory, req_id)
        history_rows = [
            [
                row.date.isoformat() if row.date else "",
                row.author,
                row.change_description,
                format_diff(row.diff),
            ]
            for row in history
        ]
        summary_md = (
            f"### {req.title}\n\n"
            f"- **id**: `{req.id}`\n"
            f"- **type**: `{req.type_code}` · **status**: `{req.status_code}` "
            f"· **version**: {req.version}\n"
            f"- **author**: {req.author}\n"
            f"- **created**: {req.date_created.isoformat()}\n"
            f"- **updated**: {req.date_updated.isoformat()}\n\n"
            f"**Statement**\n\n{req.requirement_statement}\n\n"
            + (
                f"**Extended description**\n\n{req.extended_description}\n\n"
                if req.extended_description
                else ""
            )
            + (
                "**Acceptance criteria**\n"
                + "".join(f"- {c}\n" for c in req.acceptance_criteria)
                if req.acceptance_criteria
                else ""
            )
        )
        return (
            req.id,
            summary_md,
            history_rows,
            req.id,
            req.title,
            req.requirement_statement,
            req.type_code,
            req.status_code,
            req.extended_description,
            list_to_lines(req.users),
            list_to_lines(req.triggers),
            list_to_lines(req.preconditions),
            list_to_lines(req.postconditions),
            list_to_lines(req.inputs),
            list_to_lines(req.outputs),
            list_to_lines(req.business_logic),
            list_to_lines(req.exception_handling),
            list_to_lines(req.acceptance_criteria),
        )

    select_outputs = [
        view_id,
        view_summary,
        view_history,
        e_id,
        e_title,
        e_statement,
        e_type,
        e_status,
        e_extended,
        e_users,
        e_triggers,
        e_pre,
        e_post,
        e_inputs,
        e_outputs,
        e_logic,
        e_excs,
        e_acc,
    ]
    results.select(_select_row, inputs=results, outputs=select_outputs)

    # Re-fetch detail and history on demand.
    view_refresh.click(_load_detail, inputs=view_id, outputs=select_outputs)

    # ---- Create ---------------------------------------------------------------

    def _do_create(
        title: str,
        statement: str,
        type_code: str,
        status_code: str,
        author: str,
        extended_description: str,
        users: str,
        triggers: str,
        preconditions: str,
        postconditions: str,
        inputs_: str,
        outputs: str,
        business_logic: str,
        exception_handling: str,
        acceptance_criteria: str,
    ) -> str:
        try:
            payload = RequirementCreate(
                title=safe_strip(title),
                requirement_statement=safe_strip(statement),
                type_code=cast(RequirementTypeCode, type_code),
                status_code=cast(RequirementStatusCode, status_code),
                author=safe_strip(author),
                extended_description=safe_strip(extended_description),
                users=lines_to_list(users),
                triggers=lines_to_list(triggers),
                preconditions=lines_to_list(preconditions),
                postconditions=lines_to_list(postconditions),
                inputs=lines_to_list(inputs_),
                outputs=lines_to_list(outputs),
                business_logic=lines_to_list(business_logic),
                exception_handling=lines_to_list(exception_handling),
                acceptance_criteria=lines_to_list(acceptance_criteria),
            )
        except Exception as exc:  # pragma: no cover — defensive
            return f"❌ Validation error: {exc}"

        out = tools.create_requirement(session_factory, payload)
        return (
            f"✅ Created requirement `{out.id}` "
            f"(version {out.version}, status {out.status_code})."
        )

    c_submit.click(
        _do_create,
        inputs=[
            c_title,
            c_statement,
            c_type,
            c_status,
            c_author,
            c_extended,
            c_users,
            c_triggers,
            c_pre,
            c_post,
            c_inputs,
            c_outputs,
            c_logic,
            c_excs,
            c_acc,
        ],
        outputs=c_status_box,
    )

    # ---- Edit ----------------------------------------------------------------

    def _do_edit(
        req_id: str,
        title: str,
        statement: str,
        type_code: str,
        status_code: str,
        extended_description: str,
        users: str,
        triggers: str,
        preconditions: str,
        postconditions: str,
        inputs_: str,
        outputs: str,
        business_logic: str,
        exception_handling: str,
        acceptance_criteria: str,
        author: str,
        change_description: str,
    ) -> str:
        if not safe_strip(req_id):
            return "❌ Select a requirement from the search results first."
        try:
            payload = RequirementUpdate(
                author=safe_strip(author),
                change_description=safe_strip(change_description) or "edit",
                title=safe_strip(title) or None,
                requirement_statement=safe_strip(statement) or None,
                type_code=cast("RequirementTypeCode | None", type_code or None),
                status_code=cast("RequirementStatusCode | None", status_code or None),
                extended_description=safe_strip(extended_description),
                users=lines_to_list(users),
                triggers=lines_to_list(triggers),
                preconditions=lines_to_list(preconditions),
                postconditions=lines_to_list(postconditions),
                inputs=lines_to_list(inputs_),
                outputs=lines_to_list(outputs),
                business_logic=lines_to_list(business_logic),
                exception_handling=lines_to_list(exception_handling),
                acceptance_criteria=lines_to_list(acceptance_criteria),
            )
        except Exception as exc:  # pragma: no cover — defensive
            return f"❌ Validation error: {exc}"

        try:
            out = tools.update_requirement(session_factory, req_id, payload)
        except RequirementNotFoundError:
            return f"❌ Requirement `{req_id}` not found."
        return (
            f"✅ Saved requirement `{out.id}` "
            f"(now version {out.version}, status {out.status_code})."
        )

    e_submit.click(
        _do_edit,
        inputs=[
            e_id,
            e_title,
            e_statement,
            e_type,
            e_status,
            e_extended,
            e_users,
            e_triggers,
            e_pre,
            e_post,
            e_inputs,
            e_outputs,
            e_logic,
            e_excs,
            e_acc,
            e_author,
            e_change_desc,
        ],
        outputs=e_status_box,
    )
