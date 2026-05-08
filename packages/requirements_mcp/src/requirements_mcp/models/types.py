"""Reusable SQLAlchemy column types used across ORM models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class JSONList(TypeDecorator):
    """Column type that stores a Python list as a JSON document.

    Several requirement fields (``users``, ``triggers``, ``preconditions``,
    ``postconditions``, ``inputs``, ``outputs``, ``business_logic``,
    ``exception_handling``, ``acceptance_criteria``) are naturally
    list-shaped. Storing them as JSON keeps the early schema simple and
    portable across SQLite and PostgreSQL; if any of these fields later
    grows query requirements that JSON cannot serve efficiently, it can
    be normalised into its own table without altering the surrounding
    code.

    The type guarantees a list-shaped Python value on both sides of the
    boundary: a ``None`` going in is coerced to ``[]`` at write time,
    and a ``NULL`` coming out is presented to application code as ``[]``
    at read time. This means callers never need to write
    ``value or []`` defensive checks.
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        """Coerce ``None`` to an empty list before writing.

        Args:
            value: Python value being bound to a SQL parameter. Expected
                to be a list, but ``None`` is tolerated.
            dialect: The active SQLAlchemy dialect. Unused; included
                because ``TypeDecorator`` requires the signature.

        Returns:
            The original list, or an empty list when ``value`` is
            ``None``.
        """
        if value is None:
            return []
        return value

    def process_result_value(self, value: Any, dialect: Any) -> list[Any]:
        """Coerce ``NULL`` to an empty list when reading.

        Args:
            value: Raw value loaded from the database. Will be ``None``
                if the row stored ``NULL``, otherwise a list-shaped
                JSON-decoded value.
            dialect: The active SQLAlchemy dialect. Unused; included
                because ``TypeDecorator`` requires the signature.

        Returns:
            A new list. Application code can iterate over the result
            without first checking for ``None``.
        """
        if value is None:
            return []
        return list(value)


__all__ = ["JSONList"]
