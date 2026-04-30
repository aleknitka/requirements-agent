"""
project_session.py — single-project connection helper.

Every skill calls ``get_project_conn()`` at the start of its session.
The single project database is at ``CONSTANTS.DB_PATH``.

PROJECT.md is owned by the skill: write through ``project_md_cli`` (or call
``project_md.save`` / ``append_section`` directly).
"""

from __future__ import annotations

import sqlite3

from . import CONSTANTS as C
from ._cli_io import err as _err
from .db.connection import get_db


def get_project_conn() -> sqlite3.Connection:
    """Open the single project database. Exits with error if not initialised.

    Checks that ``DB_PATH`` exists before opening. If the project has not been
    set up yet (``uv run init-project setup`` not run), exits non-zero with a
    clear error message rather than creating an empty database.

    Returns:
        An open ``sqlite3.Connection`` to the project database.
        Caller owns the lifetime and must close it.
    """
    if not C.DB_PATH.exists():
        _err("No project found. Run 'uv run init-project setup' first.")
    return get_db(str(C.DB_PATH))
