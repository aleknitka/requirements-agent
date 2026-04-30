"""Pure (no-I/O) helpers for serialising values into and out of SQLite rows."""

from __future__ import annotations

import json
import sqlite3
import struct
from datetime import datetime, timezone
from typing import Any

from ..models import (
    Dependency,
    ExternalLink,
    ProjectMeta,
    RequirementPriority,
    RequirementRow,
    RequirementStatus,
    RequirementType,
    Stakeholder,
)


def vec_to_blob(vec: list[float]) -> bytes:
    """Pack a float vector into the little-endian f32 blob sqlite-vec expects."""
    return struct.pack(f"{len(vec)}f", *vec)


def blob_to_vec(blob: bytes) -> list[float]:
    """Inverse of :func:`vec_to_blob`."""
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def to_json(v: Any) -> str:
    """Serialise a value to a JSON string suitable for a TEXT column.

    Pydantic models are unwrapped via ``model_dump(mode="json")`` so dates,
    enums, and nested models all become JSON-friendly.
    """
    if isinstance(v, list):
        return json.dumps(
            [i.model_dump(mode="json") if hasattr(i, "model_dump") else i for i in v],
            default=str,
        )
    if hasattr(v, "model_dump"):
        return json.dumps(v.model_dump(mode="json"), default=str)
    return json.dumps(v, default=str)


def parse_dt(s: str | None) -> datetime | None:
    """Parse an ISO-8601 string back into ``datetime``; ``None`` passes through."""
    if not s:
        return None
    return datetime.fromisoformat(s)


def now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def row_to_requirement(row: sqlite3.Row) -> RequirementRow:
    """Materialise a ``requirements`` row (joined with embedding flag) into a model."""
    d = dict(row)
    return RequirementRow(
        id=d["id"],
        req_type=RequirementType(d["req_type"]),
        title=d["title"],
        description=d["description"],
        status=RequirementStatus(d["status"]),
        priority=RequirementPriority(d["priority"]),
        owner=d["owner"],
        stakeholders=[Stakeholder(**s) for s in json.loads(d["stakeholders"])],
        predecessors=[Dependency(**s) for s in json.loads(d["predecessors"])],
        dependencies=[Dependency(**s) for s in json.loads(d["dependencies"])],
        external_links=[ExternalLink(**s) for s in json.loads(d["external_links"])],
        tags=json.loads(d["tags"]),
        created_at=datetime.fromisoformat(d["created_at"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
        has_embedding=bool(d.get("has_embedding", False)),
    )


def row_to_project(row: sqlite3.Row) -> ProjectMeta:
    """Materialise a ``projects`` row into a :class:`ProjectMeta`."""
    d = dict(row)
    return ProjectMeta(
        project_id=d["project_id"],
        name=d["name"],
        code=d.get("code"),
        phase=d["phase"],
        objective=d["objective"],
        business_case=d["business_case"],
        success_criteria=json.loads(d["success_criteria"]),
        out_of_scope=json.loads(d["out_of_scope"]),
        project_owner=d.get("project_owner"),
        sponsor=d.get("sponsor"),
        stakeholders=[Stakeholder(**s) for s in json.loads(d["stakeholders"])],
        start_date=d.get("start_date"),
        target_date=d.get("target_date"),
        actual_end_date=d.get("actual_end_date"),
        external_links=[
            ExternalLink(**link) for link in json.loads(d["external_links"])
        ],
        status_summary=d["status_summary"],
        status_updated_at=parse_dt(d.get("status_updated_at")),
        created_at=datetime.fromisoformat(d["created_at"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
    )
