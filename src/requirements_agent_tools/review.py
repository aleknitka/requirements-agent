"""
review.py — requirements gap analysis, conflict detection, coverage checks.

Commands
────────
  gaps       Identify missing requirement types, incomplete fields, no-FRET items
  conflicts  Flag potential conflicts (same component, opposing conditions/timings)
  coverage   Cross-check requirements against success criteria
  report     Full review report (runs all checks, outputs structured summary)
"""

import argparse
from collections import defaultdict

from .project_session import get_project_conn
from .db.projects import get_project as _get_project
from ._cli_io import err as _err
from ._cli_io import ok as _ok
from .db.requirements import search_requirements
from .models import RequirementType


# ── Checks ────────────────────────────────────────────────────────────────────


def _check_gaps(reqs, meta) -> dict:
    """Identify gaps in requirement coverage across type, fields, and FRET.

    Flags: missing requirement types, requirements without descriptions,
    requirements without an owner, requirements without a FRET statement,
    and open critical requirements.

    Args:
        reqs: List of RequirementRow objects from the active project.
        meta: ProjectMeta for the active project.

    Returns:
        Dict with gap_count (int) and gaps (list of issue dicts).
    """
    issues = []
    present_types = {r.req_type.value for r in reqs}
    all_types = {t.value for t in RequirementType}
    missing_types = all_types - present_types

    if missing_types:
        issues.append(
            {
                "kind": "missing_types",
                "message": f"No requirements for: {', '.join(sorted(missing_types))}",
                "detail": sorted(missing_types),
            }
        )

    no_description = [r.id for r in reqs if not r.description.strip()]
    if no_description:
        issues.append(
            {
                "kind": "missing_description",
                "message": f"{len(no_description)} requirement(s) have no description",
                "ids": no_description,
            }
        )

    no_owner = [r.id for r in reqs if not r.owner]
    if no_owner:
        issues.append(
            {
                "kind": "no_owner",
                "message": f"{len(no_owner)} requirement(s) have no owner assigned",
                "ids": no_owner,
            }
        )

    no_fret = [r.id for r in reqs if not getattr(r, "fret_statement", None)]
    if no_fret:
        issues.append(
            {
                "kind": "no_fret",
                "message": f"{len(no_fret)} requirement(s) lack a FRET statement",
                "ids": no_fret,
            }
        )

    open_critical = [
        r.id
        for r in reqs
        if r.priority.value == "critical" and r.status.value == "open"
    ]
    if open_critical:
        issues.append(
            {
                "kind": "open_critical",
                "message": f"{len(open_critical)} CRITICAL requirement(s) still open",
                "ids": open_critical,
            }
        )

    return {"gap_count": len(issues), "gaps": issues}


def _check_conflicts(reqs) -> dict:
    """
    Heuristic conflict detection:
    - Two requirements reference the same component in fret_fields but have
      contradictory timing or response keywords.
    - Circular predecessor chains.
    """
    issues = []

    # Group by component
    by_component: dict = defaultdict(list)
    for r in reqs:
        fret_fields = getattr(r, "fret_fields", None)
        if fret_fields and fret_fields.get("component"):
            by_component[fret_fields["component"]].append(r)

    for component, group in by_component.items():
        if len(group) < 2:
            continue
        # Check for "always" vs "never" on same component
        always = [
            r
            for r in group
            if getattr(r, "fret_fields", {}).get("timing", "").startswith("always")
        ]
        never = [
            r
            for r in group
            if getattr(r, "fret_fields", {}).get("timing", "").startswith("never")
        ]
        if always and never:
            issues.append(
                {
                    "kind": "timing_conflict",
                    "component": component,
                    "message": f"'{component}' has both 'shall always' and 'shall never' requirements",
                    "always_ids": [r.id for r in always],
                    "never_ids": [r.id for r in never],
                }
            )

    # Check for circular predecessor chains (simple depth-first)
    id_to_req = {r.id: r for r in reqs}

    def has_cycle(req_id, visited=None):
        if visited is None:
            visited = set()
        if req_id in visited:
            return True
        visited.add(req_id)
        req = id_to_req.get(req_id)
        if not req:
            return False
        for p in req.predecessors:
            if p.kind == "internal" and has_cycle(p.ref, visited.copy()):
                return True
        return False

    for r in reqs:
        if has_cycle(r.id):
            issues.append(
                {
                    "kind": "circular_predecessor",
                    "message": f"Circular predecessor chain detected involving '{r.id}'",
                    "id": r.id,
                }
            )

    return {"conflict_count": len(issues), "conflicts": issues}


def _check_coverage(reqs, meta) -> dict:
    """Cross-check project success criteria against existing requirements.

    Extracts keywords from each criterion and checks whether any
    requirement's title, description, or FRET statement contains those
    keywords.

    Args:
        reqs: List of RequirementRow objects from the active project.
        meta: ProjectMeta containing the success_criteria list.

    Returns:
        Dict with criteria_total, criteria_covered, uncovered list,
        and per-criterion detail. Returns a skipped dict if no criteria
        are defined.
    """
    if not meta.success_criteria:
        return {
            "coverage_check": "skipped",
            "reason": "No success criteria defined in project metadata",
        }

    results = []
    for criterion in meta.success_criteria:
        # Extract keywords (words > 3 chars, lowercase)
        keywords = [w.lower() for w in criterion.split() if len(w) > 3]
        matched = []
        for r in reqs:
            haystack = f"{r.title} {r.description} {getattr(r, 'fret_statement', None) or ''}".lower()
            if any(kw in haystack for kw in keywords):
                matched.append(r.id)
        results.append(
            {
                "criterion": criterion,
                "matched_requirements": matched,
                "covered": len(matched) > 0,
            }
        )

    uncovered = [r["criterion"] for r in results if not r["covered"]]
    return {
        "criteria_total": len(results),
        "criteria_covered": len(results) - len(uncovered),
        "uncovered": uncovered,
        "detail": results,
    }


# ── Commands ──────────────────────────────────────────────────────────────────


def cmd_gaps(args):
    """Run gap analysis and output identified issues as JSON.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    conn = get_project_conn()
    meta = _get_project(conn)
    reqs = search_requirements(conn)
    _ok(_check_gaps(reqs, meta), fmt=args.format)


def cmd_conflicts(args):
    """Run conflict detection and output flagged conflicts as JSON.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    conn = get_project_conn()
    reqs = search_requirements(conn)
    _ok(_check_conflicts(reqs), fmt=args.format)


def cmd_coverage(args):
    """Run success criteria coverage check and output results as JSON.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    conn = get_project_conn()
    meta = _get_project(conn)
    reqs = search_requirements(conn)
    _ok(_check_coverage(reqs, meta), fmt=args.format)


def cmd_report(args):
    """Run all review checks and output a combined review report as JSON.

    Args:
        args: Parsed CLI arguments from build_parser().
    """
    conn = get_project_conn()
    meta = _get_project(conn)
    reqs = search_requirements(conn)

    if not meta:
        _err("No project metadata found in database.")

    gaps = _check_gaps(reqs, meta)
    conflicts = _check_conflicts(reqs)
    coverage = _check_coverage(reqs, meta)

    total_issues = gaps["gap_count"] + conflicts["conflict_count"]
    uncovered = len(coverage.get("uncovered", []))

    _ok(
        {
            "project": meta.name,
            "total_requirements": len(reqs),
            "total_issues": total_issues,
            "summary": {
                "gaps": gaps["gap_count"],
                "conflicts": conflicts["conflict_count"],
                "uncovered_criteria": uncovered,
            },
            "report": {  # Nest under 'report' for human formatting in _cli_io
                "gaps": gaps,
                "conflicts": conflicts,
                "coverage": coverage,
            },
            "recommendation": (
                "Requirements look complete."
                if total_issues == 0 and uncovered == 0
                else "Review flagged issues before moving to next phase."
            ),
        },
        fmt=args.format,
    )


def build_parser():
    """Build and return the review argument parser.

    Returns:
        Configured ArgumentParser with gaps, conflicts, coverage,
        and report subcommands.
    """
    p = argparse.ArgumentParser(description="Requirements review and gap analysis")
    p.add_argument(
        "--format",
        "-f",
        choices=["json", "human"],
        default="json",
        help="Output format (default: json).",
    )
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("gaps")
    sub.add_parser("conflicts")
    sub.add_parser("coverage")
    sub.add_parser("report")
    return p


def main():
    """Entry point for the review CLI."""
    args = build_parser().parse_args()
    {
        "gaps": cmd_gaps,
        "conflicts": cmd_conflicts,
        "coverage": cmd_coverage,
        "report": cmd_report,
    }[args.command](args)


if __name__ == "__main__":
    main()
