"""
init.py — project initialisation.

Commands
────────
  new      Interview user → create <slug>.db + PROJECT.md
  list     List all existing projects
  update   Update metadata fields for an existing project
"""

import argparse
import json
import sys
from pathlib import Path

# Resolve shared library regardless of working directory
_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "shared"))

import CONSTANTS as C
import db
import md_writer
import project_session as ps
from models import ExternalLink, ProjectMeta, ProjectPhase, Stakeholder


def _ok(data: dict) -> None:
    print(json.dumps({"ok": True, **data}, indent=2, default=str))

def _err(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}), file=sys.stderr)
    sys.exit(1)

def _parse_json(raw, label):
    if not raw:
        return []
    try:
        v = json.loads(raw)
        assert isinstance(v, list)
        return v
    except Exception:
        _err(f"--{label} must be a valid JSON array")


def cmd_new(args: argparse.Namespace) -> None:
    slug = C.slugify(args.name)

    # Guard: prevent duplicate slugs
    existing = db.list_all_projects()
    if any(p["slug"] == slug for p in existing):
        _err(
            f"A project with slug '{slug}' already exists. "
            "Use 'update' to modify it, or choose a different name."
        )

    meta = ProjectMeta(
        slug=slug,
        name=args.name,
        code=args.code,
        phase=ProjectPhase(args.phase) if args.phase else ProjectPhase.DISCOVERY,
        objective=args.objective or "",
        business_case=args.business_case or "",
        success_criteria=_parse_json(args.success_criteria, "success-criteria"),
        out_of_scope=_parse_json(args.out_of_scope, "out-of-scope"),
        project_owner=args.project_owner,
        sponsor=args.sponsor,
        stakeholders=[Stakeholder(**s) for s in _parse_json(args.stakeholders, "stakeholders")],
        external_links=[ExternalLink(**l) for l in _parse_json(args.external_links, "external-links")],
    )

    conn = db.get_db(slug)
    db.upsert_project(conn, meta)
    md = ps.refresh_md(slug, conn)

    _ok({
        "project_id": meta.project_id,
        "slug":       slug,
        "name":       meta.name,
        "db":         str(C.db_path(slug)),
        "md":         str(md),
    })


def cmd_list(args: argparse.Namespace) -> None:
    projects = db.list_all_projects()
    if not projects:
        _ok({"count": 0, "projects": [],
             "message": "No projects yet. Run: python init.py new --name '<Project Name>'"})
        return
    _ok({"count": len(projects), "projects": projects})


def cmd_update(args: argparse.Namespace) -> None:
    slug, conn, meta = ps.resolve(args.project)

    SIMPLE = ["name", "code", "objective", "business_case",
              "project_owner", "sponsor", "start_date",
              "target_date", "actual_end_date", "status_summary"]
    for f in SIMPLE:
        v = getattr(args, f, None)
        if v is not None:
            setattr(meta, f, v)

    if args.phase:
        meta.phase = ProjectPhase(args.phase)
    if args.success_criteria is not None:
        meta.success_criteria = _parse_json(args.success_criteria, "success-criteria")
    if args.out_of_scope is not None:
        meta.out_of_scope = _parse_json(args.out_of_scope, "out-of-scope")
    if args.stakeholders is not None:
        meta.stakeholders = [Stakeholder(**s)    for s in _parse_json(args.stakeholders, "stakeholders")]
    if args.external_links is not None:
        meta.external_links = [ExternalLink(**l) for l in _parse_json(args.external_links, "external-links")]

    db.upsert_project(conn, meta)
    md = ps.refresh_md(slug, conn)
    _ok({"slug": slug, "md": str(md), "message": "Project metadata updated."})


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Project initialisation")
    sub = p.add_subparsers(dest="command", required=True)
    PHASES = [ph.value for ph in ProjectPhase]

    # new
    nw = sub.add_parser("new")
    nw.add_argument("--name",             required=True)
    nw.add_argument("--code")
    nw.add_argument("--phase",            choices=PHASES, default="discovery")
    nw.add_argument("--objective",        default="")
    nw.add_argument("--business-case",    dest="business_case", default="")
    nw.add_argument("--project-owner",    dest="project_owner")
    nw.add_argument("--sponsor")
    nw.add_argument("--success-criteria", dest="success_criteria")
    nw.add_argument("--out-of-scope",     dest="out_of_scope")
    nw.add_argument("--stakeholders")
    nw.add_argument("--external-links",   dest="external_links")

    # list
    sub.add_parser("list")

    # update
    up = sub.add_parser("update")
    up.add_argument("--project",          required=True, help="Slug or partial name")
    up.add_argument("--name")
    up.add_argument("--code")
    up.add_argument("--phase",            choices=PHASES)
    up.add_argument("--objective")
    up.add_argument("--business-case",    dest="business_case")
    up.add_argument("--project-owner",    dest="project_owner")
    up.add_argument("--sponsor")
    up.add_argument("--start-date",       dest="start_date")
    up.add_argument("--target-date",      dest="target_date")
    up.add_argument("--actual-end-date",  dest="actual_end_date")
    up.add_argument("--status-summary",   dest="status_summary")
    up.add_argument("--success-criteria", dest="success_criteria")
    up.add_argument("--out-of-scope",     dest="out_of_scope")
    up.add_argument("--stakeholders")
    up.add_argument("--external-links",   dest="external_links")

    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    {"new": cmd_new, "list": cmd_list, "update": cmd_update}[args.command](args)
