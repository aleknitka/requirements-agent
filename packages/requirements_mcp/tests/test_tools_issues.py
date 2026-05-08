"""Tests for the MCP tool wrappers in :mod:`requirements_mcp.tools.issues`.

Each tool wraps a service call in its own session. Tests bypass the
Gradio transport and call the tool functions directly with the seeded
``session_factory`` fixture from ``conftest``.
"""

from __future__ import annotations

import pytest

from requirements_mcp.schemas.issues import (
    IssueCreate,
    IssueOut,
    IssuePriorityOut,
    IssueSearchHit,
    IssueSearchQuery,
    IssueStatusOut,
    IssueTypeOut,
    IssueUpdate,
    IssueUpdateAdd,
    IssueUpdateOut,
    RequirementIssueLinkCreate,
    RequirementIssueLinkOut,
)
from requirements_mcp.schemas.requirements import RequirementCreate
from requirements_mcp.services.issues import (
    IssueNotFoundError,
    RequirementIssueLinkAlreadyExistsError,
    RequirementIssueLinkNotFoundError,
)
from requirements_mcp.tools import issues as tools
from requirements_mcp.tools import requirements as req_tools


def _payload(**overrides: object) -> IssueCreate:
    base: dict[str, object] = dict(
        title="Tool round-trip",
        description="x",
        issue_type_code="AMB",
        created_by="agent",
    )
    base.update(overrides)
    return IssueCreate(**base)


class TestCreateIssue:
    def test_returns_pydantic_out(self, seeded_session_factory) -> None:
        out = tools.create_issue(seeded_session_factory, _payload())
        assert isinstance(out, IssueOut)
        assert out.status_code == "open"

    def test_persists_across_sessions(self, seeded_session_factory) -> None:
        out = tools.create_issue(seeded_session_factory, _payload())
        from requirements_mcp.models import Issue

        with seeded_session_factory() as session:
            assert session.get(Issue, out.id) is not None


class TestUpdateIssue:
    def test_returns_updated_out(self, seeded_session_factory) -> None:
        created = tools.create_issue(seeded_session_factory, _payload())
        updated = tools.update_issue(
            seeded_session_factory,
            created.id,
            IssueUpdate(
                author="alice",
                change_description="resolve",
                status_code="resolved",
            ),
        )
        assert isinstance(updated, IssueOut)
        assert updated.status_code == "resolved"

    def test_unknown_id_raises(self, seeded_session_factory) -> None:
        with pytest.raises(IssueNotFoundError):
            tools.update_issue(
                seeded_session_factory,
                "missing",
                IssueUpdate(author="alice", change_description="x", title="x"),
            )


class TestAddIssueUpdate:
    def test_returns_new_update_out(self, seeded_session_factory) -> None:
        created = tools.create_issue(seeded_session_factory, _payload())
        out = tools.add_issue_update(
            seeded_session_factory,
            created.id,
            IssueUpdateAdd(
                update_type_code="note",
                description="checked spec",
                author="alice",
            ),
        )
        assert isinstance(out, IssueUpdateOut)
        assert out.update_type_code == "note"

    def test_unknown_id_raises(self, seeded_session_factory) -> None:
        with pytest.raises(IssueNotFoundError):
            tools.add_issue_update(
                seeded_session_factory,
                "missing",
                IssueUpdateAdd(
                    update_type_code="note", description="x", author="alice"
                ),
            )


class TestGetIssue:
    def test_returns_out_when_found(self, seeded_session_factory) -> None:
        created = tools.create_issue(seeded_session_factory, _payload())
        out = tools.get_issue(seeded_session_factory, created.id)
        assert isinstance(out, IssueOut)
        assert out.id == created.id

    def test_returns_none_when_missing(self, seeded_session_factory) -> None:
        assert tools.get_issue(seeded_session_factory, "missing") is None


class TestSearchIssues:
    def test_returns_search_hits(self, seeded_session_factory) -> None:
        tools.create_issue(seeded_session_factory, _payload(title="Login"))
        tools.create_issue(seeded_session_factory, _payload(title="Pipeline"))
        hits = tools.search_issues(
            seeded_session_factory, IssueSearchQuery(query="login")
        )
        assert len(hits) == 1
        assert isinstance(hits[0], IssueSearchHit)


class TestListIssueUpdates:
    def test_returns_history(self, seeded_session_factory) -> None:
        created = tools.create_issue(seeded_session_factory, _payload())
        tools.update_issue(
            seeded_session_factory,
            created.id,
            IssueUpdate(
                author="alice",
                change_description="resolve",
                status_code="resolved",
            ),
        )
        history = tools.list_issue_updates(seeded_session_factory, created.id)
        assert len(history) == 2
        assert all(isinstance(row, IssueUpdateOut) for row in history)

    def test_unknown_id_raises(self, seeded_session_factory) -> None:
        with pytest.raises(IssueNotFoundError):
            tools.list_issue_updates(seeded_session_factory, "missing")


class TestListOpenAndBlocking:
    def test_list_open(self, seeded_session_factory) -> None:
        tools.create_issue(seeded_session_factory, _payload(title="A"))
        rows = tools.list_open_issues(seeded_session_factory)
        assert all(isinstance(r, IssueOut) for r in rows)
        assert len(rows) == 1

    def test_list_blocking(self, seeded_session_factory) -> None:
        tools.create_issue(
            seeded_session_factory,
            _payload(title="B", issue_type_code="BLK"),
        )
        rows = tools.list_blocking_issues(seeded_session_factory)
        assert all(isinstance(r, IssueOut) for r in rows)
        assert len(rows) == 1


class TestLinkUnlink:
    def _make_req(self, factory) -> str:
        out = req_tools.create_requirement(
            factory,
            RequirementCreate(
                title="Login",
                requirement_statement="Users can log in.",
                type_code="FUN",
                author="alice",
            ),
        )
        return out.id

    def test_link_and_unlink(self, seeded_session_factory) -> None:
        req_id = self._make_req(seeded_session_factory)
        issue = tools.create_issue(seeded_session_factory, _payload())
        link = tools.link_issue_to_requirement(
            seeded_session_factory,
            issue.id,
            RequirementIssueLinkCreate(
                requirement_id=req_id, link_type="blocks", author="alice"
            ),
        )
        assert isinstance(link, RequirementIssueLinkOut)
        assert link.link_type == "blocks"

        tools.unlink_issue_from_requirement(
            seeded_session_factory,
            issue.id,
            req_id,
            author="alice",
            rationale="resolved separately",
        )

    def test_duplicate_link_raises(self, seeded_session_factory) -> None:
        req_id = self._make_req(seeded_session_factory)
        issue = tools.create_issue(seeded_session_factory, _payload())
        tools.link_issue_to_requirement(
            seeded_session_factory,
            issue.id,
            RequirementIssueLinkCreate(requirement_id=req_id, author="alice"),
        )
        with pytest.raises(RequirementIssueLinkAlreadyExistsError):
            tools.link_issue_to_requirement(
                seeded_session_factory,
                issue.id,
                RequirementIssueLinkCreate(requirement_id=req_id, author="alice"),
            )

    def test_unlink_missing_raises(self, seeded_session_factory) -> None:
        with pytest.raises(RequirementIssueLinkNotFoundError):
            tools.unlink_issue_from_requirement(
                seeded_session_factory, "i", "r", author="alice"
            )


class TestListMetadata:
    def test_list_statuses(self, seeded_session_factory) -> None:
        rows = tools.list_issue_statuses(seeded_session_factory)
        assert all(isinstance(r, IssueStatusOut) for r in rows)
        assert {r.code for r in rows} >= {"open", "closed"}

    def test_list_types(self, seeded_session_factory) -> None:
        rows = tools.list_issue_types(seeded_session_factory)
        assert all(isinstance(r, IssueTypeOut) for r in rows)
        assert {r.code for r in rows} >= {"AMB", "BLK"}

    def test_list_priorities(self, seeded_session_factory) -> None:
        rows = tools.list_issue_priorities(seeded_session_factory)
        assert all(isinstance(r, IssuePriorityOut) for r in rows)
        assert {r.code for r in rows} == {"LOW", "MED", "HIG", "CRT"}
