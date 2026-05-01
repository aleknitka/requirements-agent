"""
report.py — generate a structured project status report.

Commands
────────
  generate   Pull current state from DB and produce a status report (JSON + MD)
  save       Write the report to a timestamped file alongside PROJECT.md
"""

import argparse
from datetime import datetime, timezone
from ._cli_io import ok as _ok
from .db.issues import search_issues
from .db.requirements import search_requirements
from .db.updates import get_updates
from .project_session import get_project_conn
from .db.projects import get_project as _get_project


def _build_report(conn, meta) -> dict:
    """Assemble the full status report dict from the project DB.

    Queries requirements, issues, and recent changes to produce a
    structured report dict suitable for JSON output or Markdown rendering.

    Args:
        conn: Open SQLite connection to the project DB.
        meta: ProjectMeta instance for the project.

    Returns:
        Dict containing project metadata, requirement counts, FRET
        coverage, issue summaries, and a health signal.
    """
    reqs = search_requirements(conn)
    issues = search_issues(conn)

    req_counts: dict = {}
    status_counts: dict = {}
    for r in reqs:
        req_counts[r.req_type.value] = req_counts.get(r.req_type.value, 0) + 1
        status_counts[r.status.value] = status_counts.get(r.status.value, 0) + 1

    with_fret = sum(1 for r in reqs if getattr(r, "fret_statement", None))
    total = len(reqs)
    fret_pct = round(with_fret / total * 100, 1) if total else 0

    open_issues = [i for i in issues if i.status.value in ("open", "in-progress")]

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
        "issues": {
            "total": len(issues),
            "open": len(open_issues),
            "open_items": [
                {
                    "id": i.id,
                    "title": i.title,
                    "priority": i.priority.value,
                    "status": i.status.value,
                    "owner": i.owner,
                }
                for i in open_issues
            ],
        },
        "recent_changes": recent_changes,
        "status_summary": meta.status_summary or "(no status summary written yet)",
        "health": _health_signal(reqs, open_issues),
    }


def _health_signal(reqs, open_issues) -> str:
    """Simple traffic-light based on open criticals + issues."""
    critical_open = sum(
        1 for r in reqs if r.priority.value == "critical" and r.status.value == "open"
    )
    if critical_open > 3 or len(open_issues) > 10:
        return "RED — significant open issues require attention"
    if critical_open > 0 or len(open_issues) > 3:
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
        f"## Open Issues ({r['issues']['open']})",
    ]
    for i in r["issues"]["open_items"]:
        owner = f" — {i['owner']}" if i.get("owner") else ""
        lines.append(f"- [{i['id']}] {i['title']}{owner} ({i['priority']})")

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
    elif args.format == "human":
        _ok({"report": report}, fmt="human")
    else:
        _ok({"report": report})


def build_parser():
    """Build and return the report argument parser.

    Returns:
        Configured ArgumentParser with generate subcommand.
    """
    p = argparse.ArgumentParser(description="Status report generator")
    p.add_argument(
        "--format",
        "-f",
        choices=["json", "md", "human"],
        default="json",
        help="Output format (default: json).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("generate")
    return p


def main():
    """Entry point for the report CLI."""
    args = build_parser().parse_args()
    {"generate": cmd_generate}[args.command](args)


if __name__ == "__main__":
    main()
