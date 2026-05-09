"""Human-readable identifier generation for primary keys.

Every primary key in the system is a short, prefixed slug rather than an
opaque UUID, so that ids appearing in logs, the Gradio UI, and API
payloads are immediately recognisable. The shape is:

* ``REQ-<TYPE>-<6>`` for a :class:`Requirement` row, where ``<TYPE>`` is
  the three-letter requirement type code (``USR``, ``FUN``, ...).
* ``ISSUE-<TYPE>-<6>`` for an :class:`Issue` row, where ``<TYPE>`` is
  the three-letter issue type code (``BLK``, ``AMB``, ...).
* ``REQ-UPDATE-<6>`` for a :class:`RequirementChange` audit row.
* ``ISSUE-UPDATE-<6>`` for an :class:`IssueUpdate` audit row.

The trailing ``<6>`` is six characters drawn from a 62-symbol mixed-case
alphanumeric alphabet using :func:`secrets.choice`, giving roughly
56 billion combinations per (table, type) bucket — collisions inside one
database remain astronomically unlikely.
"""

from __future__ import annotations

import secrets
import string

_ID_ALPHABET = string.ascii_letters + string.digits
_ID_SUFFIX_LENGTH = 6


def _suffix() -> str:
    """Return a fresh random 6-character base62 suffix."""
    return "".join(secrets.choice(_ID_ALPHABET) for _ in range(_ID_SUFFIX_LENGTH))


def new_requirement_id(type_code: str) -> str:
    """Build a fresh id for a :class:`Requirement` row.

    Args:
        type_code: The requirement type code, e.g. ``"USR"`` or ``"FUN"``.

    Returns:
        A 14-character id of the form ``REQ-<TYPE>-<6>``.
    """
    return f"REQ-{type_code}-{_suffix()}"


def new_issue_id(type_code: str) -> str:
    """Build a fresh id for an :class:`Issue` row.

    Args:
        type_code: The issue type code, e.g. ``"BLK"`` or ``"AMB"``.

    Returns:
        A 16-character id of the form ``ISSUE-<TYPE>-<6>``.
    """
    return f"ISSUE-{type_code}-{_suffix()}"


def new_requirement_change_id() -> str:
    """Build a fresh id for a :class:`RequirementChange` audit row."""
    return f"REQ-UPDATE-{_suffix()}"


def new_issue_update_id() -> str:
    """Build a fresh id for an :class:`IssueUpdate` audit row."""
    return f"ISSUE-UPDATE-{_suffix()}"


__all__ = [
    "new_issue_id",
    "new_issue_update_id",
    "new_requirement_change_id",
    "new_requirement_id",
]
