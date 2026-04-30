"""
report.py — generate a structured project status report.

Commands
────────
  generate   Pull current state from DB and produce a status report (JSON + MD)
  save       Write the report to a timestamped file alongside PROJECT.md
"""

import argparse
import json
from datetime import datetime, timezone
from . import CONSTANTS as C
from ._cli_io import ok as _ok
from .db.minutes import list_decisions, list_minutes
from .db.requirements import search_requirements
from .db.updates import get_updates
from .project_session import get_project_conn
from .db.projects import get_project as _get_project


def _build_report(conn, meta) -> dict:
    """Assemble the full status report dict from the project DB.

    Queries requirements, meetings, decisions, action items, and recent
    changes to produce a structured report dict suitable for JSON output
    or Markdown rendering.

    Args:
        conn: Open SQLite connection to the project DB.
        meta: ProjectMeta instance for the project.

    Returns:
        Dict containing project metadata, requirement counts, FRET
        coverage, meeting/decision/action summaries, and a health signal.
    """
    reqs = search_requirements(conn)
    mins = list_minutes(conn)
    decs = list_decisions(conn)

    req_counts: dict = {}
    status_counts: dict = {}
    for r in reqs:
        req_counts[r.req_type.value] = req_counts.get(r.req_type.value, 0) + 1
        status_counts[r.status.value] = status_counts.get(r.status.value, 0) + 1

    with_fret = sum(1 for r in reqs if getattr(r, "fret_statement", None))
    total = len(reqs)
    fret_pct = round(with_fret / total * 100, 1) if total else 0

    open_decs = [d for d in decs if d["status"] == "open"]
    pending_acts = [a for m in mins for a in m.action_items if not a.done]
    unint_mins = [m for m in mins if not m.integrated_into_status]

    # Recent changes (last 5 update records across all reqs)
    recent_changes = []
    for req in sorted(reqs, key=lambda r: r.updated_at, reverse=True)[:10]:
        updates = get_updates(conn, req.id)
        if updates:
            latest = updates[-1]
            recent_changes.append(
                {
                    "req_id": req.id,
                    "title": req.title,
                    "changed_at": latest.changed_at.isoformat(),
                    "changed_by": latest.changed_by,
                    "summary": latest.summary,
                }
            )
    recent_changes = sorted(
        recent_changes, key=lambda x: x["changed_at"], reverse=True
    )[:5]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "name": meta.name,
            "code": meta.code,
            "phase": meta.phase.value,
            "project_owner": meta.project_owner,
            "sponsor": meta.sponsor,
            "target_date": str(meta.target_date) if meta.target_date else None,
        },
        "requirements": {
            "total": total,
            "by_type": req_counts,
            "by_status": status_counts,
            "fret_coverage": f"{with_fret}/{total} ({fret_pct}%)",
            "critical_open": [
                r.id
                for r in reqs
                if r.priority.value == "critical" and r.status.value == "open"
            ],
        },
        "meetings": {
            "total": len(mins),
            "unintegrated": len(unint_mins),
            "unintegrated_ids": [m.id for m in unint_mins],
        },
        "decisions": {
            "total": len(decs),
            "open": len(open_decs),
            "open_items": [
                {
                    "decision_id": d["decision_id"],
                    "title": d["title"],
                    "made_by": d["made_by"],
                    "action_owner": d.get("action_owner"),
                    "due_date": str(d.get("due_date")) if d.get("due_date") else None,
                }
                for d in open_decs
            ],
        },
        "action_items": {
            "pending": len(pending_acts),
            "pending_items": [
                {
                    "action_id": a.action_id,
                    "description": a.description,
                    "owner": a.owner,
                    "due_date": str(a.due_date) if a.due_date else None,
                }
                for a in pending_acts
            ],
        },
        "recent_changes": recent_changes,
        "status_summary": meta.status_summary or "(no status summary written yet)",
        "health": _health_signal(reqs, open_decs, pending_acts, unint_mins),
    }


def _health_signal(reqs, open_decs, pending_acts, unint_mins) -> str:
    """Simple traffic-light based on open criticals + overdue items."""
    critical_open = sum(
        1 for r in reqs if r.priority.value == "critical" and r.status.value == "open"
    )
    if critical_open > 3 or len(open_decs) > 5:
        return "RED — significant open issues require attention"
    if critical_open > 0 or len(pending_acts) > 5 or len(unint_mins) > 3:
        return "AMBER — some items need follow-up"
    return "GREEN — project looks on track"


def _report_to_md(report: dict) -> str:
    """Render a report dict as a Markdown status report string.

    Args:
        report: Report dict produced by _build_report().

    Returns:
        Multi-line Markdown string suitable for writing to a .md file.
    """
    r = report
    proj = r["project"]
    reqs = r["requirements"]
    now = r["generated_at"][:10]

    lines = [
        f"# Status Report — {proj['name']}",
        f"> Generated {now}  |  Phase: {proj['phase']}  |  Health: **{r['health']}**",
        "",
        "## Project",
        f"- **Owner:** {proj['project_owner'] or 'TBD'}",
        f"- **Sponsor:** {proj['sponsor'] or 'TBD'}",
        f"- **Target date:** {proj['target_date'] or 'TBD'}",
        "",
        "## Requirements",
        f"- Total: **{reqs['total']}**",
        f"- FRET coverage: {reqs['fret_coverage']}",
        "- By type: "
        + ", ".join(f"{k}: {v}" for k, v in sorted(reqs["by_type"].items())),
        "- By status: "
        + ", ".join(f"{k}: {v}" for k, v in sorted(reqs["by_status"].items())),
    ]
    if reqs["critical_open"]:
        lines.append(f"- ⚠️ Critical & open: {', '.join(reqs['critical_open'])}")

    lines += [
        "",
        f"## Open Decisions ({r['decisions']['open']})",
    ]
    for d in r["decisions"]["open_items"]:
        owner = f" → {d['action_owner']}" if d.get("action_owner") else ""
        due = f" (due {d['due_date']})" if d.get("due_date") else ""
        lines.append(f"- [{d['decision_id']}] {d['title']}{owner}{due}")

    lines += [
        "",
        f"## Pending Actions ({r['action_items']['pending']})",
    ]
    for a in r["action_items"]["pending_items"]:
        owner = f" — {a['owner']}" if a.get("owner") else ""
        due = f" (due {a['due_date']})" if a.get("due_date") else ""
        lines.append(f"- [{a['action_id']}]{owner} {a['description']}{due}")

    lines += [
        "",
        "## Recent Changes",
    ]
    for c in r["recent_changes"]:
        lines.append(
            f"- [{c['req_id']}] {c['title']} — {c['summary']} ({c['changed_by']}, {c['changed_at'][:10]})"
        )

    lines += [
        "",
        "## Status Summary",
        "",
        r["status_summary"],
    ]
    return "\n".join(lines)


def cmd_generate(args):
    """Generate a project status report and print it to stdout.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    conn = get_project_conn()
    meta = _get_project(conn)
    report = _build_report(conn, meta)
    if args.format == "md":
        print(_report_to_md(report))
    else:
        _ok({"report": report})


def cmd_save(args):
    """Generate a project status report and save it to timestamped files.

    Writes both a Markdown file (STATUS-<timestamp>.md) and a JSON file
    (STATUS-<timestamp>.json) to the project directory.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    conn = get_project_conn()
    meta = _get_project(conn)
    report = _build_report(conn, meta)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    md_out = C.PROJECT_DIR / f"STATUS-{ts}.md"
    json_out = C.PROJECT_DIR / f"STATUS-{ts}.json"

    md_out.write_text(_report_to_md(report), encoding="utf-8")
    json_out.write_text(
        json.dumps({"ok": True, "report": report}, indent=2, default=str),
        encoding="utf-8",
    )

    _ok({"md": str(md_out), "json": str(json_out), "health": report["health"]})


def build_parser():
    """Build and return the report argument parser.

    Returns:
        Configured ArgumentParser with generate and save subcommands.
    """
    p = argparse.ArgumentParser(description="Status report generator")
    sub = p.add_subparsers(dest="command", required=True)

    gn = sub.add_parser("generate")
    gn.add_argument("--format", choices=["json", "md"], default="json")

    sub.add_parser("save")
    return p


def main():
    """Entry point for the report CLI."""
    args = build_parser().parse_args()
    {"generate": cmd_generate, "save": cmd_save}[args.command](args)


if __name__ == "__main__":
    main()
