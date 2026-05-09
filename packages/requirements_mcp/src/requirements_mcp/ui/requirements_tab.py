"""Gradio tab for the requirement subsystem.

Layout (all single-column inside one outer ``gr.Tabs``):

* **Search** — text query, status / type filters, lookup-by-id, then
  results table, then a detail panel with audit history.
* **Create** — full creation form. After a successful submit every
  input field is cleared so an accidental double-click cannot create
  the same requirement twice.
* **Update** — id input + Load button that prefills the form, then a
  Save button that writes through and logs the diff.

UI handlers reuse the :mod:`requirements_mcp.tools.requirements`
wrappers without giving them ``api_name``, so the MCP tool surface
stays exactly the seventeen registrations declared in
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


def _format_summary(req: Any) -> str:
    """Render a requirement detail summary as Markdown.

    Args:
        req: A :class:`RequirementOut` (or any object exposing the same
            attribute names).

    Returns:
        Markdown text suitable for a :class:`gradio.Markdown` block.
    """
    summary_md = (
        f"### {req.title}\n\n"
        f"- **id**: `{req.id}`\n"
        f"- **type**: `{req.type_code}` · **status**: `{req.status_code}` "
        f"· **version**: {req.version}\n"
        f"- **author**: {req.author}\n"
        f"- **created**: {req.date_created.isoformat()}\n"
        f"- **updated**: {req.date_updated.isoformat()}\n\n"
        f"**Statement**\n\n{req.requirement_statement}\n\n"
    )
    if req.extended_description:
        summary_md += f"**Extended description**\n\n{req.extended_description}\n\n"
    if req.acceptance_criteria:
        summary_md += "**Acceptance criteria**\n" + "".join(
            f"- {c}\n" for c in req.acceptance_criteria
        )
    return summary_md


def build_requirements_tab(session_factory: sessionmaker[Session]) -> None:
    """Build the Requirements tab in the current Blocks scope.

    Args:
        session_factory: Active session factory bound to the target DB.
            Closures formed here capture it.
    """
    status_choices = [s.code for s in REQUIREMENT_STATUSES]
    type_choices = [t.code for t in REQUIREMENT_TYPES]

    with gr.Tabs():
        # ===== Search ======================================================
        with gr.Tab("Search"):
            gr.Markdown("### Search")
            search_query = gr.Textbox(
                label="Free-text query",
                placeholder="space-separated tokens; AND across them",
            )
            status_filter = gr.Dropdown(
                choices=status_choices, label="Status", multiselect=True
            )
            type_filter = gr.Dropdown(
                choices=type_choices, label="Type", multiselect=True
            )
            lookup_id = gr.Textbox(
                label="Lookup by id",
                placeholder="REQ-<TYPE>-xxxxxx — populates details directly",
            )
            with gr.Row():
                search_button = gr.Button("Search", variant="primary")
                lookup_button = gr.Button("Load by id")
            results = gr.Dataframe(
                headers=_SEARCH_COLUMNS,
                datatype=["str"] * len(_SEARCH_COLUMNS),
                label="Results",
                interactive=False,
                wrap=True,
            )

            gr.Markdown("---")
            gr.Markdown("### Details")
            view_id = gr.Textbox(label="Requirement id", interactive=False)
            view_summary = gr.Markdown("_No requirement selected._")
            view_history = gr.Dataframe(
                headers=["date", "author", "change_description", "diff"],
                label="Audit history",
                interactive=False,
                wrap=True,
            )
            view_refresh = gr.Button("Reload")

        # ===== Create ======================================================
        with gr.Tab("Create"):
            c_title = gr.Textbox(label="Title")
            c_statement = gr.Textbox(label="Statement", lines=3)
            with gr.Row():
                c_type = gr.Dropdown(choices=type_choices, label="Type", value="FUN")
                c_status = gr.Dropdown(
                    choices=status_choices, label="Status", value="draft"
                )
                c_author = gr.Textbox(label="Author")
            c_extended = gr.Textbox(label="Extended description", lines=2)
            with gr.Accordion("Structured fields (one item per line)", open=False):
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

        # ===== Update ======================================================
        with gr.Tab("Update"):
            gr.Markdown(
                "### Update requirement\n\n"
                "Enter a requirement id and click **Load** to prefill the "
                "form."
            )
            with gr.Row():
                u_id = gr.Textbox(label="Requirement id")
                u_load = gr.Button("Load")
            u_load_status = gr.Markdown()

            e_title = gr.Textbox(label="Title")
            e_statement = gr.Textbox(label="Statement", lines=3)
            with gr.Row():
                e_type = gr.Dropdown(choices=type_choices, label="Type")
                e_status = gr.Dropdown(choices=status_choices, label="Status")
            e_extended = gr.Textbox(label="Extended description", lines=2)
            with gr.Accordion("Structured fields (one item per line)", open=False):
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

    # ---- Search handlers -----------------------------------------------------

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

    def _empty_detail(message: str = "_No requirement selected._") -> tuple:
        return ("", message, [])

    def _load_detail(req_id: str) -> tuple:
        req_id = safe_strip(req_id)
        if not req_id:
            return _empty_detail()
        req = tools.get_requirement(session_factory, req_id)
        if req is None:
            return _empty_detail(f"_Requirement `{req_id}` not found._")
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
        return (req.id, _format_summary(req), history_rows)

    detail_outputs = [view_id, view_summary, view_history]

    def _on_select(evt: gr.SelectData, table: Any) -> tuple:
        row_id = selected_row_id(table, evt)
        if row_id is None:
            return _empty_detail()
        return _load_detail(row_id)

    results.select(_on_select, inputs=results, outputs=detail_outputs)
    view_refresh.click(_load_detail, inputs=view_id, outputs=detail_outputs)
    lookup_button.click(_load_detail, inputs=lookup_id, outputs=detail_outputs)

    # ---- Create handler ------------------------------------------------------

    _CREATE_DEFAULTS: tuple[Any, ...] = (
        "",  # c_title
        "",  # c_statement
        "FUN",  # c_type
        "draft",  # c_status
        "",  # c_author
        "",  # c_extended
        "",  # c_users
        "",  # c_triggers
        "",  # c_pre
        "",  # c_post
        "",  # c_inputs
        "",  # c_outputs
        "",  # c_logic
        "",  # c_excs
        "",  # c_acc
    )

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
    ) -> tuple:
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
            # On validation error keep the user's typed values so they
            # can correct without retyping; only the status message
            # changes.
            return (
                title,
                statement,
                type_code,
                status_code,
                author,
                extended_description,
                users,
                triggers,
                preconditions,
                postconditions,
                inputs_,
                outputs,
                business_logic,
                exception_handling,
                acceptance_criteria,
                f"❌ Validation error: {exc}",
            )

        out = tools.create_requirement(session_factory, payload)
        message = (
            f"✅ Created requirement `{out.id}` "
            f"(version {out.version}, status {out.status_code})."
        )
        # On success, blank the form so a duplicate cannot be created
        # by an accidental second click.
        return (*_CREATE_DEFAULTS, message)

    create_inputs = [
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
    ]
    c_submit.click(
        _do_create,
        inputs=create_inputs,
        outputs=[*create_inputs, c_status_box],
    )

    # ---- Update handlers -----------------------------------------------------

    _UPDATE_BLANK: tuple[Any, ...] = (
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

    def _load_for_update(req_id: str) -> tuple:
        req_id = safe_strip(req_id)
        if not req_id:
            return (*_UPDATE_BLANK, "_Enter a requirement id first._")
        req = tools.get_requirement(session_factory, req_id)
        if req is None:
            return (*_UPDATE_BLANK, f"❌ Requirement `{req_id}` not found.")
        return (
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
            f"✅ Loaded `{req.id}` (v{req.version}, status {req.status_code}).",
        )

    update_form_outputs = [
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
    u_load.click(
        _load_for_update,
        inputs=u_id,
        outputs=[*update_form_outputs, u_load_status],
    )

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
            return "❌ Enter a requirement id and click Load first."
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
            u_id,
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
