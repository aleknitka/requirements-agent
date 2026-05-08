"""Tests for :mod:`requirements_mcp.services.issues`.

Covers the audit-trail invariant: every successful issue mutation
(create, update, add_issue_update, link, unlink) emits a matching
``issue_updates`` row.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from requirements_mcp.models import (
    Issue,
    Requirement,
    RequirementIssueLink,
)
from requirements_mcp.models import IssueUpdate as IssueUpdateRow
from requirements_mcp.schemas.issues import (
    IssueCreate,
    IssueSearchQuery,
    IssueUpdate,
    IssueUpdateAdd,
    RequirementIssueLinkCreate,
)
from requirements_mcp.schemas.requirements import RequirementCreate
from requirements_mcp.services.issues import (
    IssueNotFoundError,
    RequirementIssueLinkAlreadyExistsError,
    RequirementIssueLinkNotFoundError,
    add_issue_update,
    create_issue,
    get_issue,
    link_issue_to_requirement,
    list_blocking_issues,
    list_issue_priorities,
    list_issue_statuses,
    list_issue_types,
    list_issue_updates,
    list_open_issues,
    search_issues,
    unlink_issue_from_requirement,
    update_issue,
)
from requirements_mcp.services.requirements import (
    RequirementNotFoundError,
    create_requirement,
)


def _create_payload(**overrides: object) -> IssueCreate:
    base: dict[str, object] = dict(
        title="Login flow ambiguous",
        description="SSO scope is unclear.",
        issue_type_code="AMB",
        created_by="agent",
    )
    base.update(overrides)
    return IssueCreate(**base)


def _update_count(session: Session, issue_id: str) -> int:
    return (
        session.query(IssueUpdateRow)
        .filter(IssueUpdateRow.issue_id == issue_id)
        .count()
    )


def _make_requirement(seeded_session: Session, **overrides: object) -> Requirement:
    base: dict[str, object] = dict(
        title="Login",
        requirement_statement="Users can log in.",
        type_code="FUN",
        author="alice",
    )
    base.update(overrides)
    req = create_requirement(seeded_session, RequirementCreate(**base))
    seeded_session.commit()
    return req


class TestCreateIssue:
    def test_inserts_issue_and_initial_update(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()

        assert issue.id
        assert issue.status_code == "open"
        assert issue.priority_code == "MED"
        assert issue.date_closed is None
        assert _update_count(seeded_session, issue.id) == 1

        update = (
            seeded_session.query(IssueUpdateRow)
            .filter(IssueUpdateRow.issue_id == issue.id)
            .one()
        )
        assert update.update_type_code == "created"
        assert update.diff == {}
        assert update.author == "agent"


class TestUpdateIssue:
    def test_status_change_records_diff_and_kind(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()

        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(
                author="alice",
                change_description="resolve",
                status_code="resolved",
            ),
        )
        seeded_session.commit()

        latest = (
            seeded_session.query(IssueUpdateRow)
            .filter(IssueUpdateRow.issue_id == issue.id)
            .order_by(IssueUpdateRow.date.desc())
            .first()
        )
        assert latest is not None
        assert latest.update_type_code == "status_changed"
        assert latest.diff == {"status_code": {"from": "open", "to": "resolved"}}

    def test_priority_only_change_kind(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(
                author="alice",
                change_description="raise prio",
                priority_code="HIG",
            ),
        )
        seeded_session.commit()
        latest = (
            seeded_session.query(IssueUpdateRow)
            .filter(IssueUpdateRow.issue_id == issue.id)
            .order_by(IssueUpdateRow.date.desc())
            .first()
        )
        assert latest is not None
        assert latest.update_type_code == "priority_changed"

    def test_multi_field_change_is_field_changed(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(
                author="alice",
                change_description="rework",
                title="Login flow ambiguous (revised)",
                description="Updated narrative.",
            ),
        )
        seeded_session.commit()
        latest = (
            seeded_session.query(IssueUpdateRow)
            .filter(IssueUpdateRow.issue_id == issue.id)
            .order_by(IssueUpdateRow.date.desc())
            .first()
        )
        assert latest is not None
        assert latest.update_type_code == "field_changed"
        assert set(latest.diff) == {"title", "description"}

    def test_terminal_status_sets_date_closed(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        assert issue.date_closed is None

        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(
                author="alice",
                change_description="close",
                status_code="closed",
            ),
        )
        seeded_session.commit()
        assert issue.date_closed is not None

    def test_reopening_clears_date_closed(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(
                author="alice",
                change_description="close",
                status_code="closed",
            ),
        )
        seeded_session.commit()
        assert issue.date_closed is not None

        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(
                author="alice",
                change_description="reopen",
                status_code="reopened",
            ),
        )
        seeded_session.commit()
        assert issue.date_closed is None

    def test_no_op_writes_no_audit_row(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload(title="t"))
        seeded_session.commit()
        before = _update_count(seeded_session, issue.id)

        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(author="alice", change_description="no-op", title="t"),
        )
        seeded_session.commit()

        assert _update_count(seeded_session, issue.id) == before

    def test_unknown_id_raises(self, seeded_session: Session) -> None:
        with pytest.raises(IssueNotFoundError):
            update_issue(
                seeded_session,
                "missing",
                IssueUpdate(author="alice", change_description="x", title="t"),
            )

    def test_clearing_owner_recorded(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload(owner="bob"))
        seeded_session.commit()

        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(
                author="alice",
                change_description="unassign",
                owner=None,
            ),
        )
        seeded_session.commit()
        assert issue.owner is None

        latest = (
            seeded_session.query(IssueUpdateRow)
            .filter(IssueUpdateRow.issue_id == issue.id)
            .order_by(IssueUpdateRow.date.desc())
            .first()
        )
        assert latest is not None
        assert latest.diff == {"owner": {"from": "bob", "to": None}}

    @pytest.mark.parametrize(
        "field,initial,changed",
        [
            ("title", "t", "T2"),
            ("description", "d", "D2"),
            ("status_code", "open", "in_progress"),
            ("priority_code", "MED", "HIG"),
            ("issue_type_code", "AMB", "RSK"),
            ("impact", "", "broad"),
            ("risk", "", "high"),
            ("proposed_resolution", "", "talk to stakeholder"),
        ],
    )
    def test_audit_invariant_per_field(
        self,
        seeded_session: Session,
        field: str,
        initial: object,
        changed: object,
    ) -> None:
        """Every diffable field, when changed, produces one new audit row."""
        issue = create_issue(seeded_session, _create_payload(**{field: initial}))
        seeded_session.commit()
        before = _update_count(seeded_session, issue.id)

        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(
                author="alice",
                change_description=f"update {field}",
                **{field: changed},
            ),  # type: ignore[arg-type]
        )
        seeded_session.commit()

        assert _update_count(seeded_session, issue.id) == before + 1


class TestAddIssueUpdate:
    def test_appends_without_diff_and_bumps_date_updated(
        self, seeded_session: Session
    ) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        seeded_session.refresh(issue)
        before_updated_at = issue.date_updated
        before_count = _update_count(seeded_session, issue.id)

        row = add_issue_update(
            seeded_session,
            issue.id,
            IssueUpdateAdd(
                update_type_code="email_sent",
                description="Asked stakeholder for clarification.",
                author="alice",
                action_taken="email",
                action_result="awaiting reply",
            ),
        )
        seeded_session.commit()
        seeded_session.refresh(issue)

        assert row.diff == {}
        assert row.update_type_code == "email_sent"
        assert _update_count(seeded_session, issue.id) == before_count + 1
        # The bump happens via service; both values are naive (SQLite strips TZ).
        assert issue.date_updated >= before_updated_at

    def test_unknown_id_raises(self, seeded_session: Session) -> None:
        with pytest.raises(IssueNotFoundError):
            add_issue_update(
                seeded_session,
                "missing",
                IssueUpdateAdd(
                    update_type_code="note",
                    description="x",
                    author="alice",
                ),
            )


class TestGetIssue:
    def test_returns_existing(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        assert get_issue(seeded_session, issue.id) is issue

    def test_returns_none_for_missing(self, seeded_session: Session) -> None:
        assert get_issue(seeded_session, "missing") is None


class TestSearchIssues:
    def test_token_and_match(self, seeded_session: Session) -> None:
        create_issue(seeded_session, _create_payload(title="Login flow ambiguous"))
        create_issue(seeded_session, _create_payload(title="Data export gap"))
        seeded_session.commit()

        hits = search_issues(seeded_session, IssueSearchQuery(query="login flow"))
        assert len(hits) == 1
        assert "login" in hits[0].title.lower()

    def test_filter_by_status(self, seeded_session: Session) -> None:
        a = create_issue(seeded_session, _create_payload(title="A"))
        create_issue(seeded_session, _create_payload(title="B"))
        seeded_session.commit()
        update_issue(
            seeded_session,
            a.id,
            IssueUpdate(
                author="alice",
                change_description="closed",
                status_code="closed",
            ),
        )
        seeded_session.commit()

        hits = search_issues(seeded_session, IssueSearchQuery(status_codes=["closed"]))
        assert {h.id for h in hits} == {a.id}

    def test_filter_by_owner(self, seeded_session: Session) -> None:
        a = create_issue(seeded_session, _create_payload(title="A", owner="bob"))
        create_issue(seeded_session, _create_payload(title="B"))
        seeded_session.commit()

        hits = search_issues(seeded_session, IssueSearchQuery(owner="bob"))
        assert {h.id for h in hits} == {a.id}

    def test_filter_by_type_and_priority(self, seeded_session: Session) -> None:
        a = create_issue(
            seeded_session,
            _create_payload(title="A", issue_type_code="BLK"),
        )
        seeded_session.commit()
        update_issue(
            seeded_session,
            a.id,
            IssueUpdate(
                author="alice",
                change_description="bump",
                priority_code="CRT",
            ),
        )
        create_issue(seeded_session, _create_payload(title="B"))
        seeded_session.commit()

        hits = search_issues(
            seeded_session,
            IssueSearchQuery(type_codes=["BLK"], priority_codes=["CRT"]),
        )
        assert {h.id for h in hits} == {a.id}

    def test_pagination(self, seeded_session: Session) -> None:
        for i in range(5):
            create_issue(seeded_session, _create_payload(title=f"Item {i}"))
        seeded_session.commit()
        page1 = search_issues(
            seeded_session, IssueSearchQuery(query="Item", limit=2, offset=0)
        )
        page2 = search_issues(
            seeded_session, IssueSearchQuery(query="Item", limit=2, offset=2)
        )
        assert len(page1) == 2
        assert len(page2) == 2
        assert {h.id for h in page1}.isdisjoint({h.id for h in page2})


class TestListIssueUpdates:
    def test_orders_oldest_first(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        update_issue(
            seeded_session,
            issue.id,
            IssueUpdate(
                author="alice",
                change_description="resolve",
                status_code="resolved",
            ),
        )
        seeded_session.commit()
        history = list_issue_updates(seeded_session, issue.id)
        assert len(history) == 2
        assert history[0].update_type_code == "created"
        assert history[1].update_type_code == "status_changed"

    def test_unknown_id_raises(self, seeded_session: Session) -> None:
        with pytest.raises(IssueNotFoundError):
            list_issue_updates(seeded_session, "missing")


class TestListOpenIssues:
    def test_excludes_terminal_statuses(self, seeded_session: Session) -> None:
        a = create_issue(seeded_session, _create_payload(title="Open"))
        b = create_issue(seeded_session, _create_payload(title="ToClose"))
        seeded_session.commit()
        update_issue(
            seeded_session,
            b.id,
            IssueUpdate(
                author="alice",
                change_description="close",
                status_code="closed",
            ),
        )
        seeded_session.commit()

        ids = {i.id for i in list_open_issues(seeded_session)}
        assert a.id in ids
        assert b.id not in ids


class TestListBlockingIssues:
    def test_returns_blk_non_terminal(self, seeded_session: Session) -> None:
        a = create_issue(
            seeded_session,
            _create_payload(title="A", issue_type_code="BLK"),
        )
        b = create_issue(
            seeded_session,
            _create_payload(title="B", issue_type_code="AMB"),
        )
        c = create_issue(
            seeded_session,
            _create_payload(title="C", issue_type_code="BLK"),
        )
        seeded_session.commit()
        update_issue(
            seeded_session,
            c.id,
            IssueUpdate(
                author="alice",
                change_description="close",
                status_code="closed",
            ),
        )
        seeded_session.commit()

        blocking = list_blocking_issues(seeded_session)
        ids = {i.id for i in blocking}
        assert a.id in ids
        assert b.id not in ids
        assert c.id not in ids

    def test_orders_by_severity_desc(self, seeded_session: Session) -> None:
        low = create_issue(
            seeded_session,
            _create_payload(title="LowBlock", issue_type_code="BLK"),
        )
        crit = create_issue(
            seeded_session,
            _create_payload(title="CritBlock", issue_type_code="BLK"),
        )
        seeded_session.commit()
        update_issue(
            seeded_session,
            crit.id,
            IssueUpdate(
                author="alice",
                change_description="bump",
                priority_code="CRT",
            ),
        )
        update_issue(
            seeded_session,
            low.id,
            IssueUpdate(
                author="alice",
                change_description="lower",
                priority_code="LOW",
            ),
        )
        seeded_session.commit()

        ordered = list_blocking_issues(seeded_session)
        assert ordered[0].id == crit.id


class TestLinkIssueToRequirement:
    def test_creates_link_and_audit_row(self, seeded_session: Session) -> None:
        req = _make_requirement(seeded_session)
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        before = _update_count(seeded_session, issue.id)

        link = link_issue_to_requirement(
            seeded_session,
            issue.id,
            RequirementIssueLinkCreate(
                requirement_id=req.id,
                link_type="blocks",
                rationale="blocks login flow",
                author="alice",
            ),
        )
        seeded_session.commit()

        assert link.requirement_id == req.id
        assert link.issue_id == issue.id
        assert link.link_type == "blocks"
        assert _update_count(seeded_session, issue.id) == before + 1

        latest = (
            seeded_session.query(IssueUpdateRow)
            .filter(IssueUpdateRow.issue_id == issue.id)
            .order_by(IssueUpdateRow.date.desc())
            .first()
        )
        assert latest is not None
        assert latest.update_type_code == "requirement_linked"

    def test_unknown_issue_raises(self, seeded_session: Session) -> None:
        req = _make_requirement(seeded_session)
        with pytest.raises(IssueNotFoundError):
            link_issue_to_requirement(
                seeded_session,
                "missing",
                RequirementIssueLinkCreate(requirement_id=req.id, author="alice"),
            )

    def test_unknown_requirement_raises(self, seeded_session: Session) -> None:
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        with pytest.raises(RequirementNotFoundError):
            link_issue_to_requirement(
                seeded_session,
                issue.id,
                RequirementIssueLinkCreate(
                    requirement_id="missing-req", author="alice"
                ),
            )

    def test_duplicate_raises(self, seeded_session: Session) -> None:
        req = _make_requirement(seeded_session)
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        link_issue_to_requirement(
            seeded_session,
            issue.id,
            RequirementIssueLinkCreate(requirement_id=req.id, author="alice"),
        )
        seeded_session.commit()
        with pytest.raises(RequirementIssueLinkAlreadyExistsError):
            link_issue_to_requirement(
                seeded_session,
                issue.id,
                RequirementIssueLinkCreate(requirement_id=req.id, author="alice"),
            )


class TestUnlinkIssueFromRequirement:
    def test_unlinks_and_audits(self, seeded_session: Session) -> None:
        req = _make_requirement(seeded_session)
        issue = create_issue(seeded_session, _create_payload())
        seeded_session.commit()
        link_issue_to_requirement(
            seeded_session,
            issue.id,
            RequirementIssueLinkCreate(requirement_id=req.id, author="alice"),
        )
        seeded_session.commit()
        before = _update_count(seeded_session, issue.id)

        unlink_issue_from_requirement(
            seeded_session,
            issue.id,
            req.id,
            author="alice",
            rationale="resolved separately",
        )
        seeded_session.commit()

        assert seeded_session.get(RequirementIssueLink, (req.id, issue.id)) is None
        assert _update_count(seeded_session, issue.id) == before + 1
        latest = (
            seeded_session.query(IssueUpdateRow)
            .filter(IssueUpdateRow.issue_id == issue.id)
            .order_by(IssueUpdateRow.date.desc())
            .first()
        )
        assert latest is not None
        assert latest.update_type_code == "requirement_unlinked"

    def test_missing_link_raises(self, seeded_session: Session) -> None:
        with pytest.raises(RequirementIssueLinkNotFoundError):
            unlink_issue_from_requirement(seeded_session, "i", "r", author="alice")


class TestListMetadata:
    def test_statuses_sorted(self, seeded_session: Session) -> None:
        rows = list_issue_statuses(seeded_session)
        sort_orders = [r.sort_order for r in rows]
        assert sort_orders == sorted(sort_orders)
        assert {r.code for r in rows} >= {"open", "closed", "cancelled"}

    def test_types_sorted(self, seeded_session: Session) -> None:
        rows = list_issue_types(seeded_session)
        sort_orders = [r.sort_order for r in rows]
        assert sort_orders == sorted(sort_orders)
        assert {r.code for r in rows} >= {"AMB", "BLK", "MSC"}

    def test_priorities_sorted(self, seeded_session: Session) -> None:
        rows = list_issue_priorities(seeded_session)
        sort_orders = [r.sort_order for r in rows]
        assert sort_orders == sorted(sort_orders)
        assert {r.code for r in rows} == {"LOW", "MED", "HIG", "CRT"}


# Issue, Requirement and IssueUpdateRow re-exported from models for clarity in
# this test file even when not directly referenced (assertions read by id).
_ = Issue
_ = Requirement
