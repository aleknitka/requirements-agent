"""Convert the ``get_full_report`` MCP JSON payload into a PDF report.

The MCP server's ``get_full_report`` tool returns a structured snapshot
of every requirement, audit row, attached issue, and unattached issue.
This script reads that JSON (from a file or stdin), adapts it into the
generic document shape that
:func:`skills.status_report.scripts.json_to_pdf.json_to_pdf` understands
(``title`` / ``metadata`` / ``sections`` with ``paragraph`` / ``bullets``
/ ``table`` blocks), and writes the PDF to disk.

Usage::

    # From a file
    uv run python skills/status-report/scripts/mcp_report_to_pdf.py \\
        --input report.json --output STATUS.pdf

    # From stdin
    curl -s http://127.0.0.1:7860/gradio_api/.../get_full_report \\
        | uv run python skills/status-report/scripts/mcp_report_to_pdf.py \\
            --output STATUS.pdf
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

# The renderer lives next to this script. Use a path-based import so
# the script is runnable as a standalone CLI without making
# ``skills/status-report`` a Python package.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from json_to_pdf import json_to_pdf  # noqa: E402

__all__ = ["mcp_report_to_doc", "main", "render"]


# ---- Adapter --------------------------------------------------------------


def _format_datetime(value: str | None) -> str:
    """Render an ISO-8601 timestamp as ``YYYY-MM-DD HH:MM UTC``.

    Args:
        value: ISO-8601 string from the MCP payload, or ``None``.

    Returns:
        A human-friendly string, or ``"—"`` when ``value`` is empty
        or unparseable.
    """
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _bullets(items: Iterable[str]) -> dict[str, Any]:
    """Build a ``bullets`` block from an iterable of strings."""
    return {"type": "bullets", "items": [str(item) for item in items if item]}


def _paragraph(text: str) -> dict[str, Any]:
    """Build a ``paragraph`` block."""
    return {"type": "paragraph", "text": text}


def _table(headers: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    """Build a ``table`` block."""
    return {"type": "table", "headers": headers, "rows": rows}


def _summary_section(report: dict[str, Any]) -> dict[str, Any]:
    """Build the cover-page-equivalent Summary section."""
    summary = report.get("summary", {})
    rows = [
        ["Requirements", summary.get("requirement_count", 0)],
        ["Issues (total)", summary.get("issue_count", 0)],
        ["  attached", summary.get("attached_issue_count", 0)],
        ["  unattached", summary.get("unattached_issue_count", 0)],
        [
            "Filter — included_issues",
            "yes" if summary.get("included_issues", True) else "no",
        ],
        [
            "Filter — included_closed_requirements",
            "yes" if summary.get("included_closed_requirements", True) else "no",
        ],
    ]
    return {
        "heading": "Summary",
        "content": [_table(["Metric", "Value"], rows)],
    }


def _requirement_blocks(req: dict[str, Any]) -> list[dict[str, Any]]:
    """Render one requirement as a flat list of blocks (no nested sections)."""
    blocks: list[dict[str, Any]] = []

    header_line = (
        f"<b>{req.get('id', '')}</b> — "
        f"type <i>{req.get('type_code', '')}</i> · "
        f"status <i>{req.get('status_code', '')}</i> · "
        f"version {req.get('version', '')}"
    )
    blocks.append(_paragraph(header_line))

    statement = req.get("requirement_statement") or ""
    if statement:
        blocks.append(_paragraph(f"<b>Statement.</b> {statement}"))

    extended = req.get("extended_description") or ""
    if extended:
        blocks.append(_paragraph(f"<b>Extended.</b> {extended}"))

    structured_pairs: list[tuple[str, list[str]]] = [
        ("Users", req.get("users", [])),
        ("Triggers", req.get("triggers", [])),
        ("Preconditions", req.get("preconditions", [])),
        ("Postconditions", req.get("postconditions", [])),
        ("Inputs", req.get("inputs", [])),
        ("Outputs", req.get("outputs", [])),
        ("Business logic", req.get("business_logic", [])),
        ("Exception handling", req.get("exception_handling", [])),
        ("Acceptance criteria", req.get("acceptance_criteria", [])),
    ]
    for label, values in structured_pairs:
        if values:
            blocks.append(_paragraph(f"<b>{label}.</b>"))
            blocks.append(_bullets(values))

    changes = req.get("changes", []) or []
    if changes:
        rows = [
            [
                _format_datetime(c.get("date")),
                c.get("author", ""),
                c.get("change_description", ""),
            ]
            for c in changes
        ]
        blocks.append(_paragraph("<b>Audit history</b>"))
        blocks.append(_table(["Date", "Author", "Change"], rows))

    issues = req.get("issues", []) or []
    if issues:
        rows = [
            [
                issue.get("id", ""),
                issue.get("priority_code", ""),
                issue.get("status_code", ""),
                issue.get("link_type", "") or "",
                issue.get("title", ""),
            ]
            for issue in issues
        ]
        blocks.append(_paragraph("<b>Linked issues</b>"))
        blocks.append(_table(["Id", "Priority", "Status", "Link", "Title"], rows))
    return blocks


def _issue_blocks(issue: dict[str, Any]) -> list[dict[str, Any]]:
    """Render one unattached issue as a flat list of blocks."""
    blocks: list[dict[str, Any]] = []
    header_line = (
        f"<b>{issue.get('id', '')}</b> — "
        f"type <i>{issue.get('issue_type_code', '')}</i> · "
        f"status <i>{issue.get('status_code', '')}</i> · "
        f"priority <i>{issue.get('priority_code', '')}</i>"
    )
    if issue.get("title"):
        header_line += f"<br/><b>{issue['title']}</b>"
    blocks.append(_paragraph(header_line))

    description = issue.get("description") or ""
    if description:
        blocks.append(_paragraph(description))

    for label, key in (
        ("Impact", "impact"),
        ("Risk", "risk"),
        ("Proposed resolution", "proposed_resolution"),
    ):
        value = issue.get(key) or ""
        if value:
            blocks.append(_paragraph(f"<b>{label}.</b> {value}"))

    updates = issue.get("updates", []) or []
    if updates:
        rows = [
            [
                _format_datetime(u.get("date")),
                u.get("update_type_code", ""),
                u.get("author", ""),
                u.get("description", ""),
            ]
            for u in updates
        ]
        blocks.append(_paragraph("<b>Action log</b>"))
        blocks.append(_table(["Date", "Kind", "Author", "Note"], rows))
    return blocks


def mcp_report_to_doc(report: dict[str, Any]) -> dict[str, Any]:
    """Adapt the MCP ``get_full_report`` payload to the renderer's shape.

    Output dict matches the structure consumed by
    :func:`json_to_pdf.json_to_pdf`: a top-level ``title``,
    ``metadata``, and ``sections`` array of ``{heading, content[]}``
    where each ``content`` block is one of ``paragraph`` /
    ``bullets`` / ``table``.

    Args:
        report: Parsed JSON from the MCP tool.

    Returns:
        A document dict ready for :func:`json_to_pdf.json_to_pdf`.
    """
    project_name = report.get("project_name", "PROJECT")
    generated_at = _format_datetime(report.get("generated_at"))
    summary = report.get("summary", {})

    sections: list[dict[str, Any]] = [_summary_section(report)]

    requirements = report.get("requirements", []) or []
    for req in requirements:
        title = req.get("title") or req.get("id") or "Requirement"
        sections.append(
            {
                "heading": f"Requirement — {title}",
                "content": _requirement_blocks(req),
            }
        )
    if not requirements:
        sections.append(
            {
                "heading": "Requirements",
                "content": [_paragraph("No requirements in scope.")],
            }
        )

    unattached = report.get("unattached_issues", []) or []
    if unattached:
        first_issue, *rest = unattached
        sections.append(
            {
                "heading": "Unattached issues",
                "content": _issue_blocks(first_issue),
            }
        )
        for issue in rest:
            title = issue.get("title") or issue.get("id") or "Issue"
            sections.append(
                {
                    "heading": f"Issue — {title}",
                    "content": _issue_blocks(issue),
                }
            )
    else:
        sections.append(
            {
                "heading": "Unattached issues",
                "content": [_paragraph("None.")],
            }
        )

    return {
        "title": f"{project_name} — Project Status Report",
        "metadata": {
            "Project": project_name,
            "Generated at": generated_at,
            "Requirements": summary.get("requirement_count", 0),
            "Issues (total)": summary.get("issue_count", 0),
            "Attached": summary.get("attached_issue_count", 0),
            "Unattached": summary.get("unattached_issue_count", 0),
        },
        "sections": sections,
    }


# ---- CLI -------------------------------------------------------------------


def render(report: dict[str, Any], output_path: str | Path) -> Path:
    """Adapt the MCP payload and render the PDF in one call.

    Args:
        report: Parsed MCP ``get_full_report`` JSON.
        output_path: Destination path for the PDF.

    Returns:
        The :class:`pathlib.Path` of the generated PDF.
    """
    doc = mcp_report_to_doc(report)
    return json_to_pdf(doc, output_path)


def _read_input(path: Path | None) -> dict[str, Any]:
    """Load the MCP report JSON from ``path`` or from stdin if ``None``."""
    if path is None:
        raw = sys.stdin.read()
    else:
        raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        raise SystemExit("Error: empty MCP report payload on input.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Error: input is not valid JSON: {exc}") from exc


def _default_output(report: dict[str, Any]) -> Path:
    """Pick a sensible default output path when ``--output`` is omitted."""
    project = str(report.get("project_name") or "report").lower()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(f"STATUS-{project}-{stamp}.pdf")


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns ``0`` on success."""
    parser = argparse.ArgumentParser(
        prog="mcp_report_to_pdf",
        description=(
            "Convert the get_full_report MCP JSON payload into a PDF. "
            "Reads from --input or stdin; writes to --output (default: "
            "STATUS-<project>-<timestamp>.pdf in the current directory)."
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to the MCP report JSON file. Omit to read from stdin.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path for the generated PDF.",
    )
    args = parser.parse_args(argv)

    report = _read_input(args.input)
    output_path = args.output or _default_output(report)
    pdf_path = render(report, output_path)
    print(f"Wrote {pdf_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover — invoked as a script
    raise SystemExit(main())
