"""Click CLI exposing full CRUD over a project database.

Each subcommand opens the SQLite file at ``projects/<slug>/<slug>.db``,
runs one operation, and prints the result as JSON to stdout. Errors are
logged via loguru and surfaced as a non-zero exit code.

Examples:
    db --project demo project show
    db --project demo req add --title "..." --by alice
    db --project demo req search --status open --priority high
    db --project demo req vec-search "fault tolerance" --top-k 5
    db --project demo minute list --unintegrated
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any, Optional

import click
from loguru import logger

from .. import CONSTANTS as C
from ..models import (
    DecisionStatus,
    MeetingSource,
    MinuteIn,
    ProjectMeta,
    ProjectPhase,
    RequirementIn,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from . import minutes as minutes_db
from . import projects as projects_db
from . import requirements as req_db
from . import updates as updates_db
from .connection import get_db
from .embeddings import vector_search


# ───────────────────── helpers ─────────────────────


def _emit(payload: dict) -> None:
    """Print ``payload`` as pretty JSON and flush stdout."""
    click.echo(json.dumps(payload, indent=2, default=str))


def _fail(msg: str, exit_code: int = 1) -> None:
    """Log an error and exit with the given code."""
    logger.error(msg)
    click.echo(json.dumps({"ok": False, "error": msg}, default=str), err=True)
    sys.exit(exit_code)


def _open_conn(slug: str) -> sqlite3.Connection:
    """Open the DB for a given project slug."""
    return get_db(str(C.db_path(slug)))


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


@click.group(help=__doc__.split("\n", 1)[0])
@click.option(
    "--project",
    "slug",
    required=True,
    metavar="SLUG",
    help="Project slug (directory name under projects/).",
)
@click.pass_context
def cli(ctx: click.Context, slug: str) -> None:
    """Top-level entry point. Stores ``slug`` on the context."""
    ctx.ensure_object(dict)
    ctx.obj["slug"] = slug


# ───────────────────── project subgroup ─────────────────────


@cli.group(help="Project metadata commands.")
def project() -> None: ...


@project.command("show", help="Show the project metadata as JSON.")
@click.pass_context
def project_show(ctx: click.Context) -> None:
    conn = _open_conn(ctx.obj["slug"])
    meta = projects_db.get_project(conn)
    if not meta:
        _fail(f"No project in DB at slug '{ctx.obj['slug']}'.")
    _emit({"ok": True, "project": meta.model_dump(mode="json")})


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
    conn = _open_conn(ctx.obj["slug"])
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
            slug=ctx.obj["slug"],
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
    _emit({"ok": True, "project_id": meta.project_id, "slug": meta.slug})


# ───────────────────── requirements subgroup ─────────────────────


@cli.group(help="Requirement CRUD and search commands.")
def req() -> None: ...


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
    conn = _open_conn(ctx.obj["slug"])
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
    conn = _open_conn(ctx.obj["slug"])
    try:
        row = req_db.update_requirement(conn, req_id, changes, changed_by, summary)
    except (KeyError, ValueError) as e:
        _fail(str(e))
    _emit({"ok": True, "requirement": row.model_dump(mode="json")})


@req.command("show", help="Show a single requirement.")
@click.argument("req_id")
@click.pass_context
def req_show(ctx: click.Context, req_id: str) -> None:
    conn = _open_conn(ctx.obj["slug"])
    row = req_db.get_requirement(conn, req_id)
    if not row:
        _fail(f"Requirement '{req_id}' not found.")
    _emit({"ok": True, "requirement": row.model_dump(mode="json")})


@req.command("search", help="Field-based search.")
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
@click.pass_context
def req_search(
    ctx: click.Context,
    status: Optional[str],
    priority: Optional[str],
    req_type: Optional[str],
    owner: Optional[str],
    tag: Optional[str],
    keyword: Optional[str],
) -> None:
    conn = _open_conn(ctx.obj["slug"])
    rows = req_db.search_requirements(
        conn,
        status=status,
        priority=priority,
        req_type=req_type,
        owner=owner,
        tag=tag,
        keyword=keyword,
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
    conn = _open_conn(ctx.obj["slug"])
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


# ───────────────────── minutes subgroup ─────────────────────


@cli.group(help="Meeting minute commands.")
def minute() -> None: ...


@minute.command("add", help="Log a meeting.")
@click.option("--title", required=True)
@click.option("--by", "logged_by", required=True)
@click.option(
    "--source",
    type=click.Choice([s.value for s in MeetingSource]),
    default=MeetingSource.OTHER.value,
)
@click.option("--source-url", "source_url", default=None)
@click.option(
    "--occurred-at", "occurred_at", default=None, help="ISO datetime; defaults to now."
)
@click.option("--summary", default="")
@click.option("--raw-notes", "raw_notes", default="")
@click.option("--attendees", default=None, help="JSON array of attendee names.")
@click.option("--decisions", default=None, help="JSON array of Decision dicts.")
@click.option(
    "--action-items",
    "action_items",
    default=None,
    help="JSON array of ActionItem dicts.",
)
@click.pass_context
def minute_add(
    ctx: click.Context,
    title: str,
    logged_by: str,
    source: str,
    source_url: Optional[str],
    occurred_at: Optional[str],
    summary: str,
    raw_notes: str,
    attendees: Optional[str],
    decisions: Optional[str],
    action_items: Optional[str],
) -> None:
    from ..models import ActionItem, Decision

    conn = _open_conn(ctx.obj["slug"])
    occurred = (
        datetime.fromisoformat(occurred_at)
        if occurred_at
        else datetime.now(timezone.utc)
    )
    minute_in = MinuteIn(
        title=title,
        source=MeetingSource(source),
        source_url=source_url,
        occurred_at=occurred,
        logged_by=logged_by,
        attendees=_parse_json_list(attendees, "attendees"),
        summary=summary,
        raw_notes=raw_notes,
        decisions=[Decision(**d) for d in _parse_json_list(decisions, "decisions")],
        action_items=[
            ActionItem(**a) for a in _parse_json_list(action_items, "action-items")
        ],
    )
    row = minutes_db.insert_minute(conn, minute_in)
    _emit({"ok": True, "meeting": row.model_dump(mode="json")})


@minute.command("show", help="Show one meeting by id.")
@click.argument("minute_id")
@click.pass_context
def minute_show(ctx: click.Context, minute_id: str) -> None:
    conn = _open_conn(ctx.obj["slug"])
    row = minutes_db.get_minute(conn, minute_id)
    if not row:
        _fail(f"Meeting '{minute_id}' not found.")
    _emit({"ok": True, "meeting": row.model_dump(mode="json")})


@minute.command("list", help="List meetings with optional filters.")
@click.option(
    "--source", type=click.Choice([s.value for s in MeetingSource]), default=None
)
@click.option("--unintegrated", is_flag=True, default=False)
@click.option("--since", default=None, help="ISO datetime lower bound.")
@click.pass_context
def minute_list(
    ctx: click.Context,
    source: Optional[str],
    unintegrated: bool,
    since: Optional[str],
) -> None:
    conn = _open_conn(ctx.obj["slug"])
    rows = minutes_db.list_minutes(
        conn, source=source, unintegrated=unintegrated, since=since
    )
    _emit(
        {
            "ok": True,
            "count": len(rows),
            "meetings": [m.model_dump(mode="json") for m in rows],
        }
    )


@minute.command("integrate", help="Mark a meeting as integrated.")
@click.argument("minute_id")
@click.pass_context
def minute_integrate(ctx: click.Context, minute_id: str) -> None:
    conn = _open_conn(ctx.obj["slug"])
    if not minutes_db.get_minute(conn, minute_id):
        _fail(f"Meeting '{minute_id}' not found.")
    row = minutes_db.mark_integrated(conn, minute_id)
    _emit({"ok": True, "meeting_id": row.id, "integrated_at": row.integrated_at})


@minute.command("decisions", help="List decisions across all meetings.")
@click.option(
    "--status", type=click.Choice([s.value for s in DecisionStatus]), default=None
)
@click.option("--affects-req", "affects_req", default=None)
@click.pass_context
def minute_decisions(
    ctx: click.Context, status: Optional[str], affects_req: Optional[str]
) -> None:
    conn = _open_conn(ctx.obj["slug"])
    decs = minutes_db.list_decisions(conn, status=status, affects_req=affects_req)
    _emit({"ok": True, "count": len(decs), "decisions": decs})


# ───────────────────── update history subgroup ─────────────────────


@cli.group(help="Requirement change-log commands.")
def update() -> None: ...


@update.command("show", help="Show full change history for a requirement.")
@click.argument("req_id")
@click.pass_context
def update_show(ctx: click.Context, req_id: str) -> None:
    conn = _open_conn(ctx.obj["slug"])
    history = updates_db.get_updates(conn, req_id)
    _emit(
        {
            "ok": True,
            "requirement_id": req_id,
            "count": len(history),
            "history": [u.model_dump(mode="json") for u in history],
        }
    )


if __name__ == "__main__":
    cli()
