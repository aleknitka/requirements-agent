"""Tests for :mod:`requirements_mcp.services.reports.build_full_report`."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from requirements_mcp.schemas.issues import (
    IssueCreate,
    RequirementIssueLinkCreate,
)
from requirements_mcp.schemas.requirements import (
    RequirementCreate,
    RequirementUpdate,
)
from requirements_mcp.seeds.demo import apply_demo_data
from requirements_mcp.services.issues import (
    add_issue_update,
    create_issue,
    link_issue_to_requirement,
)
from requirements_mcp.schemas.issues import IssueUpdateAdd
from requirements_mcp.services.reports import build_full_report
from requirements_mcp.services.requirements import (
    create_requirement,
    update_requirement,
)


def _make_req(session: Session, *, title: str, status: str = "draft") -> str:
    req = create_requirement(
        session,
        RequirementCreate(
            title=title,
            requirement_statement="x",
            type_code="FUN",
            author="alice",
            status_code=status,  # type: ignore[arg-type]
        ),
    )
    session.commit()
    return req.id


def _make_issue(
    session: Session,
    *,
    title: str = "issue",
    issue_type: str = "AMB",
    priority: str = "MED",
) -> str:
    issue = create_issue(
        session,
        IssueCreate(
            title=title,
            description="x",
            issue_type_code=issue_type,  # type: ignore[arg-type]
            priority_code=priority,  # type: ignore[arg-type]
            created_by="alice",
        ),
    )
    session.commit()
    return issue.id


def test_empty_db_returns_empty_lists(seeded_session: Session) -> None:
    report = build_full_report(seeded_session)
    assert report.requirements == []
    assert report.unattached_issues == []
    assert report.summary.requirement_count == 0
    assert report.summary.issue_count == 0


def test_requirements_sorted_by_status(seeded_session: Session) -> None:
    # Status sort_order: draft=10, in_review=20, approved=40 (per the seed list).
    _make_req(seeded_session, title="A-approved", status="approved")
    _make_req(seeded_session, title="B-draft", status="draft")
    _make_req(seeded_session, title="C-review", status="in_review")

    report = build_full_report(seeded_session)
    titles = [r.title for r in report.requirements]
    assert titles == ["B-draft", "C-review", "A-approved"]


def test_attached_issues_nested_under_requirement(seeded_session: Session) -> None:
    req_id = _make_req(seeded_session, title="parent")
    issue_id = _make_issue(seeded_session, title="child")
    link_issue_to_requirement(
        seeded_session,
        issue_id,
        RequirementIssueLinkCreate(
            requirement_id=req_id,
            link_type="clarifies",
            rationale="needs detail",
            author="alice",
        ),
    )
    seeded_session.commit()

    report = build_full_report(seeded_session)
    assert len(report.requirements) == 1
    nested = report.requirements[0].issues
    assert len(nested) == 1
    assert nested[0].id == issue_id
    assert nested[0].link_type == "clarifies"
    assert nested[0].rationale == "needs detail"
    assert report.unattached_issues == []


def test_issues_sorted_by_priority_severity_desc(seeded_session: Session) -> None:
    req_id = _make_req(seeded_session, title="parent")
    low = _make_issue(seeded_session, title="low", priority="LOW")
    crt = _make_issue(seeded_session, title="crt", priority="CRT")
    med = _make_issue(seeded_session, title="med", priority="MED")
    for iid in (low, crt, med):
        link_issue_to_requirement(
            seeded_session,
            iid,
            RequirementIssueLinkCreate(
                requirement_id=req_id, link_type="related", author="alice"
            ),
        )
    seeded_session.commit()

    report = build_full_report(seeded_session)
    priorities = [i.priority_code for i in report.requirements[0].issues]
    assert priorities == ["CRT", "MED", "LOW"]


def test_unattached_issues_collected(seeded_session: Session) -> None:
    issue_id = _make_issue(seeded_session, title="orphan")
    report = build_full_report(seeded_session)
    assert report.requirements == []
    assert len(report.unattached_issues) == 1
    assert report.unattached_issues[0].id == issue_id
    assert report.unattached_issues[0].link_type is None


def test_full_audit_trail_present(seeded_session: Session) -> None:
    req_id = _make_req(seeded_session, title="t")
    update_requirement(
        seeded_session,
        req_id,
        RequirementUpdate(
            author="bob", change_description="approve", status_code="approved"
        ),
    )
    issue_id = _make_issue(seeded_session, title="i")
    link_issue_to_requirement(
        seeded_session,
        issue_id,
        RequirementIssueLinkCreate(
            requirement_id=req_id, link_type="related", author="alice"
        ),
    )
    add_issue_update(
        seeded_session,
        issue_id,
        IssueUpdateAdd(
            update_type_code="note", description="follow-up", author="alice"
        ),
    )
    seeded_session.commit()

    report = build_full_report(seeded_session)
    [requirement] = report.requirements
    # creation row + status update
    assert len(requirement.changes) == 2
    [issue] = requirement.issues
    # creation + requirement_linked + note
    assert len(issue.updates) >= 3


def test_include_issues_false_omits_issues(seeded_session: Session) -> None:
    req_id = _make_req(seeded_session, title="parent")
    issue_id = _make_issue(seeded_session, title="child")
    link_issue_to_requirement(
        seeded_session,
        issue_id,
        RequirementIssueLinkCreate(
            requirement_id=req_id, link_type="related", author="alice"
        ),
    )
    _make_issue(seeded_session, title="orphan")
    seeded_session.commit()

    report = build_full_report(seeded_session, include_issues=False)
    assert len(report.requirements) == 1
    assert report.requirements[0].issues == []
    # Audit history is still rendered.
    assert report.requirements[0].changes
    assert report.unattached_issues == []
    assert report.summary.included_issues is False


def test_include_closed_requirements_false_filters_terminal(
    seeded_session: Session,
) -> None:
    _make_req(seeded_session, title="alive", status="draft")
    _make_req(seeded_session, title="done", status="verified")  # terminal
    _make_req(seeded_session, title="killed", status="rejected")  # terminal

    report = build_full_report(seeded_session, include_closed_requirements=False)
    titles = {r.title for r in report.requirements}
    assert titles == {"alive"}
    assert report.summary.included_closed_requirements is False


def test_default_call_returns_complete_dataset(seeded_session: Session) -> None:
    """Bare call: closed reqs included, attached + unattached issues included."""
    req_id = _make_req(seeded_session, title="alive", status="draft")
    closed_id = _make_req(seeded_session, title="done", status="verified")
    attached_id = _make_issue(seeded_session, title="attached")
    link_issue_to_requirement(
        seeded_session,
        attached_id,
        RequirementIssueLinkCreate(
            requirement_id=req_id, link_type="related", author="alice"
        ),
    )
    _make_issue(seeded_session, title="orphan")
    seeded_session.commit()

    report = build_full_report(seeded_session)

    titles = {r.title for r in report.requirements}
    assert {"alive", "done"} <= titles, "closed requirement must appear by default"
    assert any(closed_id == r.id for r in report.requirements)

    attached_titles = {i.title for r in report.requirements for i in r.issues}
    assert "attached" in attached_titles

    orphan_titles = {i.title for i in report.unattached_issues}
    assert "orphan" in orphan_titles

    assert report.summary.included_issues is True
    assert report.summary.included_closed_requirements is True


def test_uses_demo_data(seeded_session: Session) -> None:
    apply_demo_data(seeded_session)
    seeded_session.commit()

    report = build_full_report(seeded_session)
    assert len(report.requirements) == 10
    assert len(report.unattached_issues) == 2  # 5 demo issues − 3 linked
    # Three demo links, and they sit under three different requirements.
    attached_total = sum(len(r.issues) for r in report.requirements)
    assert attached_total == 3


def test_summary_counts_match_lists(seeded_session: Session) -> None:
    apply_demo_data(seeded_session)
    seeded_session.commit()

    report = build_full_report(seeded_session)
    s = report.summary
    assert s.requirement_count == len(report.requirements)
    assert s.unattached_issue_count == len(report.unattached_issues)
    assert s.attached_issue_count == sum(len(r.issues) for r in report.requirements)
    assert s.issue_count == s.attached_issue_count + s.unattached_issue_count
    assert s.included_issues is True
    assert s.included_closed_requirements is True


def test_dump_is_json_round_trippable(seeded_session: Session) -> None:
    apply_demo_data(seeded_session)
    seeded_session.commit()

    report = build_full_report(seeded_session)
    payload = report.model_dump(mode="json")
    # Round-trip through plain JSON to prove no Python-only types leaked.
    revived = json.loads(json.dumps(payload))
    assert set(revived.keys()) == {
        "generated_at",
        "project_name",
        "summary",
        "requirements",
        "unattached_issues",
    }
    assert isinstance(revived["generated_at"], str)
    assert revived["project_name"]
    assert isinstance(revived["requirements"], list)
    assert isinstance(revived["unattached_issues"], list)
