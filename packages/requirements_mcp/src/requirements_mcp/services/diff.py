"""Compute structured diffs for audit-log entries.

The output shape is ``{field_name: {"from": old_value, "to": new_value}}``
for every field in the supplied ``diffable_fields`` whose value actually
changed. Fields outside that whitelist are ignored even if present in
the update mapping, so caller-supplied bookkeeping fields (``author``,
``change_description``) cannot pollute the diff.

The helper is intentionally generic: subsystems define their own
diffable-field tuples (``REQUIREMENT_DIFFABLE_FIELDS``,
``ISSUE_DIFFABLE_FIELDS``) and pass the appropriate one in. There is no
need for a per-subsystem diff helper.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "ISSUE_DIFFABLE_FIELDS",
    "REQUIREMENT_DIFFABLE_FIELDS",
    "REQUIREMENT_JSON_LIST_FIELDS",
    "REQUIREMENT_SCALAR_FIELDS",
    "compute_diff",
]


REQUIREMENT_SCALAR_FIELDS: tuple[str, ...] = (
    "title",
    "requirement_statement",
    "type_code",
    "status_code",
    "extended_description",
)
"""Scalar requirement fields that participate in the diff."""

REQUIREMENT_JSON_LIST_FIELDS: tuple[str, ...] = (
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

REQUIREMENT_DIFFABLE_FIELDS: tuple[str, ...] = (
    REQUIREMENT_SCALAR_FIELDS + REQUIREMENT_JSON_LIST_FIELDS
)
"""All requirement fields tracked in the audit-log diff."""


ISSUE_DIFFABLE_FIELDS: tuple[str, ...] = (
    "title",
    "description",
    "issue_type_code",
    "status_code",
    "priority_code",
    "impact",
    "risk",
    "proposed_resolution",
    "owner",
)
"""Issue fields tracked in the audit-log diff.

``date_closed`` is intentionally absent: it is a derived side-effect of
``status_code`` transitioning into or out of a terminal state, recorded
implicitly by the change to ``status_code``.
"""


def compute_diff(
    old: Any,
    updates: dict[str, Any],
    diffable_fields: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    """Return a structured diff for a single ORM-row update.

    For each field in ``diffable_fields`` that appears in ``updates`` and
    whose new value differs from the value currently on ``old``, the
    result contains an entry of the form
    ``{"from": old_value, "to": new_value}``. Fields whose new value
    equals the old value are omitted entirely so the diff captures only
    real changes; this also makes "did anything change?" a simple
    ``len(diff) > 0`` check.

    List values are compared by Python equality (``==``), which means
    elementwise across both lists. The function does not mutate either
    argument and is safe to call inside a transaction before issuing
    the actual update.

    Args:
        old: The ORM row in its pre-update state.
        updates: Mapping of field-name → new-value. May contain extra
            keys (for example ``author`` or ``change_description``);
            those are ignored. Only keys in ``diffable_fields`` are
            considered.
        diffable_fields: Whitelist of field names to consider. Pass
            :data:`REQUIREMENT_DIFFABLE_FIELDS` for ``Requirement``
            updates and :data:`ISSUE_DIFFABLE_FIELDS` for ``Issue``
            updates.

    Returns:
        A new dict with one entry per actually-changed field. Empty
        when ``updates`` represents a no-op.
    """
    diff: dict[str, dict[str, Any]] = {}
    for field in diffable_fields:
        if field not in updates:
            continue
        new_value = updates[field]
        old_value = getattr(old, field)
        if old_value != new_value:
            diff[field] = {"from": old_value, "to": new_value}
    return diff
