"""Convert the ``get_full_report`` MCP JSON payload into a PDF report.

The MCP server's ``get_full_report`` tool returns a structured snapshot
of every requirement, audit row, attached issue, and unattached issue.
This script reads that JSON (from a file or stdin), maps it onto a
generic document shape (``title`` / ``metadata`` / ``sections`` with
``paragraph`` / ``bullets`` / ``table`` blocks), and renders the PDF
with ReportLab Platypus.

Usage::

    # From a file
    uv run python skills/status-report/scripts/mcp_report_to_pdf.py \\
        --input report.json --output STATUS.pdf

    # From stdin
    curl -s http://127.0.0.1:7860/gradio_api/.../get_full_report \\
        | uv run python skills/status-report/scripts/mcp_report_to_pdf.py \\
            --output STATUS.pdf

Default output path when ``--output`` is omitted is
``STATUS-<project>-<timestamp>.pdf`` in the current working directory.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

__all__ = [
    "json_to_pdf",
    "main",
    "mcp_report_to_doc",
    "render",
]


# ---- Generic ReportLab renderer ------------------------------------------


def json_to_pdf(data: dict[str, Any] | str, output_path: str | Path) -> Path:
    """Build a PDF from a generic document dict.

    Supported document shape::

        {
            "title": "Report title",
            "metadata": {"Author": "Jane Doe", "Date": "2026-05-09"},
            "sections": [
                {
                    "heading": "Introduction",
                    "content": [
                        {"type": "paragraph", "text": "Some text here."},
                        {"type": "bullets", "items": ["one", "two"]},
                        {
                            "type": "table",
                            "headers": ["Name", "Value"],
                            "rows": [["A", 10], ["B", 20]],
                        },
                    ],
                },
            ],
        }

    Args:
        data: Dict or JSON string describing the document.
        output_path: Where to save the generated PDF.

    Returns:
        :class:`pathlib.Path` to the generated PDF.
    """
    if isinstance(data, str):
        data = json.loads(data)

    output_path = Path(output_path)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading1"]
    body_style = styles["BodyText"]
    metadata_key_style = ParagraphStyle(
        "MetadataKey",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    story: list[Any] = []

    title = data.get("title")
    if title:
        story.append(Paragraph(str(title), title_style))
        story.append(Spacer(1, 0.5 * cm))

    metadata = data.get("metadata")
    if isinstance(metadata, dict) and metadata:
        metadata_rows = [
            [
                Paragraph(str(key), metadata_key_style),
                Paragraph(str(value), body_style),
            ]
            for key, value in metadata.items()
        ]
        metadata_table = Table(metadata_rows, colWidths=[4 * cm, 11 * cm])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(metadata_table)
        story.append(Spacer(1, 0.7 * cm))

    for section in data.get("sections", []) or []:
        heading = section.get("heading")
        if heading:
            story.append(Paragraph(str(heading), heading_style))
            story.append(Spacer(1, 0.25 * cm))

        for block in section.get("content", []) or []:
            block_type = block.get("type")

            if block_type == "paragraph":
                text = block.get("text", "")
                story.append(Paragraph(str(text), body_style))
                story.append(Spacer(1, 0.3 * cm))

            elif block_type == "bullets":
                bullet_items = [
                    ListItem(Paragraph(str(item), body_style))
                    for item in block.get("items", []) or []
                ]
                story.append(
                    ListFlowable(
                        bullet_items,
                        bulletType="bullet",
                        leftIndent=18,
                    )
                )
                story.append(Spacer(1, 0.3 * cm))

            elif block_type == "table":
                headers = block.get("headers", []) or []
                rows = block.get("rows", []) or []
                table_data: list[list[Any]] = []
                has_header = bool(headers)
                if has_header:
                    table_data.append(
                        [Paragraph(str(cell), body_style) for cell in headers]
                    )
                for row in rows:
                    table_data.append(
                        [Paragraph(str(cell), body_style) for cell in row]
                    )
                if not table_data:
                    continue
                col_count = len(table_data[0])
                # Explicit colWidths so Paragraph cells word-wrap rather
                # than collapse to the longest single word. ``repeatRows``
                # is conditional: setting it to 1 with no real header
                # would repeat the first data row on every page.
                table = Table(
                    table_data,
                    repeatRows=1 if has_header else 0,
                    colWidths=[doc.width / col_count] * col_count,
                )
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 0.4 * cm))

            else:
                # Fallback for unknown block kinds — keep going.
                story.append(Paragraph(str(block), body_style))
                story.append(Spacer(1, 0.3 * cm))

    if not story:
        # ReportLab raises ``LayoutError: Empty story`` otherwise; fall
        # back to a single placeholder paragraph so the PDF is still
        # well-formed.
        story.append(Paragraph("No content to display.", body_style))
    doc.build(story)
    return output_path


# ---- MCP-payload → document adapter -------------------------------------


def _e(value: Any) -> str:
    """Coerce ``value`` to a string and HTML-escape it for ReportLab ``Paragraph``.

    Paragraph parses an XML-like subset and crashes on unescaped ``<``,
    ``>``, or ``&`` in user-controlled text. Every dynamic value that
    ends up inside a markup string must go through this helper.
    """
    if value is None:
        return ""
    return html.escape(str(value), quote=False)


def _format_datetime(value: str | datetime | None) -> str:
    """Render an ISO-8601 timestamp or ``datetime`` as ``YYYY-MM-DD HH:MM UTC``.

    Accepts both string and ``datetime`` inputs so the adapter works
    against the wire-format JSON *and* the in-process Pydantic model
    (whose Python-mode ``model_dump()`` returns ``datetime`` objects).
    Timestamps carrying a non-UTC offset are converted to UTC before
    the label is applied — naive datetimes are *assumed* to be UTC.

    Args:
        value: ISO-8601 string, :class:`datetime.datetime`, or ``None``.

    Returns:
        A human-friendly string, or ``"—"`` when ``value`` is empty
        or unparseable.
    """
    if value is None or value == "":
        return "—"
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return str(value)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


_MAX_CELL_LENGTH = 500
"""Soft cap on text-cell length in audit/action tables.

ReportLab's ``Table`` does not split rows across pages, so an oversize
cell can trigger ``LayoutError`` on long change notes. Truncating with
an ellipsis keeps the report printable; full text is still on screen
in the UI and over the MCP endpoint.
"""


def _cell_text(value: Any, limit: int = _MAX_CELL_LENGTH) -> str:
    """Coerce ``value`` to a string, truncate beyond ``limit`` chars."""
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


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
        f"<b>{_e(req.get('id'))}</b> — "
        f"type <i>{_e(req.get('type_code'))}</i> · "
        f"status <i>{_e(req.get('status_code'))}</i> · "
        f"version {_e(req.get('version'))}"
    )
    blocks.append(_paragraph(header_line))

    statement = req.get("requirement_statement") or ""
    if statement:
        blocks.append(_paragraph(f"<b>Statement.</b> {_e(statement)}"))

    extended = req.get("extended_description") or ""
    if extended:
        blocks.append(_paragraph(f"<b>Extended.</b> {_e(extended)}"))

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
            blocks.append(_bullets(_e(v) for v in values))

    changes = req.get("changes", []) or []
    if changes:
        rows = [
            [
                _e(_format_datetime(c.get("date"))),
                _e(c.get("author") or ""),
                _e(_cell_text(c.get("change_description"))),
            ]
            for c in changes
        ]
        blocks.append(_paragraph("<b>Audit history</b>"))
        blocks.append(_table(["Date", "Author", "Change"], rows))

    issues = req.get("issues", []) or []
    if issues:
        rows = [
            [
                _e(issue.get("id") or ""),
                _e(issue.get("priority_code") or ""),
                _e(issue.get("status_code") or ""),
                _e(issue.get("link_type") or ""),
                _e(_cell_text(issue.get("title"))),
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
        f"<b>{_e(issue.get('id'))}</b> — "
        f"type <i>{_e(issue.get('issue_type_code'))}</i> · "
        f"status <i>{_e(issue.get('status_code'))}</i> · "
        f"priority <i>{_e(issue.get('priority_code'))}</i>"
    )
    if issue.get("title"):
        header_line += f"<br/><b>{_e(issue['title'])}</b>"
    blocks.append(_paragraph(header_line))

    description = issue.get("description") or ""
    if description:
        blocks.append(_paragraph(_e(description)))

    for label, key in (
        ("Impact", "impact"),
        ("Risk", "risk"),
        ("Proposed resolution", "proposed_resolution"),
    ):
        value = issue.get(key) or ""
        if value:
            blocks.append(_paragraph(f"<b>{label}.</b> {_e(value)}"))

    updates = issue.get("updates", []) or []
    if updates:
        rows = [
            [
                _e(_format_datetime(u.get("date"))),
                _e(u.get("update_type_code") or ""),
                _e(u.get("author") or ""),
                _e(_cell_text(u.get("description"))),
            ]
            for u in updates
        ]
        blocks.append(_paragraph("<b>Action log</b>"))
        blocks.append(_table(["Date", "Kind", "Author", "Note"], rows))
    return blocks


_REQUIRED_REPORT_KEYS: tuple[tuple[str, type], ...] = (
    ("project_name", str),
    ("generated_at", str),
    ("summary", dict),
    ("requirements", list),
    ("unattached_issues", list),
)


_REQUIRED_SUMMARY_KEYS: tuple[tuple[str, type], ...] = (
    ("requirement_count", int),
    ("issue_count", int),
    ("attached_issue_count", int),
    ("unattached_issue_count", int),
    ("included_issues", bool),
    ("included_closed_requirements", bool),
)


_REQUIREMENT_LIST_FIELDS: tuple[str, ...] = (
    "users",
    "triggers",
    "preconditions",
    "postconditions",
    "inputs",
    "outputs",
    "business_logic",
    "exception_handling",
    "acceptance_criteria",
    "changes",
    "issues",
)
"""Fields on a requirement entry that the adapter iterates over."""

_ISSUE_LIST_FIELDS: tuple[str, ...] = ("updates",)
"""Fields on an issue entry that the adapter iterates over."""


def _assert_dict_entries(items: list[Any], path: str) -> None:
    """Raise ``ValueError`` when any entry of ``items`` is not a dict.

    ``path`` is the dotted location for the error message
    (e.g. ``"requirements[3].changes"``).
    """
    bad = [
        (i, type(entry).__name__)
        for i, entry in enumerate(items)
        if not isinstance(entry, dict)
    ]
    if bad:
        details = ", ".join(f"index {i}: {kind}" for i, kind in bad)
        raise ValueError(
            f"{path} must contain JSON objects only (offending entries: {details})."
        )


def _assert_list(value: Any, path: str) -> None:
    """Raise ``ValueError`` when ``value`` is not a list."""
    if not isinstance(value, list):
        raise ValueError(f"{path} should be a list (got {type(value).__name__}).")


def _validate_report(report: Any) -> None:
    """Sanity-check that ``report`` looks like a ``get_full_report`` payload.

    Fails fast on the common foot-guns:

    * the payload is not a JSON object;
    * a wrapping envelope was forwarded (e.g. ``{"data": {...}}``);
    * the file was simply empty (``{}``);
    * a top-level field exists but carries the wrong *type* (e.g.
      ``summary: []`` or ``requirements: {}``);
    * the ``summary`` block is missing required count / flag fields,
      or carries them with the wrong type — without this check, a
      drifted upstream payload would silently render a plausible but
      incorrect report with default ``0`` counts and ``yes`` flags;
    * an entry in ``requirements`` or ``unattached_issues`` is not a
      JSON object — without this check, ``{"requirements": ["x"]}``
      would pass top-level validation and crash later inside the
      adapter on ``"x".get(...)``.

    Raises:
        ValueError: when the shape is obviously wrong. Callers convert
            this to a clean ``SystemExit`` at the CLI boundary.
    """
    if not isinstance(report, dict):
        raise ValueError(
            f"Expected the report to be a JSON object, got {type(report).__name__}."
        )
    missing = [k for k, _ in _REQUIRED_REPORT_KEYS if k not in report]
    if missing:
        raise ValueError(
            "Payload is missing required keys "
            f"({', '.join(missing)}). "
            "Did you pass a get_full_report response (and not a wrapping envelope)?"
        )
    type_mismatches = [
        f"{name} should be a {expected.__name__} (got {type(report[name]).__name__})"
        for name, expected in _REQUIRED_REPORT_KEYS
        if not isinstance(report[name], expected)
    ]
    if type_mismatches:
        raise ValueError(
            "Payload has top-level fields of the wrong type: "
            + "; ".join(type_mismatches)
        )

    # Summary fields are individually checked: a drifted upstream
    # payload that drops a count must fail fast instead of rendering
    # a confidently-wrong "0".
    summary = report["summary"]
    summary_missing = [k for k, _ in _REQUIRED_SUMMARY_KEYS if k not in summary]
    if summary_missing:
        raise ValueError(
            f"summary is missing required keys ({', '.join(summary_missing)})."
        )
    summary_mismatches = [
        f"summary.{name} should be a {expected.__name__} "
        f"(got {type(summary[name]).__name__})"
        for name, expected in _REQUIRED_SUMMARY_KEYS
        # ``bool`` is a subclass of ``int`` in Python; reject that here.
        if not isinstance(summary[name], expected)
        or (expected is int and isinstance(summary[name], bool))
    ]
    if summary_mismatches:
        raise ValueError(
            "summary has fields of the wrong type: " + "; ".join(summary_mismatches)
        )

    for list_field in ("requirements", "unattached_issues"):
        _assert_dict_entries(report[list_field], list_field)

    # Walk every requirement: structured-list fields must be lists,
    # and every change / linked-issue entry must be a dict so the
    # adapter's `c.get(...)` / `issue.get(...)` reads don't crash.
    for i, req in enumerate(report["requirements"]):
        for field in _REQUIREMENT_LIST_FIELDS:
            if field in req:
                _assert_list(req[field], f"requirements[{i}].{field}")
        for sub_field in ("changes", "issues"):
            if sub_field in req:
                _assert_dict_entries(req[sub_field], f"requirements[{i}].{sub_field}")
        # Nested issue.updates is iterated as part of attached-issue
        # rendering, so it gets the same treatment.
        for j, nested_issue in enumerate(req.get("issues", []) or []):
            for field in _ISSUE_LIST_FIELDS:
                if field in nested_issue:
                    _assert_list(
                        nested_issue[field],
                        f"requirements[{i}].issues[{j}].{field}",
                    )
                    _assert_dict_entries(
                        nested_issue[field],
                        f"requirements[{i}].issues[{j}].{field}",
                    )

    # Same walk for unattached issues.
    for i, issue in enumerate(report["unattached_issues"]):
        for field in _ISSUE_LIST_FIELDS:
            if field in issue:
                _assert_list(issue[field], f"unattached_issues[{i}].{field}")
                _assert_dict_entries(issue[field], f"unattached_issues[{i}].{field}")


def mcp_report_to_doc(report: dict[str, Any]) -> dict[str, Any]:
    """Adapt the MCP ``get_full_report`` payload to the renderer's shape.

    Output dict matches the structure consumed by :func:`json_to_pdf`:
    a top-level ``title``, ``metadata``, and ``sections`` array of
    ``{heading, content[]}`` where each ``content`` block is one of
    ``paragraph`` / ``bullets`` / ``table``.

    Args:
        report: Parsed JSON from the MCP tool. Validated against
            :data:`_REQUIRED_REPORT_KEYS` before adaptation.

    Returns:
        A document dict ready for :func:`json_to_pdf`.

    Raises:
        ValueError: When ``report`` does not look like a
            ``get_full_report`` payload — see :func:`_validate_report`.
    """
    _validate_report(report)
    project_name = report.get("project_name", "PROJECT")
    generated_at = _format_datetime(report.get("generated_at"))
    summary = report.get("summary", {})

    sections: list[dict[str, Any]] = [_summary_section(report)]

    requirements = report.get("requirements", []) or []
    for req in requirements:
        title = req.get("title") or req.get("id") or "Requirement"
        sections.append(
            {
                "heading": f"Requirement — {_e(title)}",
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
                    "heading": f"Issue — {_e(title)}",
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
        "title": f"{_e(project_name)} — Project Status Report",
        "metadata": {
            "Project": _e(project_name),
            "Generated at": _e(generated_at),
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
    return json_to_pdf(mcp_report_to_doc(report), output_path)


def _read_input(path: Path | None) -> dict[str, Any]:
    """Load the MCP report JSON from ``path`` or from stdin if ``None``.

    When ``path`` is ``None`` and stdin is a terminal, fail loudly with
    a usage hint instead of blocking on a read that will never come.
    """
    if path is None:
        if sys.stdin.isatty():
            raise SystemExit(
                "Error: no --input file and stdin is a terminal. "
                "Pass --input PATH or pipe JSON in."
            )
        raw = sys.stdin.read()
    else:
        raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        raise SystemExit("Error: empty MCP report payload on input.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Error: input is not valid JSON: {exc}") from exc


_SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_slug(value: str, fallback: str = "report") -> str:
    """Reduce ``value`` to a filename-safe slug.

    Drops path separators and any character outside ``[A-Za-z0-9._-]``
    so a malicious ``project_name`` (e.g. ``../etc/passwd``) cannot
    escape the current directory when used to compute the default
    output filename. Falls back to ``fallback`` if the result is empty.
    """
    cleaned = _SLUG_RE.sub("-", value).strip("-._").lower()
    return cleaned or fallback


def _default_output(report: dict[str, Any]) -> Path:
    """Pick a sensible default output path when ``--output`` is omitted.

    Uses a UTC timestamp so two operators running the script at the
    same time on different machines produce reproducible filenames.
    The project component is run through :func:`_safe_slug` so an
    attacker-controlled ``project_name`` cannot cause the script to
    write outside the current directory.
    """
    project = _safe_slug(str(report.get("project_name") or "report"))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
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
    # Validate before deriving the default output path: otherwise a
    # non-dict payload (e.g. ``[]`` from a bad pipe) would crash inside
    # ``_default_output`` with a confusing AttributeError instead of
    # the clean SystemExit we want.
    try:
        _validate_report(report)
    except ValueError as exc:
        raise SystemExit(f"Error: {exc}") from exc
    output_path = args.output or _default_output(report)
    try:
        pdf_path = render(report, output_path)
    except ValueError as exc:
        # Defensive: mcp_report_to_doc re-runs _validate_report, but
        # surface any later ValueError the same way.
        raise SystemExit(f"Error: {exc}") from exc
    print(f"Wrote {pdf_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover — invoked as a script
    raise SystemExit(main())
