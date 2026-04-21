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
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "shared"))

import db
import project_session as ps


def _ok(data):  print(json.dumps({"ok": True,  **data}, indent=2, default=str))
def _err(msg):  print(json.dumps({"ok": False, "error": msg}), file=sys.stderr); sys.exit(1)


def cmd_pending(args):
    """List requirements that still need a FRET statement."""
    _, conn, _ = ps.resolve(args.project)
    reqs = db.search_requirements(conn, has_fret=False)
    _ok({
        "count": len(reqs),
        "message": f"{len(reqs)} requirement(s) need FRET refinement.",
        "requirements": [
            {"id": r.id, "req_type": r.req_type.value,
             "title": r.title, "status": r.status.value,
             "priority": r.priority.value,
             "description_preview": r.description[:120] + ("…" if len(r.description) > 120 else "")}
            for r in reqs
        ],
    })


def cmd_show(args):
    """Show a requirement with full FRET status for refinement session."""
    _, conn, _ = ps.resolve(args.project)
    req = db.get_requirement(conn, args.id)
    if not req:
        _err(f"Requirement '{args.id}' not found.")
    _ok({
        "id":             req.id,
        "req_type":       req.req_type.value,
        "title":          req.title,
        "description":    req.description,
        "status":         req.status.value,
        "priority":       req.priority.value,
        "fret_statement": req.fret_statement or "(none — needs refinement)",
        "fret_fields":    req.fret_fields or {},
        "has_fret":       bool(req.fret_statement),
    })


def cmd_apply(args):
    """
    Write a confirmed FRET statement and field breakdown to a requirement.
    Called by the agent after user approves the proposed statement.
    """
    slug, conn, _ = ps.resolve(args.project)

    # Validate the fret_fields JSON if provided
    fret_fields = None
    if args.fret_fields:
        try:
            fret_fields = json.loads(args.fret_fields)
            if not isinstance(fret_fields, dict):
                _err("--fret-fields must be a JSON object")
        except json.JSONDecodeError as e:
            _err(f"Invalid JSON for --fret-fields: {e}")

    changes = {
        "fret_statement": args.fret_statement,
        "fret_fields":    fret_fields,
    }
    # Optionally update description with a refined version
    if args.description:
        changes["description"] = args.description

    try:
        row = db.update_requirement(
            conn, args.id, changes,
            changed_by=args.by,
            summary=args.summary or "FRET statement applied.",
        )
    except (KeyError, ValueError) as e:
        _err(str(e))

    ps.refresh_md(slug, conn)
    _ok({
        "id":             row.id,
        "fret_statement": row.fret_statement,
        "fret_fields":    row.fret_fields,
        "updated_at":     row.updated_at.isoformat(),
    })


def cmd_coverage(args):
    """Show FRET coverage across all requirements."""
    _, conn, _ = ps.resolve(args.project)
    all_reqs   = db.search_requirements(conn)
    with_fret  = [r for r in all_reqs if r.fret_statement]
    without    = [r for r in all_reqs if not r.fret_statement]
    total      = len(all_reqs)
    pct        = (len(with_fret) / total * 100) if total else 0

    # Break down by type
    by_type = {}
    for r in all_reqs:
        t = r.req_type.value
        if t not in by_type:
            by_type[t] = {"total": 0, "with_fret": 0}
        by_type[t]["total"] += 1
        if r.fret_statement:
            by_type[t]["with_fret"] += 1

    _ok({
        "total":      total,
        "with_fret":  len(with_fret),
        "without_fret": len(without),
        "coverage_pct": round(pct, 1),
        "by_type":    by_type,
        "pending_ids": [r.id for r in without],
    })


def build_parser():
    p = argparse.ArgumentParser(description="FRET requirement refinement")
    p.add_argument("--project", default=None)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("pending")

    sh = sub.add_parser("show")
    sh.add_argument("--id", required=True)

    ap = sub.add_parser("apply")
    ap.add_argument("--id",              required=True)
    ap.add_argument("--by",              required=True)
    ap.add_argument("--fret-statement",  dest="fret_statement", required=True,
                    help="The full assembled FRET sentence")
    ap.add_argument("--fret-fields",     dest="fret_fields",
                    help='JSON object: {"scope":"...","condition":"...","component":"...","timing":"...","response":"..."}')
    ap.add_argument("--description",     default=None,
                    help="Optionally update the plain-language description too")
    ap.add_argument("--summary",         default="FRET statement applied.")

    sub.add_parser("coverage")

    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    {"pending": cmd_pending, "show": cmd_show,
     "apply": cmd_apply, "coverage": cmd_coverage}[args.command](args)
