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
import json
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT / "shared"))

import db
import project_session as ps
from models import RequirementType


def _ok(data):  print(json.dumps({"ok": True,  **data}, indent=2, default=str))
def _err(msg):  print(json.dumps({"ok": False, "error": msg}), file=sys.stderr); sys.exit(1)


# ── Checks ────────────────────────────────────────────────────────────────────

def _check_gaps(reqs, meta) -> dict:
    issues = []
    present_types = {r.req_type.value for r in reqs}
    all_types     = {t.value for t in RequirementType}
    missing_types = all_types - present_types

    if missing_types:
        issues.append({
            "kind":    "missing_types",
            "message": f"No requirements for: {', '.join(sorted(missing_types))}",
            "detail":  sorted(missing_types),
        })

    no_description = [r.id for r in reqs if not r.description.strip()]
    if no_description:
        issues.append({
            "kind":    "missing_description",
            "message": f"{len(no_description)} requirement(s) have no description",
            "ids":     no_description,
        })

    no_owner = [r.id for r in reqs if not r.owner]
    if no_owner:
        issues.append({
            "kind":    "no_owner",
            "message": f"{len(no_owner)} requirement(s) have no owner assigned",
            "ids":     no_owner,
        })

    no_fret = [r.id for r in reqs if not r.fret_statement]
    if no_fret:
        issues.append({
            "kind":    "no_fret",
            "message": f"{len(no_fret)} requirement(s) lack a FRET statement",
            "ids":     no_fret,
        })

    open_critical = [r.id for r in reqs
                     if r.priority.value == "critical" and r.status.value == "open"]
    if open_critical:
        issues.append({
            "kind":    "open_critical",
            "message": f"{len(open_critical)} CRITICAL requirement(s) still open",
            "ids":     open_critical,
        })

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
        if r.fret_fields and r.fret_fields.get("component"):
            by_component[r.fret_fields["component"]].append(r)

    for component, group in by_component.items():
        if len(group) < 2:
            continue
        # Check for "always" vs "never" on same component
        always = [r for r in group if r.fret_fields.get("timing", "").startswith("always")]
        never  = [r for r in group if r.fret_fields.get("timing", "").startswith("never")]
        if always and never:
            issues.append({
                "kind":      "timing_conflict",
                "component": component,
                "message":   f"'{component}' has both 'shall always' and 'shall never' requirements",
                "always_ids":[r.id for r in always],
                "never_ids": [r.id for r in never],
            })

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
            issues.append({
                "kind":    "circular_predecessor",
                "message": f"Circular predecessor chain detected involving '{r.id}'",
                "id":      r.id,
            })

    return {"conflict_count": len(issues), "conflicts": issues}


def _check_coverage(reqs, meta) -> dict:
    """
    Cross-check success criteria against requirements.
    For each criterion, look for requirements whose title/description/fret_statement
    contains keywords from the criterion.
    """
    if not meta.success_criteria:
        return {"coverage_check": "skipped", "reason": "No success criteria defined in project metadata"}

    results = []
    for criterion in meta.success_criteria:
        # Extract keywords (words > 3 chars, lowercase)
        keywords = [w.lower() for w in criterion.split() if len(w) > 3]
        matched  = []
        for r in reqs:
            haystack = f"{r.title} {r.description} {r.fret_statement or ''}".lower()
            if any(kw in haystack for kw in keywords):
                matched.append(r.id)
        results.append({
            "criterion": criterion,
            "matched_requirements": matched,
            "covered": len(matched) > 0,
        })

    uncovered = [r["criterion"] for r in results if not r["covered"]]
    return {
        "criteria_total":   len(results),
        "criteria_covered": len(results) - len(uncovered),
        "uncovered":        uncovered,
        "detail":           results,
    }


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_gaps(args):
    _, conn, meta = ps.resolve(args.project)
    reqs = db.search_requirements(conn)
    _ok(_check_gaps(reqs, meta))


def cmd_conflicts(args):
    _, conn, _ = ps.resolve(args.project)
    reqs = db.search_requirements(conn)
    _ok(_check_conflicts(reqs))


def cmd_coverage(args):
    _, conn, meta = ps.resolve(args.project)
    reqs = db.search_requirements(conn)
    _ok(_check_coverage(reqs, meta))


def cmd_report(args):
    _, conn, meta = ps.resolve(args.project)
    reqs = db.search_requirements(conn)

    gaps      = _check_gaps(reqs, meta)
    conflicts = _check_conflicts(reqs)
    coverage  = _check_coverage(reqs, meta)

    total_issues = gaps["gap_count"] + conflicts["conflict_count"]
    uncovered    = len(coverage.get("uncovered", []))

    _ok({
        "project":          meta.name,
        "total_requirements": len(reqs),
        "total_issues":     total_issues,
        "summary": {
            "gaps":            gaps["gap_count"],
            "conflicts":       conflicts["conflict_count"],
            "uncovered_criteria": uncovered,
        },
        "gaps":      gaps,
        "conflicts": conflicts,
        "coverage":  coverage,
        "recommendation": (
            "Requirements look complete." if total_issues == 0 and uncovered == 0
            else "Review flagged issues before moving to next phase."
        ),
    })


def build_parser():
    p = argparse.ArgumentParser(description="Requirements review and gap analysis")
    p.add_argument("--project", default=None)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("gaps")
    sub.add_parser("conflicts")
    sub.add_parser("coverage")
    sub.add_parser("report")
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    {"gaps": cmd_gaps, "conflicts": cmd_conflicts,
     "coverage": cmd_coverage, "report": cmd_report}[args.command](args)