"""Tests for ``mcp_report_to_pdf``.

Two layers of coverage:

* ``mcp_report_to_doc`` is pure data adaptation, tested directly with a
  small fixture payload.
* ``render`` end-to-end check: builds a ``get_full_report`` against the
  live ``apply_demo_data`` content and asserts the produced PDF is a
  non-empty file beginning with ``%PDF``.

The end-to-end test imports from :mod:`requirements_mcp` which is on
the workspace's import path during ``uv run pytest``. Skipped
otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from mcp_report_to_pdf import mcp_report_to_doc, render  # noqa: E402


_SAMPLE_REPORT: dict = {
    "generated_at": "2026-05-11T12:00:00+00:00",
    "project_name": "DEMO",
    "summary": {
        "requirement_count": 1,
        "issue_count": 2,
        "attached_issue_count": 1,
        "unattached_issue_count": 1,
        "included_issues": True,
        "included_closed_requirements": True,
    },
    "requirements": [
        {
            "id": "REQ-USR-aaaaaa",
            "title": "Login",
            "requirement_statement": "Users can log in.",
            "type_code": "USR",
            "status_code": "draft",
            "version": 1,
            "author": "alice",
            "date_created": "2026-05-01T10:00:00+00:00",
            "date_updated": "2026-05-02T10:00:00+00:00",
            "extended_description": "",
            "users": ["end_user"],
            "triggers": [],
            "preconditions": [],
            "postconditions": [],
            "inputs": ["email", "password"],
            "outputs": [],
            "business_logic": [],
            "exception_handling": [],
            "acceptance_criteria": ["valid login succeeds"],
            "changes": [
                {
                    "id": "REQ-UPDATE-x",
                    "requirement_id": "REQ-USR-aaaaaa",
                    "change_description": "created",
                    "diff": {},
                    "author": "alice",
                    "date": "2026-05-01T10:00:00+00:00",
                },
            ],
            "issues": [
                {
                    "id": "ISSUE-AMB-aaaaaa",
                    "title": "scope unclear",
                    "description": "scope of SSO?",
                    "issue_type_code": "AMB",
                    "status_code": "open",
                    "priority_code": "MED",
                    "impact": "",
                    "risk": "",
                    "proposed_resolution": "",
                    "owner": None,
                    "created_by": "agent",
                    "date_created": "2026-05-01T10:00:00+00:00",
                    "date_updated": "2026-05-01T10:00:00+00:00",
                    "date_closed": None,
                    "link_type": "clarifies",
                    "rationale": "needs detail",
                    "updates": [],
                },
            ],
        },
    ],
    "unattached_issues": [
        {
            "id": "ISSUE-QST-orphan",
            "title": "estimate format?",
            "description": "Story points or hours?",
            "issue_type_code": "QST",
            "status_code": "open",
            "priority_code": "LOW",
            "impact": "",
            "risk": "",
            "proposed_resolution": "",
            "owner": None,
            "created_by": "agent",
            "date_created": "2026-05-03T10:00:00+00:00",
            "date_updated": "2026-05-03T10:00:00+00:00",
            "date_closed": None,
            "link_type": None,
            "rationale": None,
            "updates": [],
        },
    ],
}


# ---- adapter ------------------------------------------------------------


def test_mcp_report_to_doc_title_and_metadata() -> None:
    doc = mcp_report_to_doc(_SAMPLE_REPORT)
    assert doc["title"] == "DEMO — Project Status Report"
    metadata = doc["metadata"]
    assert metadata["Project"] == "DEMO"
    assert metadata["Requirements"] == 1
    assert metadata["Issues (total)"] == 2


def test_mcp_report_to_doc_has_summary_and_requirement_sections() -> None:
    doc = mcp_report_to_doc(_SAMPLE_REPORT)
    headings = [s["heading"] for s in doc["sections"]]
    assert headings[0] == "Summary"
    assert "Requirement — Login" in headings
    # First unattached issue uses the umbrella heading; further issues
    # get an "Issue — <title>" heading.
    assert "Unattached issues" in headings


def test_mcp_report_to_doc_nested_issues_render_as_table() -> None:
    doc = mcp_report_to_doc(_SAMPLE_REPORT)
    req_section = next(
        s for s in doc["sections"] if s["heading"] == "Requirement — Login"
    )
    tables = [b for b in req_section["content"] if b.get("type") == "table"]
    assert any(
        t["headers"] == ["Id", "Priority", "Status", "Link", "Title"] for t in tables
    )


def test_mcp_report_to_doc_empty_requirements_section() -> None:
    doc = mcp_report_to_doc(
        {**_SAMPLE_REPORT, "requirements": [], "unattached_issues": []}
    )
    headings = [s["heading"] for s in doc["sections"]]
    assert "Requirements" in headings
    assert "Unattached issues" in headings


# ---- end-to-end ---------------------------------------------------------


def test_render_writes_pdf(tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    render(_SAMPLE_REPORT, out)
    assert out.exists()
    data = out.read_bytes()
    assert data.startswith(b"%PDF"), "output should be a PDF"
    assert len(data) > 1000


@pytest.mark.parametrize("with_demo", [True])
def test_render_with_live_demo_data(tmp_path: Path, with_demo: bool) -> None:
    """Render demo data through the live service to catch shape drift."""
    pytest.importorskip("sqlalchemy")
    pytest.importorskip("requirements_mcp")

    from requirements_mcp.db.engine import make_engine, make_session_factory
    from requirements_mcp.db.init import init_db
    from requirements_mcp.seeds.demo import apply_demo_data
    from requirements_mcp.services.reports import build_full_report

    db_path = tmp_path / "data" / "requirements.db"
    resolved, _ = init_db(db_path=db_path)
    engine = make_engine(resolved)
    factory = make_session_factory(engine)
    with factory() as session:
        if with_demo:
            apply_demo_data(session)
            session.commit()
        report = build_full_report(session)

    payload = report.model_dump(mode="json")
    out = tmp_path / "demo.pdf"
    render(payload, out)
    assert out.read_bytes().startswith(b"%PDF")
