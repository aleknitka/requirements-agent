"""Gradio tab for the issue subsystem.

Same shape as the Requirements tab, plus controls for the operations
unique to issues:

* **Add update** — append an action-log entry without changing fields.
* **Link to requirement** — typed many-to-many link with audit row.
* **Quick filters** — `Open` and `Blocking` shortcut buttons that
  bypass the search form.
"""

from __future__ import annotations

from typing import Any, cast

import gradio as gr
from sqlalchemy.orm import Session, sessionmaker

from requirements_mcp.schemas.issues import (
    IssueCreate,
    IssuePriorityCode,
    IssueSearchQuery,
    IssueStatusCode,
    IssueTypeCode,
    IssueUpdate,
    IssueUpdateAdd,
    IssueUpdateTypeCode,
    RequirementIssueLinkCreate,
    RequirementIssueLinkType,
)
from requirements_mcp.seeds.issue_priorities import ISSUE_PRIORITIES
from requirements_mcp.seeds.issue_statuses import ISSUE_STATUSES
from requirements_mcp.seeds.issue_types import ISSUE_TYPES
from requirements_mcp.services.issues import (
    IssueNotFoundError,
    RequirementIssueLinkAlreadyExistsError,
    RequirementIssueLinkNotFoundError,
)
from requirements_mcp.services.requirements import RequirementNotFoundError
from requirements_mcp.tools import issues as tools
from requirements_mcp.ui._helpers import format_diff, rows_to_table, safe_strip

__all__ = ["build_issues_tab"]

_SEARCH_COLUMNS = [
    "id",
    "title",
    "issue_type_code",
    "status_code",
    "priority_code",
    "owner",
    "date_updated",
]


_LINK_TYPES = (
    "related",
    "blocks",
    "clarifies",
    "conflicts_with",
    "risk_for",
    "caused_by",
    "resolved_by",
)

_UPDATE_KINDS = (
    "note",
    "email_sent",
    "email_received",
    "evidence_added",
    "requirement_updated",
    "stakeholder_question_asked",
    "resolution_proposed",
    "issue_resolved",
    "issue_reopened",
)


def build_issues_tab(session_factory: sessionmaker[Session]) -> None:
    """Build the Issues tab in the current Blocks scope.

    Args:
        session_factory: Active session factory bound to the target DB.
    """
    status_choices = [s.code for s in ISSUE_STATUSES]
    type_choices = [t.code for t in ISSUE_TYPES]
    priority_choices = [p.code for p in ISSUE_PRIORITIES]

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Search")
            query = gr.Textbox(label="Free-text query", placeholder="tokens (AND)")
            with gr.Row():
                status_filter = gr.Dropdown(
                    choices=status_choices, label="Status", multiselect=True
                )
                type_filter = gr.Dropdown(
                    choices=type_choices, label="Type", multiselect=True
                )
                priority_filter = gr.Dropdown(
                    choices=priority_choices,
                    label="Priority",
                    multiselect=True,
                )
            owner_filter = gr.Textbox(label="Owner (exact match)")
            search_button = gr.Button("Search", variant="primary")
            with gr.Row():
                open_button = gr.Button("Show open")
                blocking_button = gr.Button("Show blocking")
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
                    view_id = gr.Textbox(label="Issue id", interactive=False)
                    view_summary = gr.Markdown()
                    view_history = gr.Dataframe(
                        headers=[
                            "date",
                            "kind",
                            "author",
                            "description",
                            "diff",
                        ],
                        label="Audit / action log",
                        interactive=False,
                        wrap=True,
                    )
                    view_refresh = gr.Button("Reload")

                with gr.Tab("Create"):
                    c_title = gr.Textbox(label="Title")
                    c_description = gr.Textbox(label="Description", lines=3)
                    with gr.Row():
                        c_type = gr.Dropdown(
                            choices=type_choices, label="Type", value="AMB"
                        )
                        c_status = gr.Dropdown(
                            choices=status_choices,
                            label="Status",
                            value="open",
                        )
                        c_priority = gr.Dropdown(
                            choices=priority_choices,
                            label="Priority",
                            value="MED",
                        )
                    with gr.Row():
                        c_created_by = gr.Textbox(label="Raised by")
                        c_owner = gr.Textbox(
                            label="Owner (optional)", placeholder="leave empty if none"
                        )
                    c_impact = gr.Textbox(label="Impact", lines=2)
                    c_risk = gr.Textbox(label="Risk", lines=2)
                    c_resolution = gr.Textbox(label="Proposed resolution", lines=2)
                    c_submit = gr.Button("Create issue", variant="primary")
                    c_status_box = gr.Markdown()

                with gr.Tab("Edit"):
                    e_id = gr.Textbox(label="Issue id", interactive=False)
                    e_title = gr.Textbox(label="Title")
                    e_description = gr.Textbox(label="Description", lines=3)
                    with gr.Row():
                        e_type = gr.Dropdown(choices=type_choices, label="Type")
                        e_status = gr.Dropdown(choices=status_choices, label="Status")
                        e_priority = gr.Dropdown(
                            choices=priority_choices, label="Priority"
                        )
                    e_owner = gr.Textbox(
                        label="Owner",
                        placeholder="leave empty to clear",
                    )
                    e_impact = gr.Textbox(label="Impact", lines=2)
                    e_risk = gr.Textbox(label="Risk", lines=2)
                    e_resolution = gr.Textbox(label="Proposed resolution", lines=2)
                    with gr.Row():
                        e_author = gr.Textbox(label="Editing author")
                        e_change_desc = gr.Textbox(label="Change description")
                    e_submit = gr.Button("Save changes", variant="primary")
                    e_status_box = gr.Markdown()

                with gr.Tab("Add update"):
                    u_id = gr.Textbox(
                        label="Issue id (set from selected row)",
                        interactive=False,
                    )
                    u_kind = gr.Dropdown(
                        choices=list(_UPDATE_KINDS),
                        label="Update type",
                        value="note",
                    )
                    u_description = gr.Textbox(label="Description", lines=2)
                    u_action_taken = gr.Textbox(label="Action taken", lines=2)
                    u_action_result = gr.Textbox(label="Action result", lines=2)
                    u_author = gr.Textbox(label="Author")
                    u_submit = gr.Button("Append update", variant="primary")
                    u_status_box = gr.Markdown()

                with gr.Tab("Link / unlink"):
                    l_id = gr.Textbox(
                        label="Issue id (set from selected row)",
                        interactive=False,
                    )
                    l_req_id = gr.Textbox(label="Requirement id")
                    with gr.Row():
                        l_type = gr.Dropdown(
                            choices=list(_LINK_TYPES),
                            label="Link type",
                            value="related",
                        )
                        l_author = gr.Textbox(label="Author")
                    l_rationale = gr.Textbox(label="Rationale")
                    with gr.Row():
                        l_link_button = gr.Button("Link", variant="primary")
                        l_unlink_button = gr.Button("Unlink")
                    l_status_box = gr.Markdown()

    # ---- Search ---------------------------------------------------------------

    def _do_search(
        text: str,
        statuses: list[str] | None,
        types: list[str] | None,
        priorities: list[str] | None,
        owner: str,
    ) -> list[list[Any]]:
        payload = IssueSearchQuery(
            query=safe_strip(text),
            status_codes=cast("list[IssueStatusCode] | None", statuses or None),
            type_codes=cast("list[IssueTypeCode] | None", types or None),
            priority_codes=cast("list[IssuePriorityCode] | None", priorities or None),
            owner=safe_strip(owner) or None,
        )
        rows = tools.search_issues(session_factory, payload)
        return rows_to_table(rows, _SEARCH_COLUMNS)

    search_button.click(
        _do_search,
        inputs=[query, status_filter, type_filter, priority_filter, owner_filter],
        outputs=results,
    )

    def _show_open() -> list[list[Any]]:
        rows = tools.list_open_issues(session_factory)
        return rows_to_table(rows, _SEARCH_COLUMNS)

    def _show_blocking() -> list[list[Any]]:
        rows = tools.list_blocking_issues(session_factory)
        return rows_to_table(rows, _SEARCH_COLUMNS)

    open_button.click(_show_open, outputs=results)
    blocking_button.click(_show_blocking, outputs=results)

    # ---- Selecting a row populates View / Edit / Add update / Link ----------

    select_outputs = [
        view_id,
        view_summary,
        view_history,
        # Edit prefill
        e_id,
        e_title,
        e_description,
        e_type,
        e_status,
        e_priority,
        e_owner,
        e_impact,
        e_risk,
        e_resolution,
        # Sub-tab id pickers
        u_id,
        l_id,
    ]

    def _empty_select() -> tuple:
        return (
            "",  # view_id
            "_No issue selected._",
            [],
            "",  # e_id
            "",  # e_title
            "",  # e_description
            "AMB",
            "open",
            "MED",
            "",
            "",
            "",
            "",
            "",  # u_id
            "",  # l_id
        )

    def _load_detail(issue_id: str) -> tuple:
        issue = tools.get_issue(session_factory, issue_id)
        if issue is None:
            return (
                "",
                f"_Issue `{issue_id}` not found._",
                [],
                "",
                "",
                "",
                "AMB",
                "open",
                "MED",
                "",
                "",
                "",
                "",
                "",
                "",
            )
        history = tools.list_issue_updates(session_factory, issue_id)
        history_rows = [
            [
                row.date.isoformat() if row.date else "",
                row.update_type_code,
                row.author,
                row.description,
                format_diff(row.diff),
            ]
            for row in history
        ]
        closed_line = (
            f"- **closed**: {issue.date_closed.isoformat()}\n"
            if issue.date_closed
            else ""
        )
        owner_line = (
            f"- **owner**: {issue.owner}\n"
            if issue.owner
            else "- **owner**: _(unassigned)_\n"
        )
        summary = (
            f"### {issue.title}\n\n"
            f"- **id**: `{issue.id}`\n"
            f"- **type**: `{issue.issue_type_code}` "
            f"· **status**: `{issue.status_code}` "
            f"· **priority**: `{issue.priority_code}`\n"
            + owner_line
            + f"- **created by**: {issue.created_by}\n"
            f"- **created**: {issue.date_created.isoformat()}\n"
            f"- **updated**: {issue.date_updated.isoformat()}\n"
            + closed_line
            + f"\n**Description**\n\n{issue.description}\n"
            + (f"\n**Impact**\n\n{issue.impact}\n" if issue.impact else "")
            + (f"\n**Risk**\n\n{issue.risk}\n" if issue.risk else "")
            + (
                f"\n**Proposed resolution**\n\n{issue.proposed_resolution}\n"
                if issue.proposed_resolution
                else ""
            )
        )
        return (
            issue.id,
            summary,
            history_rows,
            issue.id,
            issue.title,
            issue.description,
            issue.issue_type_code,
            issue.status_code,
            issue.priority_code,
            issue.owner or "",
            issue.impact,
            issue.risk,
            issue.proposed_resolution,
            issue.id,  # u_id
            issue.id,  # l_id
        )

    def _select_row(evt: gr.SelectData, table: list[list[Any]]) -> tuple:
        if not table or evt.index is None:
            return _empty_select()
        row_index = evt.index[0]
        return _load_detail(table[row_index][0])

    results.select(_select_row, inputs=results, outputs=select_outputs)
    view_refresh.click(_load_detail, inputs=view_id, outputs=select_outputs)

    # ---- Create ---------------------------------------------------------------

    def _do_create(
        title: str,
        description: str,
        issue_type: str,
        status: str,
        priority: str,
        created_by: str,
        owner: str,
        impact: str,
        risk: str,
        resolution: str,
    ) -> str:
        try:
            payload = IssueCreate(
                title=safe_strip(title),
                description=safe_strip(description),
                issue_type_code=cast(IssueTypeCode, issue_type),
                status_code=cast(IssueStatusCode, status),
                priority_code=cast(IssuePriorityCode, priority),
                impact=safe_strip(impact),
                risk=safe_strip(risk),
                proposed_resolution=safe_strip(resolution),
                owner=safe_strip(owner) or None,
                created_by=safe_strip(created_by),
            )
        except Exception as exc:  # pragma: no cover — defensive
            return f"❌ Validation error: {exc}"
        out = tools.create_issue(session_factory, payload)
        return (
            f"✅ Created issue `{out.id}` "
            f"({out.issue_type_code} · {out.status_code} · {out.priority_code})."
        )

    c_submit.click(
        _do_create,
        inputs=[
            c_title,
            c_description,
            c_type,
            c_status,
            c_priority,
            c_created_by,
            c_owner,
            c_impact,
            c_risk,
            c_resolution,
        ],
        outputs=c_status_box,
    )

    # ---- Edit ----------------------------------------------------------------

    def _do_edit(
        issue_id: str,
        title: str,
        description: str,
        issue_type: str,
        status: str,
        priority: str,
        owner: str,
        impact: str,
        risk: str,
        resolution: str,
        author: str,
        change_description: str,
    ) -> str:
        if not safe_strip(issue_id):
            return "❌ Select an issue from the search results first."
        owner_value: str | None = safe_strip(owner) or None
        try:
            payload = IssueUpdate(
                author=safe_strip(author),
                change_description=safe_strip(change_description) or "edit",
                title=safe_strip(title) or None,
                description=safe_strip(description) or None,
                issue_type_code=cast("IssueTypeCode | None", issue_type or None),
                status_code=cast("IssueStatusCode | None", status or None),
                priority_code=cast("IssuePriorityCode | None", priority or None),
                # owner is special: explicit empty -> None means "clear".
                owner=owner_value,
                impact=safe_strip(impact),
                risk=safe_strip(risk),
                proposed_resolution=safe_strip(resolution),
            )
        except Exception as exc:  # pragma: no cover — defensive
            return f"❌ Validation error: {exc}"

        try:
            out = tools.update_issue(session_factory, issue_id, payload)
        except IssueNotFoundError:
            return f"❌ Issue `{issue_id}` not found."
        return f"✅ Saved issue `{out.id}` (status `{out.status_code}`)."

    e_submit.click(
        _do_edit,
        inputs=[
            e_id,
            e_title,
            e_description,
            e_type,
            e_status,
            e_priority,
            e_owner,
            e_impact,
            e_risk,
            e_resolution,
            e_author,
            e_change_desc,
        ],
        outputs=e_status_box,
    )

    # ---- Add update ----------------------------------------------------------

    def _do_add_update(
        issue_id: str,
        kind: str,
        description: str,
        action_taken: str,
        action_result: str,
        author: str,
    ) -> str:
        if not safe_strip(issue_id):
            return "❌ Select an issue from the search results first."
        try:
            payload = IssueUpdateAdd(
                update_type_code=cast(IssueUpdateTypeCode, kind),
                description=safe_strip(description),
                author=safe_strip(author),
                action_taken=safe_strip(action_taken),
                action_result=safe_strip(action_result),
            )
        except Exception as exc:  # pragma: no cover — defensive
            return f"❌ Validation error: {exc}"
        try:
            out = tools.add_issue_update(session_factory, issue_id, payload)
        except IssueNotFoundError:
            return f"❌ Issue `{issue_id}` not found."
        return f"✅ Appended update `{out.id}` ({out.update_type_code})."

    u_submit.click(
        _do_add_update,
        inputs=[
            u_id,
            u_kind,
            u_description,
            u_action_taken,
            u_action_result,
            u_author,
        ],
        outputs=u_status_box,
    )

    # ---- Link / Unlink -------------------------------------------------------

    def _do_link(
        issue_id: str,
        requirement_id: str,
        link_type: str,
        rationale: str,
        author: str,
    ) -> str:
        if not safe_strip(issue_id):
            return "❌ Select an issue from the search results first."
        if not safe_strip(requirement_id):
            return "❌ Provide a requirement id."
        try:
            payload = RequirementIssueLinkCreate(
                requirement_id=safe_strip(requirement_id),
                link_type=cast(RequirementIssueLinkType, link_type),
                rationale=safe_strip(rationale),
                author=safe_strip(author),
            )
        except Exception as exc:  # pragma: no cover — defensive
            return f"❌ Validation error: {exc}"
        try:
            out = tools.link_issue_to_requirement(session_factory, issue_id, payload)
        except IssueNotFoundError:
            return f"❌ Issue `{issue_id}` not found."
        except RequirementNotFoundError:
            return f"❌ Requirement `{requirement_id}` not found."
        except RequirementIssueLinkAlreadyExistsError:
            return "❌ Link already exists between this issue and requirement."
        return (
            f"✅ Linked issue `{out.issue_id}` to requirement "
            f"`{out.requirement_id}` ({out.link_type})."
        )

    def _do_unlink(
        issue_id: str,
        requirement_id: str,
        rationale: str,
        author: str,
    ) -> str:
        if not safe_strip(issue_id) or not safe_strip(requirement_id):
            return "❌ Both issue id and requirement id are required."
        try:
            tools.unlink_issue_from_requirement(
                session_factory,
                safe_strip(issue_id),
                safe_strip(requirement_id),
                author=safe_strip(author),
                rationale=safe_strip(rationale),
            )
        except RequirementIssueLinkNotFoundError:
            return "❌ No such link."
        return f"✅ Unlinked issue `{issue_id}` from requirement `{requirement_id}`."

    l_link_button.click(
        _do_link,
        inputs=[l_id, l_req_id, l_type, l_rationale, l_author],
        outputs=l_status_box,
    )
    l_unlink_button.click(
        _do_unlink,
        inputs=[l_id, l_req_id, l_rationale, l_author],
        outputs=l_status_box,
    )
