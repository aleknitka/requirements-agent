"""Small helpers shared across the UI tab builders.

These functions exist so each tab module stays focused on layout. They
do no I/O and have no Gradio dependency on the call site (so they're
safe to import from any builder).
"""

from __future__ import annotations

import json
from typing import Any

__all__ = [
    "format_diff",
    "lines_to_list",
    "list_to_lines",
    "rows_to_table",
    "safe_strip",
]


def lines_to_list(text: str | None) -> list[str]:
    """Split a multi-line text input into a list of non-empty trimmed lines.

    Used to translate :class:`gradio.Textbox` content into the
    list-of-strings shape expected by the requirement schemas.

    Args:
        text: Raw textarea content. ``None`` is treated as empty.

    Returns:
        A list of trimmed lines, with blank lines dropped.
    """
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def list_to_lines(values: list[str] | None) -> str:
    """Render a list of strings as a newline-joined textarea body.

    Args:
        values: A list to display, or ``None``.

    Returns:
        The values joined with ``"\\n"``; empty string when input is
        ``None`` or empty.
    """
    if not values:
        return ""
    return "\n".join(values)


def safe_strip(text: str | None) -> str:
    """Trim whitespace from ``text`` and tolerate ``None``.

    Args:
        text: The string to strip, possibly ``None``.

    Returns:
        The stripped text, or ``""`` if input was ``None`` or empty.
    """
    return (text or "").strip()


def format_diff(diff: dict[str, Any]) -> str:
    """Render a structured diff as a compact multi-line summary.

    The diff shape is the one produced by
    :func:`requirements_mcp.services.diff.compute_diff`:
    ``{field_name: {"from": old, "to": new}}``. Lists are rendered as
    JSON to keep the formatting unambiguous.

    Args:
        diff: The diff payload from a ``requirements_changes`` or
            ``issue_updates`` row.

    Returns:
        A multi-line string with one ``field: from -> to`` line per
        entry. Empty diffs render as ``"(no field changes)"``.
    """
    if not diff:
        return "(no field changes)"

    lines: list[str] = []
    for field, change in diff.items():
        old = change.get("from") if isinstance(change, dict) else None
        new = change.get("to") if isinstance(change, dict) else None
        old_repr = (
            json.dumps(old, ensure_ascii=False) if not isinstance(old, str) else old
        )
        new_repr = (
            json.dumps(new, ensure_ascii=False) if not isinstance(new, str) else new
        )
        lines.append(f"{field}: {old_repr} -> {new_repr}")
    return "\n".join(lines)


def rows_to_table(rows: list[Any], columns: list[str]) -> list[list[Any]]:
    """Project a list of Pydantic Out-models into a Gradio Dataframe payload.

    Args:
        rows: Pydantic models (or any object with attributes named in
            ``columns``). An empty list yields an empty table.
        columns: Field names to read in order. The result preserves
            this order column by column.

    Returns:
        A list of row-lists suitable for assignment to a
        :class:`gradio.Dataframe`'s ``value``.
    """
    return [[getattr(row, col, None) for col in columns] for row in rows]
