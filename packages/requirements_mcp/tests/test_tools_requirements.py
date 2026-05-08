"""Tests for the MCP tool wrappers in :mod:`requirements_mcp.tools.requirements`.

Each tool wraps a service call in its own session. Tests bypass the
stdio transport and call the tool functions directly with the seeded
``session_factory`` fixture from ``conftest``.
"""

from __future__ import annotations

import pytest

from requirements_mcp.schemas.requirements import (
    RequirementChangeOut,
    RequirementCreate,
    RequirementOut,
    RequirementSearchHit,
    RequirementSearchQuery,
    RequirementStatusOut,
    RequirementTypeOut,
    RequirementUpdate,
)
from requirements_mcp.services.requirements import RequirementNotFoundError
from requirements_mcp.tools import requirements as tools


def _payload(**overrides: object) -> RequirementCreate:
    base: dict[str, object] = dict(
        title="Tool round-trip",
        requirement_statement="x",
        type_code="FUN",
        author="alice",
    )
    base.update(overrides)
    return RequirementCreate(**base)


class TestCreateRequirement:
    def test_returns_pydantic_out(self, seeded_session_factory) -> None:
        out = tools.create_requirement(seeded_session_factory, _payload())
        assert isinstance(out, RequirementOut)
        assert out.version == 1

    def test_persists_across_sessions(self, seeded_session_factory) -> None:
        out = tools.create_requirement(seeded_session_factory, _payload())
        # Re-open a fresh session and confirm the row is there.
        with seeded_session_factory() as session:
            from requirements_mcp.models import Requirement

            assert session.get(Requirement, out.id) is not None


class TestUpdateRequirement:
    def test_increments_version_and_returns_out(self, seeded_session_factory) -> None:
        created = tools.create_requirement(seeded_session_factory, _payload())
        updated = tools.update_requirement(
            seeded_session_factory,
            created.id,
            RequirementUpdate(
                author="bob",
                change_description="approve",
                status_code="approved",
            ),
        )
        assert isinstance(updated, RequirementOut)
        assert updated.version == created.version + 1
        assert updated.status_code == "approved"

    def test_unknown_id_raises(self, seeded_session_factory) -> None:
        with pytest.raises(RequirementNotFoundError):
            tools.update_requirement(
                seeded_session_factory,
                "missing",
                RequirementUpdate(author="bob", change_description="x", title="x"),
            )


class TestGetRequirement:
    def test_returns_out_when_found(self, seeded_session_factory) -> None:
        created = tools.create_requirement(seeded_session_factory, _payload())
        out = tools.get_requirement(seeded_session_factory, created.id)
        assert isinstance(out, RequirementOut)
        assert out.id == created.id

    def test_returns_none_when_missing(self, seeded_session_factory) -> None:
        assert tools.get_requirement(seeded_session_factory, "missing") is None


class TestSearchRequirements:
    def test_returns_search_hits(self, seeded_session_factory) -> None:
        tools.create_requirement(seeded_session_factory, _payload(title="Login flow"))
        tools.create_requirement(seeded_session_factory, _payload(title="Pipeline"))
        hits = tools.search_requirements(
            seeded_session_factory, RequirementSearchQuery(query="login")
        )
        assert len(hits) == 1
        assert isinstance(hits[0], RequirementSearchHit)


class TestListRequirementChanges:
    def test_returns_ordered_history(self, seeded_session_factory) -> None:
        created = tools.create_requirement(seeded_session_factory, _payload())
        tools.update_requirement(
            seeded_session_factory,
            created.id,
            RequirementUpdate(
                author="bob", change_description="approve", status_code="approved"
            ),
        )

        history = tools.list_requirement_changes(seeded_session_factory, created.id)
        assert len(history) == 2
        assert all(isinstance(row, RequirementChangeOut) for row in history)
        assert history[0].change_description == "created"

    def test_unknown_id_raises(self, seeded_session_factory) -> None:
        with pytest.raises(RequirementNotFoundError):
            tools.list_requirement_changes(seeded_session_factory, "missing")


class TestListMetadata:
    def test_list_statuses(self, seeded_session_factory) -> None:
        rows = tools.list_requirement_statuses(seeded_session_factory)
        assert all(isinstance(r, RequirementStatusOut) for r in rows)
        assert {r.code for r in rows} >= {"draft", "approved"}

    def test_list_types(self, seeded_session_factory) -> None:
        rows = tools.list_requirement_types(seeded_session_factory)
        assert all(isinstance(r, RequirementTypeOut) for r in rows)
        assert {r.code for r in rows} >= {"FUN", "NFR"}
