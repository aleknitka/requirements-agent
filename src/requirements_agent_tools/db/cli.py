"""Click CLI exposing full CRUD over a project database.

Each subcommand opens the single project SQLite file,
runs one operation, and prints the result as JSON to stdout. Errors are
logged via loguru and surfaced as a non-zero exit code.

Examples:
    db project show
    db req add --title "..." --by alice
    db req search --status open --priority high
    db req vec-search "fault tolerance" --top-k 5
    db minute list --unintegrated
"""

from __future__ import annotations

import json
import sqlite3
import sys
from typing import Any, NoReturn, Optional

import click
from loguru import logger
from tabulate import tabulate

from .. import CONSTANTS as C
from ..models import (
    IssuePriority,
    IssueStatus,
    ProjectMeta,
    ProjectPhase,
    RequirementIn,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from . import issues as issues_db
from . import projects as projects_db
from . import requirements as req_db
from . import updates as updates_db
from .connection import get_db
from .embeddings import vector_search


# ───────────────────── helpers ─────────────────────


def _emit(payload: dict) -> None:
    """Print ``payload`` as pretty JSON or human-readable text.

    Uses ``ctx.obj["format"]`` to determine the output style.
    """
    ctx = click.get_current_context()
    fmt = ctx.obj.get("format", "json")

    if fmt == "json":
        click.echo(json.dumps(payload, indent=2, default=str))
        return

    # ── Human-readable formatting ──
    # Check if payload is a collection (list) or single item
    for key in ["requirements", "issues", "updates", "actions", "projects"]:
        if key in payload and isinstance(payload[key], list):
            items = payload[key]
            if not items:
                click.secho(f"No {key} found.", fg="yellow")
                return
            click.secho(f"\n{key.upper()} ({len(items)})", fg="cyan", bold=True)
            click.echo(tabulate(items, headers="keys", tablefmt="simple"))
            return

    # Special case: single entities (e.g. "requirement", "issue", "project")
    for key in ["requirement", "issue", "project", "action"]:
        if key in payload and isinstance(payload[key], dict):
            data = payload[key]
            click.secho(
                f"\n{key.upper()}: {data.get('id', data.get('project_id', ''))}",
                fg="cyan",
                bold=True,
            )

            # Print main fields
            main_fields = {
                k: v for k, v in data.items() if not isinstance(v, (list, dict))
            }
            click.echo(tabulate(main_fields.items(), tablefmt="plain"))

            # Print nested lists (e.g. stakeholders, updates, actions)
            for k, v in data.items():
                if isinstance(v, list) and v:
                    click.secho(f"\n{k.upper()}:", fg="blue", bold=True)
                    if all(isinstance(i, dict) for i in v):
                        click.echo(tabulate(v, headers="keys", tablefmt="simple"))
                    else:
                        for i in v:
                            click.echo(f" - {i}")
            return

    # Fallback for unexpected shapes
    click.echo(json.dumps(payload, indent=2, default=str))


def _fail(msg: str, exit_code: int = 1) -> NoReturn:
    """Log an error and exit with the given code."""
    logger.error(msg)
    click.echo(json.dumps({"ok": False, "error": msg}, default=str), err=True)
    sys.exit(exit_code)


def _open_conn() -> sqlite3.Connection:
    """Open the single project database."""
    return get_db(str(C.DB_PATH))


def _parse_json_list(raw: Optional[str], label: str) -> list[Any]:
    """Decode a CLI-supplied JSON array; abort on malformed input."""
    if not raw:
        return []
    try:
        v = json.loads(raw)
    except json.JSONDecodeError as e:
        _fail(f"--{label} is not valid JSON: {e}")
    if not isinstance(v, list):
        _fail(f"--{label} must decode to a JSON array")
    return v


# ───────────────────── root group ─────────────────────


@click.group(help=(__doc__ or "").split("\n", 1)[0])
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "human"]),
    default="json",
    help="Output format (default: json).",
)
@click.pass_context
def cli(ctx: click.Context, output_format: str) -> None:
    """Entry point for the db CLI.

    Args:
        ctx: Click context object.
        output_format: Desired output style (json or human).
    """
    ctx.ensure_object(dict)
    ctx.obj["format"] = output_format


# ───────────────────── project subgroup ─────────────────────


@cli.group(help="Project metadata commands.")
def project() -> None:
    """Project metadata subcommands."""


@project.command("show", help="Show the project metadata as JSON.")
@click.pass_context
def project_show(ctx: click.Context) -> None:
    """Display the project metadata row as JSON.

    Args:
        ctx: Click context.
    """
    conn = _open_conn()
    meta = projects_db.get_project(conn)
    if not meta:
        _fail("No project found in database.")
    _emit({"ok": True, "project": meta.model_dump(mode="json")})


@project.command("list", help="List project(s) matching filters.")
@click.option("--name")
@click.option("--code")
@click.option("--phase", type=click.Choice([p.value for p in ProjectPhase]))
@click.option("--owner", "project_owner")
@click.pass_context
def project_list(
    ctx: click.Context,
    name: Optional[str],
    code: Optional[str],
    phase: Optional[str],
    project_owner: Optional[str],
) -> None:
    """Search for the singleton project row using any parameter."""
    conn = _open_conn()
    rows = projects_db.search_projects(
        conn, name=name, code=code, phase=phase, owner=project_owner
    )
    _emit(
        {
            "ok": True,
            "count": len(rows),
            "projects": [r.model_dump(mode="json") for r in rows],
        }
    )


@project.command("upsert", help="Insert or update the single project row.")
@click.option("--name", required=True)
@click.option("--code", default=None)
@click.option(
    "--phase",
    type=click.Choice([p.value for p in ProjectPhase]),
    default=ProjectPhase.DISCOVERY.value,
)
@click.option("--objective", default="")
@click.option("--business-case", "business_case", default="")
@click.option("--project-owner", "project_owner", default=None)
@click.option("--sponsor", default=None)
@click.option("--status-summary", "status_summary", default="")
@click.pass_context
def project_upsert(
    ctx: click.Context,
    name: str,
    code: Optional[str],
    phase: str,
    objective: str,
    business_case: str,
    project_owner: Optional[str],
    sponsor: Optional[str],
    status_summary: str,
) -> None:
    """Insert or update the single project metadata row.

    Args:
        ctx: Click context.
        name: Human-readable project name.
        code: Optional short project code (e.g. "PROJ-24").
        phase: Project lifecycle phase value.
        objective: One-sentence project objective.
        business_case: Business justification text.
        project_owner: Name of the project owner.
        sponsor: Name of the executive sponsor.
        status_summary: Current status narrative.
    """
    conn = _open_conn()
    existing = projects_db.get_project(conn)
    if existing:
        existing.name = name
        existing.code = code
        existing.phase = ProjectPhase(phase)
        existing.objective = objective
        existing.business_case = business_case
        existing.project_owner = project_owner
        existing.sponsor = sponsor
        existing.status_summary = status_summary
        meta = existing
    else:
        meta = ProjectMeta(
            name=name,
            code=code,
            phase=ProjectPhase(phase),
            objective=objective,
            business_case=business_case,
            project_owner=project_owner,
            sponsor=sponsor,
            status_summary=status_summary,
        )
    projects_db.upsert_project(conn, meta)
    _emit({"ok": True, "project_id": meta.project_id})


# ───────────────────── requirements subgroup ─────────────────────


@cli.group(help="Requirement CRUD and search commands.")
def req() -> None:
    """Requirement CRUD and search subcommands."""


@req.command("add", help="Insert a new requirement.")
@click.option("--title", required=True)
@click.option("--by", "created_by", required=True)
@click.option(
    "--type",
    "req_type",
    type=click.Choice([t.value for t in RequirementType]),
    default=RequirementType.FUN.value,
)
@click.option("--description", default="")
@click.option(
    "--priority",
    type=click.Choice([p.value for p in RequirementPriority]),
    default=RequirementPriority.MEDIUM.value,
)
@click.option("--owner", default=None)
@click.option("--tags", default="", help="Comma-separated tag list.")
@click.pass_context
def req_add(
    ctx: click.Context,
    title: str,
    created_by: str,
    req_type: str,
    description: str,
    priority: str,
    owner: Optional[str],
    tags: str,
) -> None:
    """Insert a new requirement row.

    Args:
        ctx: Click context.
        title: Short requirement title.
        created_by: Identifier of the person creating the requirement.
        req_type: Three-letter requirement type code (e.g. "FUN").
        description: Full requirement description text.
        priority: Priority level (low/medium/high/critical).
        owner: Optional owner identifier.
        tags: Comma-separated tag string.
    """
    conn = _open_conn()
    req_in = RequirementIn(
        req_type=RequirementType(req_type),
        title=title,
        description=description,
        priority=RequirementPriority(priority),
        owner=owner,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
    )
    row = req_db.insert_requirement(conn, req_in, created_by=created_by)
    _emit({"ok": True, "requirement": row.model_dump(mode="json")})


@req.command("update", help="Apply a partial update to a requirement.")
@click.option("--id", "req_id", required=True)
@click.option("--by", "changed_by", required=True)
@click.option("--summary", required=True)
@click.option("--title", default=None)
@click.option("--description", default=None)
@click.option(
    "--status", type=click.Choice([s.value for s in RequirementStatus]), default=None
)
@click.option(
    "--priority",
    type=click.Choice([p.value for p in RequirementPriority]),
    default=None,
)
@click.option("--owner", default=None)
@click.option("--tags", default=None, help="Comma-separated tag list (replaces).")
@click.pass_context
def req_update(
    ctx: click.Context,
    req_id: str,
    changed_by: str,
    summary: str,
    title: Optional[str],
    description: Optional[str],
    status: Optional[str],
    priority: Optional[str],
    owner: Optional[str],
    tags: Optional[str],
) -> None:
    """Apply a partial field update to an existing requirement.

    Args:
        ctx: Click context.
        req_id: Requirement identifier to update.
        changed_by: Identifier of the person making the change.
        summary: One-line summary of what changed and why.
        title: New title, if updating.
        description: New description, if updating.
        status: New status value, if updating.
        priority: New priority value, if updating.
        owner: New owner, if updating.
        tags: Comma-separated replacement tag list, if updating.
    """
    changes: dict[str, Any] = {}
    if title is not None:
        changes["title"] = title
    if description is not None:
        changes["description"] = description
    if status is not None:
        changes["status"] = status
    if priority is not None:
        changes["priority"] = priority
    if owner is not None:
        changes["owner"] = owner
    if tags is not None:
        changes["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    if not changes:
        _fail("No fields to update.")
    conn = _open_conn()
    try:
        row = req_db.update_requirement(conn, req_id, changes, changed_by, summary)
    except (KeyError, ValueError) as e:
        _fail(str(e))
    _emit({"ok": True, "requirement": row.model_dump(mode="json")})


@req.command("show", help="Show a single requirement.")
@click.argument("req_id")
@click.pass_context
def req_show(ctx: click.Context, req_id: str) -> None:
    """Display a single requirement as JSON.

    Args:
        ctx: Click context.
        req_id: Requirement identifier to fetch.
    """
    conn = _open_conn()
    row = req_db.get_requirement(conn, req_id)
    if not row:
        _fail(f"Requirement '{req_id}' not found.")
    _emit({"ok": True, "requirement": row.model_dump(mode="json")})


@req.command("search", help="Comprehensive search and list.")
@click.option(
    "--status", type=click.Choice([s.value for s in RequirementStatus]), default=None
)
@click.option(
    "--priority",
    type=click.Choice([p.value for p in RequirementPriority]),
    default=None,
)
@click.option(
    "--type",
    "req_type",
    type=click.Choice([t.value for t in RequirementType]),
    default=None,
)
@click.option("--owner", default=None)
@click.option("--tag", default=None)
@click.option("--keyword", default=None)
@click.option("--fts", "fts_query", help="Full-text search query (FTS5).")
@click.option("--since", help="Created at/after (ISO).")
@click.option("--until", help="Created before/at (ISO).")
@click.option("--updated-since", help="Updated at/after (ISO).")
@click.option("--updated-until", help="Updated before/at (ISO).")
@click.option(
    "--sort-by",
    type=click.Choice(["created_at", "updated_at", "status", "priority", "title"]),
    default="updated_at",
)
@click.option("--asc", is_flag=True, default=False, help="Sort ascending.")
@click.pass_context
def req_search(
    ctx: click.Context,
    status: Optional[str],
    priority: Optional[str],
    req_type: Optional[str],
    owner: Optional[str],
    tag: Optional[str],
    keyword: Optional[str],
    fts_query: Optional[str],
    since: Optional[str],
    until: Optional[str],
    updated_since: Optional[str],
    updated_until: Optional[str],
    sort_by: str,
    asc: bool,
) -> None:
    """Search requirements using comprehensive filters."""
    from datetime import datetime

    conn = _open_conn()

    if fts_query:
        rows = req_db.fts_search_requirements(conn, fts_query)
        # Apply other filters in-memory if provided (simple version)
        if status:
            rows = [r for r in rows if r.status.value == status]
        if priority:
            rows = [r for r in rows if r.priority.value == priority]
        if req_type:
            rows = [r for r in rows if r.req_type.value == req_type]
        if owner:
            rows = [r for r in rows if r.owner == owner]
        if tag:
            rows = [r for r in rows if tag in r.tags]

        # Sort
        rev = not asc
        if sort_by == "created_at":
            rows.sort(key=lambda r: r.created_at, reverse=rev)
        elif sort_by == "updated_at":
            rows.sort(key=lambda r: r.updated_at, reverse=rev)
        elif sort_by == "title":
            rows.sort(key=lambda r: r.title, reverse=rev)
    else:
        rows = req_db.search_requirements(
            conn,
            status=status,
            priority=priority,
            req_type=req_type,
            owner=owner,
            tag=tag,
            keyword=keyword,
            since=datetime.fromisoformat(since) if since else None,
            until=datetime.fromisoformat(until) if until else None,
            updated_since=datetime.fromisoformat(updated_since)
            if updated_since
            else None,
            updated_until=datetime.fromisoformat(updated_until)
            if updated_until
            else None,
            sort_by=sort_by,
            desc=not asc,
        )

    _emit(
        {
            "ok": True,
            "count": len(rows),
            "requirements": [r.model_dump(mode="json") for r in rows],
        }
    )


@req.command("vec-search", help="Embedding-based similarity search.")
@click.argument("query")
@click.option("--top-k", "top_k", type=int, default=10)
@click.pass_context
def req_vec_search(ctx: click.Context, query: str, top_k: int) -> None:
    """Run an embedding-based similarity search over requirements.

    Args:
        ctx: Click context.
        query: Natural-language query string.
        top_k: Number of nearest neighbours to return.
    """
    conn = _open_conn()
    try:
        results = vector_search(conn, query, top_k=top_k)
    except RuntimeError as e:
        _fail(str(e))
    _emit(
        {
            "ok": True,
            "query": query,
            "results": [
                {**r.model_dump(mode="json"), "distance": round(dist, 4)}
                for r, dist in results
            ],
        }
    )


# ───────────────────── issues subgroup ─────────────────────


@cli.group(help="Issue CRUD and search commands.")
def issue() -> None:
    """Issue CRUD and search subcommands."""


@issue.command("add", help="Insert a new issue.")
@click.option("--title", required=True)
@click.option("--by", "created_by", required=True)
@click.option("--description", default="")
@click.option(
    "--status",
    type=click.Choice([s.value for s in IssueStatus]),
    default=IssueStatus.OPEN.value,
)
@click.option(
    "--priority",
    type=click.Choice([p.value for p in IssuePriority]),
    default=IssuePriority.MEDIUM.value,
)
@click.option("--owner", default=None)
@click.option(
    "--req-ids", "requirement_ids", default="", help="Comma-separated req IDs."
)
@click.option("--upd-ids", "update_ids", default="", help="Comma-separated update IDs.")
@click.pass_context
def issue_add(
    ctx: click.Context,
    title: str,
    created_by: str,
    description: str,
    status: str,
    priority: str,
    owner: Optional[str],
    requirement_ids: str,
    update_ids: str,
) -> None:
    """Insert a new issue row."""
    from ..models import IssueIn

    conn = _open_conn()
    issue_in = IssueIn(
        title=title,
        description=description,
        status=IssueStatus(status),
        priority=IssuePriority(priority),
        owner=owner,
        requirement_ids=[i.strip() for i in requirement_ids.split(",") if i.strip()],
        update_ids=[i.strip() for i in update_ids.split(",") if i.strip()],
    )
    row = issues_db.insert_issue(conn, issue_in, created_by=created_by)
    _emit({"ok": True, "issue": row.model_dump(mode="json")})


@issue.command("show", help="Show a single issue (full data).")
@click.argument("issue_id")
@click.pass_context
def issue_show(ctx: click.Context, issue_id: str) -> None:
    """Display a single issue with all linked updates and actions."""
    conn = _open_conn()
    data = issues_db.get_issue_full(conn, issue_id)
    if not data:
        _fail(f"Issue '{issue_id}' not found.")
    _emit({"ok": True, "issue": data})


@issue.command("search", help="Comprehensive search and list.")
@click.option(
    "--status", type=click.Choice([s.value for s in IssueStatus]), default=None
)
@click.option(
    "--priority",
    type=click.Choice([p.value for p in IssuePriority]),
    default=None,
)
@click.option("--owner", default=None)
@click.option("--req-id", "requirement_id", default=None)
@click.option("--fts", "fts_query", help="Full-text search query (FTS5).")
@click.option("--since", help="Created at/after (ISO).")
@click.option("--until", help="Created before/at (ISO).")
@click.option("--updated-since", help="Updated at/after (ISO).")
@click.option("--updated-until", help="Updated before/at (ISO).")
@click.option(
    "--sort-by",
    type=click.Choice(["created_at", "updated_at", "status", "priority", "title"]),
    default="updated_at",
)
@click.option("--asc", is_flag=True, default=False, help="Sort ascending.")
@click.pass_context
def issue_search(
    ctx: click.Context,
    status: Optional[str],
    priority: Optional[str],
    owner: Optional[str],
    requirement_id: Optional[str],
    fts_query: Optional[str],
    since: Optional[str],
    until: Optional[str],
    updated_since: Optional[str],
    updated_until: Optional[str],
    sort_by: str,
    asc: bool,
) -> None:
    """Search issues using comprehensive filters."""
    from datetime import datetime

    conn = _open_conn()

    if fts_query:
        rows = issues_db.fts_search_issues(conn, fts_query)
        # Apply other filters in-memory if provided
        if status:
            rows = [r for r in rows if r.status.value == status]
        if priority:
            rows = [r for r in rows if r.priority.value == priority]
        if owner:
            rows = [r for r in rows if r.owner == owner]
        if requirement_id:
            rows = [r for r in rows if requirement_id in r.requirement_ids]

        # Sort
        rev = not asc
        if sort_by == "created_at":
            rows.sort(key=lambda r: r.created_at, reverse=rev)
        elif sort_by == "updated_at":
            rows.sort(key=lambda r: r.updated_at, reverse=rev)
        elif sort_by == "title":
            rows.sort(key=lambda r: r.title, reverse=rev)
    else:
        rows = issues_db.search_issues(
            conn,
            status=status,
            priority=priority,
            owner=owner,
            requirement_id=requirement_id,
            since=datetime.fromisoformat(since) if since else None,
            until=datetime.fromisoformat(until) if until else None,
            updated_since=datetime.fromisoformat(updated_since)
            if updated_since
            else None,
            updated_until=datetime.fromisoformat(updated_until)
            if updated_until
            else None,
            sort_by=sort_by,
            desc=not asc,
        )

    _emit(
        {
            "ok": True,
            "count": len(rows),
            "issues": [r.model_dump(mode="json") for r in rows if r],
        }
    )


@issue.command("log-action", help="Record an action taken for an issue.")
@click.option("--id", "issue_id", required=True)
@click.option("--description", required=True)
@click.pass_context
def issue_log_action(ctx: click.Context, issue_id: str, description: str) -> None:
    """Record an action taken for an issue."""
    from ..models import IssueActionIn

    conn = _open_conn()
    action_in = IssueActionIn(issue_id=issue_id, description=description)
    row = issues_db.log_issue_action(conn, action_in)
    _emit({"ok": True, "action": row.model_dump(mode="json")})


@issue.command("search-actions", help="Comprehensive search for actions.")
@click.option("--issue-id", help="Filter by issue.")
@click.option("--since")
@click.option("--until")
@click.option("--keyword")
@click.option("--asc", is_flag=True, default=False)
@click.pass_context
def issue_search_actions(
    ctx: click.Context,
    issue_id: Optional[str],
    since: Optional[str],
    until: Optional[str],
    keyword: Optional[str],
    asc: bool,
) -> None:
    """Search issue actions with date and keyword filters."""
    from datetime import datetime

    conn = _open_conn()
    rows = issues_db.search_issue_actions(
        conn,
        issue_id=issue_id,
        since=datetime.fromisoformat(since) if since else None,
        until=datetime.fromisoformat(until) if until else None,
        keyword=keyword,
        desc=not asc,
    )
    _emit(
        {
            "ok": True,
            "count": len(rows),
            "actions": [r.model_dump(mode="json") for r in rows],
        }
    )


# ───────────────────── update history subgroup ─────────────────────


@cli.group(help="Requirement change-log commands.")
def update() -> None:
    """Requirement change-log subcommands."""


@update.command("show", help="Show full change history for a requirement.")
@click.argument("req_id")
@click.pass_context
def update_show(ctx: click.Context, req_id: str) -> None:
    """Display the full change history for a requirement.

    Args:
        ctx: Click context.
        req_id: Requirement identifier whose history to fetch.
    """
    conn = _open_conn()
    history = updates_db.get_updates(conn, req_id)
    _emit(
        {
            "ok": True,
            "requirement_id": req_id,
            "count": len(history),
            "history": [u.model_dump(mode="json") for u in history],
        }
    )


@update.command("search", help="Search the global audit log.")
@click.option(
    "--type", "entity_type", type=click.Choice(["requirement", "project", "issue"])
)
@click.option("--id", "entity_id")
@click.option("--by", "changed_by")
@click.option("--since")
@click.option("--until")
@click.option(
    "--sort-by", type=click.Choice(["changed_at", "changed_by"]), default="changed_at"
)
@click.option("--asc", is_flag=True, default=False)
@click.pass_context
def update_search(
    ctx: click.Context,
    entity_type: Optional[str],
    entity_id: Optional[str],
    changed_by: Optional[str],
    since: Optional[str],
    until: Optional[str],
    sort_by: str,
    asc: bool,
) -> None:
    """Search audit records by any parameter."""
    from datetime import datetime

    conn = _open_conn()
    rows = updates_db.search_updates(
        conn,
        entity_type=entity_type,
        entity_id=entity_id,
        changed_by=changed_by,
        since=datetime.fromisoformat(since) if since else None,
        until=datetime.fromisoformat(until) if until else None,
        sort_by=sort_by,
        desc=not asc,
    )
    _emit(
        {
            "ok": True,
            "count": len(rows),
            "updates": [r.model_dump(mode="json") for r in rows],
        }
    )


if __name__ == "__main__":
    cli()
