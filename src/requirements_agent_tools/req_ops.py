"""
req_ops.py — requirement CRUD, search, history.

Commands: add · update · get · list · search · history · vector
"""

import argparse

from . import CONSTANTS as C
from . import project_session as ps
from ._cli_io import err as _err
from ._cli_io import ok as _ok
from ._cli_io import parse_json_arg as _pj
from .db.embeddings import vector_search
from .db.requirements import (
    get_requirement,
    insert_requirement,
    search_requirements,
    update_requirement,
)
from .db.updates import get_updates
from .models import (
    Dependency,
    ExternalLink,
    RequirementIn,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
    Stakeholder,
)


def cmd_add(args):
    """Add a new requirement to the active project.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    slug, conn, meta = ps.resolve(args.project)
    req_in = RequirementIn(
        req_type=RequirementType(args.type.upper())
        if args.type
        else RequirementType.FUN,
        title=args.title,
        description=args.description or "",
        priority=RequirementPriority(args.priority)
        if args.priority
        else RequirementPriority.MEDIUM,
        owner=args.owner,
        tags=args.tags.split(",") if args.tags else [],
        stakeholders=[Stakeholder(**s) for s in _pj(args.stakeholders, "stakeholders")],
        predecessors=[Dependency(**d) for d in _pj(args.predecessors, "predecessors")],
        dependencies=[Dependency(**d) for d in _pj(args.dependencies, "dependencies")],
        external_links=[
            ExternalLink(**link) for link in _pj(args.external_links, "external-links")
        ],
    )
    row = insert_requirement(conn, req_in, created_by=args.by)
    _ok(
        {
            "id": row.id,
            "req_type": row.req_type.value,
            "title": row.title,
            "status": row.status.value,
            "priority": row.priority.value,
            "has_embedding": row.has_embedding,
        }
    )


def cmd_update(args):
    """Apply a partial field update to an existing requirement.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    slug, conn, meta = ps.resolve(args.project)
    changes = {}
    if args.title:
        changes["title"] = args.title
    if args.description is not None:
        changes["description"] = args.description
    if args.status:
        changes["status"] = args.status
    if args.priority:
        changes["priority"] = args.priority
    if args.owner is not None:
        changes["owner"] = args.owner
    if args.tags is not None:
        changes["tags"] = args.tags.split(",") if args.tags else []
    if args.stakeholders is not None:
        changes["stakeholders"] = [
            s.model_dump()
            for s in [Stakeholder(**s) for s in _pj(args.stakeholders, "stakeholders")]
        ]
    if args.predecessors is not None:
        changes["predecessors"] = [
            d.model_dump()
            for d in [Dependency(**d) for d in _pj(args.predecessors, "predecessors")]
        ]
    if args.dependencies is not None:
        changes["dependencies"] = [
            d.model_dump()
            for d in [Dependency(**d) for d in _pj(args.dependencies, "dependencies")]
        ]
    if args.external_links is not None:
        changes["external_links"] = [
            link.model_dump()
            for link in [
                ExternalLink(**link)
                for link in _pj(args.external_links, "external-links")
            ]
        ]
    if not changes:
        _err("No fields to update provided.")
    try:
        row = update_requirement(conn, args.id, changes, args.by, args.summary)
    except (KeyError, ValueError) as e:
        _err(str(e))
    _ok(
        {
            "id": row.id,
            "updated_fields": list(changes.keys()),
            "status": row.status.value,
            "updated_at": row.updated_at.isoformat(),
        }
    )


def cmd_get(args):
    """Fetch and display a single requirement by ID.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    _, conn, _ = ps.resolve(args.project)
    row = get_requirement(conn, args.id)
    if not row:
        _err(f"Requirement '{args.id}' not found.")
    _ok({"requirement": row.model_dump(mode="json")})


def cmd_list(args):
    """List all requirements with optional field filters.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    _, conn, _ = ps.resolve(args.project)
    rows = search_requirements(
        conn,
        status=args.status,
        priority=args.priority,
        req_type=args.type,
        owner=args.owner,
        tag=args.tag,
        keyword=args.keyword,
    )
    _ok(
        {
            "count": len(rows),
            "requirements": [
                {
                    "id": r.id,
                    "req_type": r.req_type.value,
                    "title": r.title,
                    "status": r.status.value,
                    "priority": r.priority.value,
                    "owner": r.owner,
                    "tags": r.tags,
                    "has_fret": False,
                    "has_embedding": r.has_embedding,
                    "updated_at": r.updated_at.isoformat(),
                }
                for r in rows
            ],
        }
    )


def cmd_search(args):
    """Keyword search across requirement titles and descriptions.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    _, conn, _ = ps.resolve(args.project)
    rows = search_requirements(conn, keyword=args.query)
    _ok(
        {
            "query": args.query,
            "count": len(rows),
            "requirements": [
                {
                    "id": r.id,
                    "req_type": r.req_type.value,
                    "title": r.title,
                    "status": r.status.value,
                }
                for r in rows
            ],
        }
    )


def cmd_history(args):
    """Display the full change history for a requirement.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    _, conn, _ = ps.resolve(args.project)
    updates = get_updates(conn, args.id)
    _ok(
        {
            "requirement_id": args.id,
            "change_count": len(updates),
            "history": [
                {
                    "changed_at": u.changed_at.isoformat(),
                    "changed_by": u.changed_by,
                    "summary": u.summary,
                    "diffs": [d.model_dump() for d in u.diffs],
                    "full_snapshot": "present" if u.full_snapshot else None,
                }
                for u in updates
            ],
        }
    )


def cmd_vector(args):
    """Embedding-based similarity search over requirements.

    Requires EMBEDDING_API_KEY environment variable to be set.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    if not C.EMBEDDING_API_KEY:
        _err("EMBEDDING_API_KEY not set. Vector search unavailable.")
    _, conn, _ = ps.resolve(args.project)
    results = vector_search(conn, args.query, top_k=args.top_k)
    _ok(
        {
            "query": args.query,
            "results": [
                {
                    "id": r.id,
                    "req_type": r.req_type.value,
                    "title": r.title,
                    "status": r.status.value,
                    "priority": r.priority.value,
                    "distance": round(dist, 4),
                }
                for r, dist in results
            ],
        }
    )


def build_parser():
    """Build and return the req-ops argument parser.

    Returns:
        Configured ArgumentParser with add, update, get, list, search,
        history, and vector subcommands.
    """
    p = argparse.ArgumentParser(description="Requirement operations")
    p.add_argument("--project", default=None, help="Project slug or partial name")
    sub = p.add_subparsers(dest="command", required=True)

    TYPES = [t.value for t in RequirementType]
    STATS = [s.value for s in RequirementStatus]
    PRIOS = [p.value for p in RequirementPriority]

    add = sub.add_parser("add")
    add.add_argument("--title", required=True)
    add.add_argument("--by", required=True)
    add.add_argument("--type", choices=TYPES, default="FUN")
    add.add_argument("--description", default="")
    add.add_argument("--priority", choices=PRIOS, default="medium")
    add.add_argument("--owner")
    add.add_argument("--tags")
    add.add_argument("--stakeholders", default=None)
    add.add_argument("--predecessors", default=None)
    add.add_argument("--dependencies", default=None)
    add.add_argument("--external-links", dest="external_links", default=None)

    upd = sub.add_parser("update")
    upd.add_argument("--id", required=True)
    upd.add_argument("--by", required=True)
    upd.add_argument("--summary", required=True)
    upd.add_argument("--title")
    upd.add_argument("--description")
    upd.add_argument("--status", choices=STATS)
    upd.add_argument("--priority", choices=PRIOS)
    upd.add_argument("--owner")
    upd.add_argument("--tags")
    upd.add_argument("--stakeholders", default=None)
    upd.add_argument("--predecessors", default=None)
    upd.add_argument("--dependencies", default=None)
    upd.add_argument("--external-links", dest="external_links", default=None)

    gt = sub.add_parser("get")
    gt.add_argument("--id", required=True)

    ls = sub.add_parser("list")
    ls.add_argument("--status", choices=STATS)
    ls.add_argument("--priority", choices=PRIOS)
    ls.add_argument("--type", choices=TYPES)
    ls.add_argument("--owner")
    ls.add_argument("--tag")
    ls.add_argument("--keyword")

    sr = sub.add_parser("search")
    sr.add_argument("--query", required=True)

    hs = sub.add_parser("history")
    hs.add_argument("--id", required=True)

    vs = sub.add_parser("vector")
    vs.add_argument("--query", required=True)
    vs.add_argument("--top-k", dest="top_k", type=int, default=10)

    return p


def main():
    """Entry point for the req-ops CLI."""
    args = build_parser().parse_args()
    {
        "add": cmd_add,
        "update": cmd_update,
        "get": cmd_get,
        "list": cmd_list,
        "search": cmd_search,
        "history": cmd_history,
        "vector": cmd_vector,
    }[args.command](args)


if __name__ == "__main__":
    main()
