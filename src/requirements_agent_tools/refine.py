"""
refine.py — interactive FRET requirement refinement.

Commands
────────
  pending   List requirements without a FRET statement
  show      Show a requirement with its current FRET status
  apply     Write FRET statement + fields to a requirement (after user confirms)
  coverage  Show FRET coverage stats across all requirements
"""

import argparse

from . import project_session as ps
from ._cli_io import err as _err
from ._cli_io import ok as _ok
from .db.requirements import get_requirement, search_requirements, update_requirement


def cmd_pending(args):
    """List requirements that still need a FRET statement."""
    _, conn, _ = ps.resolve(args.project)
    reqs = search_requirements(conn)
    _ok(
        {
            "count": len(reqs),
            "message": f"{len(reqs)} requirement(s) need FRET refinement.",
            "requirements": [
                {
                    "id": r.id,
                    "req_type": r.req_type.value,
                    "title": r.title,
                    "status": r.status.value,
                    "priority": r.priority.value,
                    "description_preview": r.description[:120]
                    + ("…" if len(r.description) > 120 else ""),
                }
                for r in reqs
            ],
        }
    )


def cmd_show(args):
    """Show a requirement with full FRET status for refinement session."""
    _, conn, _ = ps.resolve(args.project)
    req = get_requirement(conn, args.id)
    if not req:
        _err(f"Requirement '{args.id}' not found.")
    _ok(
        {
            "id": req.id,
            "req_type": req.req_type.value,
            "title": req.title,
            "description": req.description,
            "status": req.status.value,
            "priority": req.priority.value,
            "has_fret": False,  # fret fields deferred to Phase 3
        }
    )


def cmd_apply(args):
    """
    Write a refined description to a requirement.
    FRET grammar fields (scope/condition/timing/response) are deferred to Phase 3.
    For now, only description can be updated via this command.
    """
    _, conn, _ = ps.resolve(args.project)

    changes = {}
    # Optionally update description with a refined version
    if args.description:
        changes["description"] = args.description

    if not changes:
        _err("No updatable fields provided. (FRET grammar fields deferred to Phase 3.)")

    try:
        row = update_requirement(
            conn,
            args.id,
            changes,
            changed_by=args.by,
            summary=args.summary or "FRET statement applied.",
        )
    except (KeyError, ValueError) as e:
        _err(str(e))

    _ok(
        {
            "id": row.id,
            "updated_at": row.updated_at.isoformat(),
            "note": "FRET grammar fields will be added in Phase 3",
        }
    )


def cmd_coverage(args):
    """Show FRET coverage across all requirements."""
    _, conn, _ = ps.resolve(args.project)
    all_reqs = search_requirements(conn)
    total = len(all_reqs)

    _ok(
        {
            "total": total,
            "with_fret": 0,
            "without_fret": total,
            "coverage_pct": 0.0,
            "note": "FRET grammar fields deferred to Phase 3",
            "pending_ids": [r.id for r in all_reqs],
        }
    )


def build_parser():
    p = argparse.ArgumentParser(description="FRET requirement refinement")
    p.add_argument("--project", default=None)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("pending")

    sh = sub.add_parser("show")
    sh.add_argument("--id", required=True)

    ap = sub.add_parser("apply")
    ap.add_argument("--id", required=True)
    ap.add_argument("--by", required=True)
    ap.add_argument(
        "--description",
        default=None,
        help="Optionally update the plain-language description",
    )
    ap.add_argument("--summary", default="FRET statement applied.")

    sub.add_parser("coverage")

    return p


def main():
    args = build_parser().parse_args()
    {
        "pending": cmd_pending,
        "show": cmd_show,
        "apply": cmd_apply,
        "coverage": cmd_coverage,
    }[args.command](args)


if __name__ == "__main__":
    main()
