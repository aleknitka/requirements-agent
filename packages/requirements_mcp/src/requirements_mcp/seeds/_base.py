"""Common Pydantic base for every controlled-vocabulary seed row."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SeedBase(BaseModel):
    """Shared base class for all seed Pydantic models.

    Configured with ``frozen=True`` so seed instances are immutable
    after construction (the lists in ``REQUIREMENT_STATUSES`` and so on
    are effectively constants), and with ``extra="forbid"`` so a
    misspelled field name in a seed declaration raises a validation
    error at import time instead of silently producing a row with the
    field missing. Subclasses add the table-specific fields and any
    Pydantic ``Field`` validators (regex patterns, numeric bounds).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


__all__ = ["SeedBase"]
