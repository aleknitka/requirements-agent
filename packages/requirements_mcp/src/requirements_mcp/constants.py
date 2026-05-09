"""Module-level constants exposed to the rest of the package.

The single non-trivial value here is :data:`PROJECT_NAME`, the short
identifier that brands the running app. The window title shown in the
browser is :data:`APP_TITLE` (``"<PROJECT_NAME> - requirements db"``)
so an operator running several instances against different databases
can tell them apart at a glance.

``PROJECT_NAME`` is sourced in priority order from:

1. The ``REQUIREMENTS_PROJECT_NAME`` environment variable.
2. The :data:`_DEFAULT_PROJECT_NAME` constant below.

Whichever wins must satisfy :data:`PROJECT_NAME_PATTERN`
(``^[A-Za-z0-9_-]{3,15}$``); otherwise a :class:`ValueError` is raised
at import time so the misconfiguration is surfaced immediately.
"""

from __future__ import annotations

import os
import re

__all__ = [
    "APP_NAME",
    "APP_TITLE",
    "PROJECT_NAME",
    "PROJECT_NAME_PATTERN",
]

PROJECT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9_-]{3,15}$")
"""Validation regex for ``PROJECT_NAME``: 3-15 chars from ``[A-Za-z0-9_-]``."""

_DEFAULT_PROJECT_NAME = "PROJECT"
_ENV_VAR = "REQUIREMENTS_PROJECT_NAME"


def _resolve_project_name() -> str:
    """Pick the project name from env var or the built-in default and validate it.

    Returns:
        The resolved project name.

    Raises:
        ValueError: If the chosen value does not match
            :data:`PROJECT_NAME_PATTERN`.
    """
    raw = os.environ.get(_ENV_VAR, _DEFAULT_PROJECT_NAME)
    if not PROJECT_NAME_PATTERN.match(raw):
        raise ValueError(
            f"Invalid project name {raw!r}: must match {PROJECT_NAME_PATTERN.pattern} "
            f"(3-15 chars, letters / digits / underscore / hyphen). "
            f"Set the {_ENV_VAR} environment variable or edit "
            f"requirements_mcp/constants.py."
        )
    return raw


PROJECT_NAME: str = _resolve_project_name()
"""Short identifier branding the running instance."""

APP_NAME: str = "requirements db"
"""Application name component appended after the project name in the title."""

APP_TITLE: str = f"{PROJECT_NAME} - {APP_NAME}"
"""The browser window title and the in-page header."""
