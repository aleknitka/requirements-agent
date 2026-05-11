"""Tests for ``skills/status-report/scripts/mcp_report_to_pdf``.

Two layers of coverage:

* ``mcp_report_to_doc`` is pure data adaptation, tested directly with a
  small fixture payload.
* ``render`` end-to-end: build a ``get_full_report`` against the live
  ``apply_demo_data`` content and assert the produced PDF is a
  non-empty file beginning with ``%PDF``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPT_DIR = Path(__file__).resolve().parents[1] / "status-report" / "scripts"
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


def test_render_handles_xml_unsafe_characters(tmp_path: Path) -> None:
    """Project/title text containing &, <, > must not crash Paragraph."""
    payload = {
        "generated_at": "2026-05-11T12:00:00+00:00",
        "project_name": "A & B <Co>",
        "summary": {
            "requirement_count": 1,
            "issue_count": 0,
            "attached_issue_count": 0,
            "unattached_issue_count": 0,
            "included_issues": True,
            "included_closed_requirements": True,
        },
        "requirements": [
            {
                **_SAMPLE_REPORT["requirements"][0],
                "title": "needs <fix> & care",
                "requirement_statement": "uses A & B <tag> properly",
                "issues": [],
            }
        ],
        "unattached_issues": [],
    }
    out = tmp_path / "escape.pdf"
    render(payload, out)
    assert out.read_bytes().startswith(b"%PDF")


def test_default_output_uses_utc_stamp() -> None:
    """The default filename stamp must be UTC, suffixed with 'Z'."""
    from mcp_report_to_pdf import _default_output

    name = _default_output({"project_name": "DEMO"}).name
    assert name.startswith("STATUS-demo-")
    assert name.endswith("Z.pdf"), name


def test_read_input_rejects_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """No --input + stdin is a TTY should fail loud, not hang."""
    from mcp_report_to_pdf import _read_input

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    with pytest.raises(SystemExit) as exc_info:
        _read_input(None)
    assert "stdin is a terminal" in str(exc_info.value)


def test_renderer_handles_empty_story(tmp_path: Path) -> None:
    """A doc with no title/metadata/sections must still produce a PDF."""
    from mcp_report_to_pdf import json_to_pdf

    out = tmp_path / "empty.pdf"
    json_to_pdf({}, out)
    assert out.read_bytes().startswith(b"%PDF")


# ---- Codex feedback -----------------------------------------------------


def test_format_datetime_converts_non_utc_offset_to_utc() -> None:
    """`+02:00` must be converted to UTC before the label is applied."""
    from mcp_report_to_pdf import _format_datetime

    assert _format_datetime("2026-05-11T12:00:00+02:00") == "2026-05-11 10:00 UTC"


def test_format_datetime_accepts_datetime_objects() -> None:
    """Pydantic Python-mode dumps deliver datetime objects, not strings."""
    from datetime import datetime, timezone

    from mcp_report_to_pdf import _format_datetime

    dt = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
    assert _format_datetime(dt) == "2026-05-11 12:00 UTC"


def test_mcp_report_to_doc_rejects_non_dict() -> None:
    """A non-dict payload must fail loud, not silently render an empty PDF."""
    with pytest.raises(ValueError):
        mcp_report_to_doc([])  # type: ignore[arg-type]


def test_mcp_report_to_doc_rejects_empty_dict() -> None:
    with pytest.raises(ValueError):
        mcp_report_to_doc({})


def test_mcp_report_to_doc_rejects_wrapped_envelope() -> None:
    """``{"data": {...}}`` is a common bystander shape — must fail."""
    with pytest.raises(ValueError):
        mcp_report_to_doc({"data": _SAMPLE_REPORT})


def test_default_output_sanitises_project_slug() -> None:
    """``project_name`` must not leak path separators into the filename."""
    from mcp_report_to_pdf import _default_output

    path = _default_output({"project_name": "../../etc/passwd"})
    # Whole name has no path separators left; parent is cwd.
    assert "/" not in path.name
    assert ".." not in path.name
    assert path.name.startswith("STATUS-")


def test_default_output_falls_back_when_slug_empty() -> None:
    from mcp_report_to_pdf import _default_output

    path = _default_output({"project_name": "///"})
    assert path.name.startswith("STATUS-report-")


def test_long_audit_text_is_truncated_in_table(tmp_path: Path) -> None:
    """Oversized audit descriptions must not blow up ReportLab Tables."""
    long_text = "x" * 5000
    payload = {
        **_SAMPLE_REPORT,
        "requirements": [
            {
                **_SAMPLE_REPORT["requirements"][0],
                "changes": [
                    {
                        "id": "REQ-UPDATE-x",
                        "requirement_id": "REQ-USR-aaaaaa",
                        "change_description": long_text,
                        "diff": {},
                        "author": "alice",
                        "date": "2026-05-01T10:00:00+00:00",
                    },
                ],
                "issues": [],
            },
        ],
        "unattached_issues": [],
    }
    out = tmp_path / "long.pdf"
    render(payload, out)
    assert out.read_bytes().startswith(b"%PDF")


def test_render_with_live_demo_data(tmp_path: Path) -> None:
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
        apply_demo_data(session)
        session.commit()
        report = build_full_report(session)

    payload = report.model_dump(mode="json")
    out = tmp_path / "demo.pdf"
    render(payload, out)
    assert out.read_bytes().startswith(b"%PDF")
