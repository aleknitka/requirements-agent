"""Compute structured diffs between a requirement's old and new state.

The output shape is ``{field_name: {"from": old_value, "to": new_value}}``
for every field in :data:`DIFFABLE_FIELDS` whose value actually changed.
Fields outside :data:`DIFFABLE_FIELDS` are ignored even if present in
the supplied update mapping, so caller-supplied bookkeeping fields
(``author``, ``change_description``) cannot pollute the diff.
"""

from __future__ import annotations

from typing import Any

from requirements_mcp.models import Requirement

__all__ = [
    "DIFFABLE_FIELDS",
    "JSON_LIST_FIELDS",
    "SCALAR_FIELDS",
    "compute_diff",
]


SCALAR_FIELDS: tuple[str, ...] = (
    "title",
    "requirement_statement",
    "type_code",
    "status_code",
    "extended_description",
)
"""Scalar requirement fields that participate in the diff."""

JSON_LIST_FIELDS: tuple[str, ...] = (
    "users",
    "triggers",
    "preconditions",
    "postconditions",
    "inputs",
    "outputs",
    "business_logic",
    "exception_handling",
    "acceptance_criteria",
)
"""List-shaped requirement fields that participate in the diff."""

DIFFABLE_FIELDS: tuple[str, ...] = SCALAR_FIELDS + JSON_LIST_FIELDS
"""All requirement fields tracked in the audit-log diff."""


def compute_diff(
    old: Requirement,
    updates: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return a structured diff for a single requirement update.

    For each field in :data:`DIFFABLE_FIELDS` that appears in
    ``updates`` and whose new value differs from the value currently on
    ``old``, the result contains an entry of the form
    ``{"from": old_value, "to": new_value}``. Fields whose new value
    equals the old value are omitted entirely so the diff captures only
    real changes; this also makes "did anything change?" a simple
    ``len(diff) > 0`` check.

    List values are compared by Python equality (``==``), which means
    elementwise across both lists. The function does not mutate either
    argument and is safe to call inside a transaction before issuing
    the actual update.

    Args:
        old: The requirement row in its pre-update state.
        updates: Mapping of field-name → new-value. May contain extra
            keys (for example ``author`` or ``change_description``);
            those are ignored. Only keys in :data:`DIFFABLE_FIELDS` are
            considered.

    Returns:
        A new dict with one entry per actually-changed field. Empty
        when ``updates`` represents a no-op.
    """
    diff: dict[str, dict[str, Any]] = {}
    for field in DIFFABLE_FIELDS:
        if field not in updates:
            continue
        new_value = updates[field]
        old_value = getattr(old, field)
        if old_value != new_value:
            diff[field] = {"from": old_value, "to": new_value}
    return diff
