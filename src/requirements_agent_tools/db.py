"""
db.py — SQLite persistence layer with sqlite-vec for embeddings.

Public API (used by CLI scripts)
─────────────────────────────────
  get_db(path)              → open/create DB, return connection
  bootstrap(conn)           → create tables + vec virtual table if absent
  embed(text)               → call configured embedding API, return list[float]

  # Projects
  upsert_project(conn, meta)
  get_project(conn, project_id)      → ProjectMeta | None
  get_project_by_slug(conn, slug)    → ProjectMeta | None
  list_projects(conn)                → list[ProjectMeta]

  # Requirements
  insert_requirement(conn, project_id, req_in, created_by) → RequirementRow
  update_requirement(conn, req_id, project_id, changes, changed_by, summary)
                                                           → RequirementRow
  get_requirement(conn, req_id)  → RequirementRow | None
  search_requirements(conn, project_id, **filters)        → list[RequirementRow]
  vector_search(conn, project_id, query_text, top_k)      → list[tuple[RequirementRow, float]]

  # Minutes
  insert_minute(conn, project_id, minute_in)  → MinuteRow
  get_minute(conn, minute_id)                 → MinuteRow | None
  list_minutes(conn, project_id, **filters)   → list[MinuteRow]
  mark_integrated(conn, minute_id)            → MinuteRow
  list_decisions(conn, project_id, **filters) → list[dict]

  # Updates
  get_updates(conn, req_id)  → list[UpdateRecord]
"""

from __future__ import annotations

import json
import sqlite3
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── Locate the scripts directory for local imports ────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
import CONSTANTS as C
from models import (
    ActionItem, Decision, DecisionStatus, Dependency, ExternalLink,
    FieldDiff, MinuteIn, MinuteRow, ProjectMeta, RequirementIn,
    RequirementPriority, RequirementRow, RequirementStatus, RequirementType,
    Stakeholder, UpdateRecord,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Embedding
# ═══════════════════════════════════════════════════════════════════════════════

def embed(text: str) -> list[float]:
    """
    Call the configured OpenAI-compatible embedding endpoint.
    Returns a list[float] of length EMBEDDING_DIM.
    Raises RuntimeError if the API key is missing or the call fails.
    """
    if not C.EMBEDDING_API_KEY:
        raise RuntimeError(
            "EMBEDDING_API_KEY is not set. "
            "Export OPENAI_API_KEY (or the relevant env var) before running."
        )
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")

    client = OpenAI(api_key=C.EMBEDDING_API_KEY, base_url=C.EMBEDDING_API_BASE)
    response = client.embeddings.create(model=C.EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def _vec_to_blob(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)

def _blob_to_vec(blob: bytes) -> list[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


# ═══════════════════════════════════════════════════════════════════════════════
# Connection & bootstrap
# ═══════════════════════════════════════════════════════════════════════════════

def get_db(path: str) -> sqlite3.Connection:
    """Open (and create if needed) the SQLite DB; load sqlite-vec extension."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Load sqlite-vec
    try:
        import sqlite_vec
        sqlite_vec.load(conn)
    except Exception as e:
        raise RuntimeError(
            f"Could not load sqlite-vec extension: {e}\n"
        )

    bootstrap(conn)
    return conn


def bootstrap(conn: sqlite3.Connection) -> None:
    """Create all tables and virtual tables if they don't already exist."""
    conn.executescript(f"""
    -- ── Projects ──────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS projects (
        project_id        TEXT PRIMARY KEY,
        slug              TEXT NOT NULL DEFAULT '',
        name              TEXT NOT NULL,
        code              TEXT,
        phase             TEXT NOT NULL DEFAULT 'discovery',
        objective         TEXT NOT NULL DEFAULT '',
        business_case     TEXT NOT NULL DEFAULT '',
        success_criteria  TEXT NOT NULL DEFAULT '[]',
        out_of_scope      TEXT NOT NULL DEFAULT '[]',
        project_owner     TEXT,
        sponsor           TEXT,
        stakeholders      TEXT NOT NULL DEFAULT '[]',
        start_date        TEXT,
        target_date       TEXT,
        actual_end_date   TEXT,
        external_links    TEXT NOT NULL DEFAULT '[]',
        status_summary    TEXT NOT NULL DEFAULT '',
        status_updated_at TEXT,
        created_at        TEXT NOT NULL,
        updated_at        TEXT NOT NULL
    );

    -- ── Requirements ──────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS requirements (
        id             TEXT PRIMARY KEY,
        project_id     TEXT NOT NULL REFERENCES projects(project_id),
        req_type       TEXT NOT NULL DEFAULT 'CORE',
        title          TEXT NOT NULL,
        description    TEXT NOT NULL DEFAULT '',
        status         TEXT NOT NULL DEFAULT 'open',
        priority       TEXT NOT NULL DEFAULT 'medium',
        owner          TEXT,
        stakeholders   TEXT NOT NULL DEFAULT '[]',
        predecessors   TEXT NOT NULL DEFAULT '[]',
        dependencies   TEXT NOT NULL DEFAULT '[]',
        external_links TEXT NOT NULL DEFAULT '[]',
        tags           TEXT NOT NULL DEFAULT '[]',
        created_at     TEXT NOT NULL,
        updated_at     TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_req_project  ON requirements(project_id);
    CREATE INDEX IF NOT EXISTS idx_req_status   ON requirements(status);
    CREATE INDEX IF NOT EXISTS idx_req_type     ON requirements(req_type);
    CREATE INDEX IF NOT EXISTS idx_req_priority ON requirements(priority);

    -- ── Vec virtual table for requirement embeddings ───────────────────────
    CREATE VIRTUAL TABLE IF NOT EXISTS req_embeddings
    USING vec0(
        requirement_id TEXT PRIMARY KEY,
        embedding      FLOAT[{C.EMBEDDING_DIM}]
    );

    -- ── Updates (change log) ──────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS updates (
        id             TEXT PRIMARY KEY,
        requirement_id TEXT NOT NULL REFERENCES requirements(id),
        changed_at     TEXT NOT NULL,
        changed_by     TEXT NOT NULL,
        summary        TEXT NOT NULL DEFAULT '',
        diffs          TEXT NOT NULL DEFAULT '[]',
        full_snapshot  TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_upd_req ON updates(requirement_id);

    -- ── Minutes ───────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS minutes (
        id                      TEXT PRIMARY KEY,
        project_id              TEXT NOT NULL REFERENCES projects(project_id),
        title                   TEXT NOT NULL,
        source                  TEXT NOT NULL DEFAULT 'other',
        source_url              TEXT,
        occurred_at             TEXT NOT NULL,
        logged_at               TEXT NOT NULL,
        logged_by               TEXT NOT NULL,
        attendees               TEXT NOT NULL DEFAULT '[]',
        summary                 TEXT NOT NULL DEFAULT '',
        raw_notes               TEXT NOT NULL DEFAULT '',
        decisions               TEXT NOT NULL DEFAULT '[]',
        action_items            TEXT NOT NULL DEFAULT '[]',
        integrated_into_status  INTEGER NOT NULL DEFAULT 0,
        integrated_at           TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_min_project ON minutes(project_id);
    """)
    conn.commit()

    # Add slug column to existing DBs (idempotent — OperationalError if already exists)
    try:
        conn.execute("ALTER TABLE projects ADD COLUMN slug TEXT NOT NULL DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists


# ═══════════════════════════════════════════════════════════════════════════════
# Serialisation helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _j(v: Any) -> str:
    """Serialize a value to JSON string for storage."""
    if isinstance(v, list):
        return json.dumps([
            i.model_dump(mode="json") if hasattr(i, "model_dump") else i
            for i in v
        ], default=str)
    if hasattr(v, "model_dump"):
        return json.dumps(v.model_dump(mode="json"), default=str)
    return json.dumps(v, default=str)


def _dt(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_requirement(row: sqlite3.Row) -> RequirementRow:
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
        predecessors=[Dependency(**s)  for s in json.loads(d["predecessors"])],
        dependencies=[Dependency(**s)  for s in json.loads(d["dependencies"])],
        external_links=[ExternalLink(**s) for s in json.loads(d["external_links"])],
        tags=json.loads(d["tags"]),
        created_at=datetime.fromisoformat(d["created_at"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
        has_embedding=bool(d.get("has_embedding", False)),
    )


def _row_to_minute(row: sqlite3.Row) -> MinuteRow:
    d = dict(row)
    return MinuteRow(
        id=d["id"],
        title=d["title"],
        source=d["source"],
        source_url=d.get("source_url"),
        occurred_at=datetime.fromisoformat(d["occurred_at"]),
        logged_at=datetime.fromisoformat(d["logged_at"]),
        logged_by=d["logged_by"],
        attendees=json.loads(d["attendees"]),
        summary=d["summary"],
        raw_notes=d["raw_notes"],
        decisions=[Decision(**x)    for x in json.loads(d["decisions"])],
        action_items=[ActionItem(**x) for x in json.loads(d["action_items"])],
        integrated_into_status=bool(d["integrated_into_status"]),
        integrated_at=_dt(d.get("integrated_at")),
    )


def _row_to_project(row: sqlite3.Row) -> ProjectMeta:
    d = dict(row)
    return ProjectMeta(
        project_id=d["project_id"],
        slug=d.get("slug", ""),
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
        external_links=[ExternalLink(**l) for l in json.loads(d["external_links"])],
        status_summary=d["status_summary"],
        status_updated_at=_dt(d.get("status_updated_at")),
        created_at=datetime.fromisoformat(d["created_at"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Projects
# ═══════════════════════════════════════════════════════════════════════════════

def upsert_project(conn: sqlite3.Connection, meta: ProjectMeta) -> ProjectMeta:
    if not meta.slug:
        meta.slug = C.slugify(meta.name)
    now = _now()
    meta.updated_at = datetime.now(timezone.utc)
    conn.execute("""
        INSERT INTO projects VALUES (
            :project_id,:slug,:name,:code,:phase,:objective,:business_case,
            :success_criteria,:out_of_scope,:project_owner,:sponsor,
            :stakeholders,:start_date,:target_date,:actual_end_date,
            :external_links,:status_summary,:status_updated_at,
            :created_at,:updated_at
        )
        ON CONFLICT(project_id) DO UPDATE SET
            slug=excluded.slug,
            name=excluded.name, code=excluded.code, phase=excluded.phase,
            objective=excluded.objective, business_case=excluded.business_case,
            success_criteria=excluded.success_criteria,
            out_of_scope=excluded.out_of_scope,
            project_owner=excluded.project_owner, sponsor=excluded.sponsor,
            stakeholders=excluded.stakeholders,
            start_date=excluded.start_date, target_date=excluded.target_date,
            actual_end_date=excluded.actual_end_date,
            external_links=excluded.external_links,
            status_summary=excluded.status_summary,
            status_updated_at=excluded.status_updated_at,
            updated_at=excluded.updated_at
    """, {
        "project_id":        meta.project_id,
        "slug":              meta.slug,
        "name":              meta.name,
        "code":              meta.code,
        "phase":             meta.phase.value,
        "objective":         meta.objective,
        "business_case":     meta.business_case,
        "success_criteria":  _j(meta.success_criteria),
        "out_of_scope":      _j(meta.out_of_scope),
        "project_owner":     meta.project_owner,
        "sponsor":           meta.sponsor,
        "stakeholders":      _j(meta.stakeholders),
        "start_date":        str(meta.start_date) if meta.start_date else None,
        "target_date":       str(meta.target_date) if meta.target_date else None,
        "actual_end_date":   str(meta.actual_end_date) if meta.actual_end_date else None,
        "external_links":    _j(meta.external_links),
        "status_summary":    meta.status_summary,
        "status_updated_at": meta.status_updated_at.isoformat() if meta.status_updated_at else None,
        "created_at":        meta.created_at.isoformat(),
        "updated_at":        meta.updated_at.isoformat(),
    })
    conn.commit()
    return meta


def get_project(conn: sqlite3.Connection, project_id: str) -> Optional[ProjectMeta]:
    row = conn.execute(
        "SELECT * FROM projects WHERE project_id = ?", (project_id,)
    ).fetchone()
    return _row_to_project(row) if row else None


def get_project_by_slug(conn: sqlite3.Connection, slug: str) -> Optional[ProjectMeta]:
    """Look up a project by its slug. Returns None if not found."""
    row = conn.execute(
        "SELECT * FROM projects WHERE slug = ?", (slug,)
    ).fetchone()
    return _row_to_project(row) if row else None


def list_projects(conn: sqlite3.Connection) -> list[ProjectMeta]:
    rows = conn.execute(
        "SELECT * FROM projects ORDER BY created_at"
    ).fetchall()
    return [_row_to_project(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# Requirements
# ═══════════════════════════════════════════════════════════════════════════════

def _make_req_id(req_type: RequirementType) -> str:
    import uuid
    return f"REQ-{req_type.value}-{str(uuid.uuid4())[:8].upper()}"


def insert_requirement(
    conn: sqlite3.Connection,
    project_id: str,
    req_in: RequirementIn,
    created_by: str,
) -> RequirementRow:
    now = _now()
    req_id = _make_req_id(req_in.req_type)

    conn.execute("""
        INSERT INTO requirements VALUES (
            :id,:project_id,:req_type,:title,:description,
            :status,:priority,:owner,:stakeholders,:predecessors,
            :dependencies,:external_links,:tags,:created_at,:updated_at
        )
    """, {
        "id":            req_id,
        "project_id":    project_id,
        "req_type":      req_in.req_type.value,
        "title":         req_in.title,
        "description":   req_in.description,
        "status":        req_in.status.value,
        "priority":      req_in.priority.value,
        "owner":         req_in.owner,
        "stakeholders":  _j(req_in.stakeholders),
        "predecessors":  _j(req_in.predecessors),
        "dependencies":  _j(req_in.dependencies),
        "external_links":_j(req_in.external_links),
        "tags":          _j(req_in.tags),
        "created_at":    now,
        "updated_at":    now,
    })

    # Initial update record
    _write_update(conn, UpdateRecord(
        requirement_id=req_id,
        changed_by=created_by,
        summary="Requirement created.",
        diffs=[],
        full_snapshot=None,
    ))

    # Compute and store embedding
    _store_embedding(conn, req_id, req_in.title, req_in.description)

    conn.commit()
    return get_requirement(conn, req_id)


def update_requirement(
    conn: sqlite3.Connection,
    req_id: str,
    project_id: str,
    changes: dict[str, Any],
    changed_by: str,
    summary: str,
) -> RequirementRow:
    """
    Apply a partial update to a requirement.
    `changes` maps field names to new values (only changed fields needed).
    Writes field diffs + full snapshot on status transition.
    """
    existing = get_requirement(conn, req_id)
    if not existing:
        raise KeyError(f"Requirement '{req_id}' not found.")

    # Validate changes through RequirementIn
    updatable = {
        "req_type", "title", "description", "status", "priority",
        "owner", "stakeholders", "predecessors", "dependencies",
        "external_links", "tags",
    }
    bad = set(changes) - updatable
    if bad:
        raise ValueError(f"Fields not updatable: {bad}")

    # Build diffs
    diffs: list[FieldDiff] = []
    current = existing.model_dump(mode="json")
    for field, new_val in changes.items():
        old_val = current.get(field)
        if old_val != new_val:
            diffs.append(FieldDiff(field=field, old_value=old_val, new_value=new_val))

    if not diffs:
        return existing  # nothing changed

    # Full snapshot on status transition
    full_snap = None
    if "status" in changes and changes["status"] in C.SNAPSHOT_ON_STATUSES:
        full_snap = current

    _write_update(conn, UpdateRecord(
        requirement_id=req_id,
        changed_by=changed_by,
        summary=summary,
        diffs=diffs,
        full_snapshot=full_snap,
    ))

    # Build SET clause dynamically
    col_map = {
        "req_type":      ("req_type",      lambda v: RequirementType(v).value),
        "title":         ("title",         None),
        "description":   ("description",   None),
        "status":        ("status",        lambda v: RequirementStatus(v).value),
        "priority":      ("priority",      lambda v: RequirementPriority(v).value),
        "owner":         ("owner",         None),
        "stakeholders":  ("stakeholders",  _j),
        "predecessors":  ("predecessors",  _j),
        "dependencies":  ("dependencies",  _j),
        "external_links":("external_links",_j),
        "tags":          ("tags",          _j),
    }
    sets, params = [], {}
    for field, new_val in changes.items():
        col, transform = col_map[field]
        params[col] = transform(new_val) if transform else new_val
        sets.append(f"{col} = :{col}")

    now = _now()
    params["updated_at"] = now
    params["req_id"]     = req_id
    sets.append("updated_at = :updated_at")

    conn.execute(
        f"UPDATE requirements SET {', '.join(sets)} WHERE id = :req_id",
        params
    )

    # Re-embed if title or description changed
    if "title" in changes or "description" in changes:
        new_title = changes.get("title", existing.title)
        new_desc  = changes.get("description", existing.description)
        _store_embedding(conn, req_id, new_title, new_desc)

    conn.commit()
    return get_requirement(conn, req_id)


def get_requirement(conn: sqlite3.Connection, req_id: str) -> Optional[RequirementRow]:
    row = conn.execute("""
        SELECT r.*,
               CASE WHEN e.requirement_id IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
        FROM requirements r
        LEFT JOIN req_embeddings e ON e.requirement_id = r.id
        WHERE r.id = ?
    """, (req_id,)).fetchone()
    return _row_to_requirement(row) if row else None


def search_requirements(
    conn: sqlite3.Connection,
    project_id: str,
    status:   Optional[str] = None,
    priority: Optional[str] = None,
    req_type: Optional[str] = None,
    owner:    Optional[str] = None,
    tag:      Optional[str] = None,
    keyword:  Optional[str] = None,
) -> list[RequirementRow]:
    """Structured field-based search with optional keyword match on title/description."""
    clauses = ["r.project_id = :project_id"]
    params: dict = {"project_id": project_id}

    if status:   clauses.append("r.status = :status");     params["status"]   = status
    if priority: clauses.append("r.priority = :priority"); params["priority"] = priority
    if req_type: clauses.append("r.req_type = :req_type"); params["req_type"] = req_type.upper()
    if owner:    clauses.append("r.owner = :owner");       params["owner"]    = owner
    if tag:
        clauses.append("json_each.value = :tag")
        # joined below
    if keyword:
        clauses.append(
            "(r.title LIKE :kw OR r.description LIKE :kw)"
        )
        params["kw"] = f"%{keyword}%"

    tag_join = (
        "JOIN json_each(r.tags) ON json_each.value = :tag" if tag else ""
    )
    if tag:
        params["tag"] = tag
        # remove duplicate clause added above
        clauses = [c for c in clauses if "json_each.value" not in c]

    where = " AND ".join(clauses)
    sql = f"""
        SELECT r.*,
               CASE WHEN e.requirement_id IS NOT NULL THEN 1 ELSE 0 END AS has_embedding
        FROM requirements r
        LEFT JOIN req_embeddings e ON e.requirement_id = r.id
        {tag_join}
        WHERE {where}
        ORDER BY r.created_at
    """
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_requirement(r) for r in rows]


def vector_search(
    conn: sqlite3.Connection,
    project_id: str,
    query_text: str,
    top_k: int = 10,
) -> list[tuple[RequirementRow, float]]:
    """
    Embed query_text and return the top_k most similar requirements by cosine distance.
    Returns list of (RequirementRow, distance) tuples, closest first.
    """
    q_vec  = embed(query_text)
    q_blob = _vec_to_blob(q_vec)

    # sqlite-vec returns (requirement_id, distance) from the virtual table
    vec_rows = conn.execute("""
        SELECT requirement_id, distance
        FROM req_embeddings
        WHERE embedding MATCH ?
          AND k = ?
        ORDER BY distance
    """, (q_blob, top_k)).fetchall()

    results = []
    for vec_row in vec_rows:
        req_id   = vec_row["requirement_id"]
        distance = vec_row["distance"]
        req = get_requirement(conn, req_id)
        if req and req.id in (
            r.id for r in search_requirements(conn, project_id)
        ):
            results.append((req, distance))
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Internal: embedding storage
# ═══════════════════════════════════════════════════════════════════════════════

def _store_embedding(
    conn: sqlite3.Connection,
    req_id: str,
    title: str,
    description: str,
) -> None:
    """Generate and upsert an embedding for a requirement. Silently skips if no API key."""
    if not C.EMBEDDING_API_KEY:
        return
    try:
        vec  = embed(f"{title}\n\n{description}".strip())
        blob = _vec_to_blob(vec)
        conn.execute("""
            INSERT INTO req_embeddings(requirement_id, embedding) VALUES (?, ?)
            ON CONFLICT(requirement_id) DO UPDATE SET embedding = excluded.embedding
        """, (req_id, blob))
    except Exception as e:
        # Non-fatal: requirement is saved, embedding just won't be available
        import warnings
        warnings.warn(f"Embedding generation failed for {req_id}: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Internal: update log
# ═══════════════════════════════════════════════════════════════════════════════

def _write_update(conn: sqlite3.Connection, record: UpdateRecord) -> None:
    conn.execute("""
        INSERT INTO updates(id, requirement_id, changed_at, changed_by,
                            summary, diffs, full_snapshot)
        VALUES (:id,:req_id,:changed_at,:changed_by,:summary,:diffs,:full_snap)
    """, {
        "id":         record.id,
        "req_id":     record.requirement_id,
        "changed_at": record.changed_at.isoformat(),
        "changed_by": record.changed_by,
        "summary":    record.summary,
        "diffs":      _j(record.diffs),
        "full_snap":  json.dumps(record.full_snapshot) if record.full_snapshot else None,
    })


def get_updates(
    conn: sqlite3.Connection,
    req_id: str,
) -> list[UpdateRecord]:
    rows = conn.execute(
        "SELECT * FROM updates WHERE requirement_id = ? ORDER BY changed_at",
        (req_id,)
    ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        result.append(UpdateRecord(
            id=d["id"],
            requirement_id=d["requirement_id"],
            changed_at=datetime.fromisoformat(d["changed_at"]),
            changed_by=d["changed_by"],
            summary=d["summary"],
            diffs=[FieldDiff(**x) for x in json.loads(d["diffs"])],
            full_snapshot=json.loads(d["full_snapshot"]) if d["full_snapshot"] else None,
        ))
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Minutes
# ═══════════════════════════════════════════════════════════════════════════════

def insert_minute(
    conn: sqlite3.Connection,
    project_id: str,
    minute_in: MinuteIn,
) -> MinuteRow:
    import uuid as _uuid
    now = _now()
    mid = f"MTG-{str(_uuid.uuid4())[:8].upper()}"
    conn.execute("""
        INSERT INTO minutes VALUES (
            :id,:project_id,:title,:source,:source_url,
            :occurred_at,:logged_at,:logged_by,:attendees,
            :summary,:raw_notes,:decisions,:action_items,0,NULL
        )
    """, {
        "id":          mid,
        "project_id":  project_id,
        "title":       minute_in.title,
        "source":      minute_in.source.value,
        "source_url":  minute_in.source_url,
        "occurred_at": minute_in.occurred_at.isoformat(),
        "logged_at":   now,
        "logged_by":   minute_in.logged_by,
        "attendees":   _j(minute_in.attendees),
        "summary":     minute_in.summary,
        "raw_notes":   minute_in.raw_notes,
        "decisions":   _j(minute_in.decisions),
        "action_items":_j(minute_in.action_items),
    })
    conn.commit()
    return get_minute(conn, mid)


def get_minute(conn: sqlite3.Connection, minute_id: str) -> Optional[MinuteRow]:
    row = conn.execute(
        "SELECT * FROM minutes WHERE id = ?", (minute_id,)
    ).fetchone()
    return _row_to_minute(row) if row else None


def list_minutes(
    conn: sqlite3.Connection,
    project_id: str,
    source:       Optional[str]  = None,
    unintegrated: bool           = False,
    since:        Optional[str]  = None,
) -> list[MinuteRow]:
    clauses = ["project_id = :project_id"]
    params: dict = {"project_id": project_id}
    if source:       clauses.append("source = :source");               params["source"] = source
    if unintegrated: clauses.append("integrated_into_status = 0")
    if since:        clauses.append("occurred_at >= :since");          params["since"]  = since
    rows = conn.execute(
        f"SELECT * FROM minutes WHERE {' AND '.join(clauses)} ORDER BY occurred_at",
        params
    ).fetchall()
    return [_row_to_minute(r) for r in rows]


def mark_integrated(conn: sqlite3.Connection, minute_id: str) -> MinuteRow:
    now = _now()
    conn.execute("""
        UPDATE minutes
        SET integrated_into_status = 1, integrated_at = ?
        WHERE id = ?
    """, (now, minute_id))
    conn.commit()
    return get_minute(conn, minute_id)


def list_decisions(
    conn: sqlite3.Connection,
    project_id: str,
    status:      Optional[str] = None,
    affects_req: Optional[str] = None,
) -> list[dict]:
    """Return flat list of decisions across all meetings for a project."""
    minutes = list_minutes(conn, project_id)
    out = []
    for m in minutes:
        for d in m.decisions:
            if status and d.status.value != status:
                continue
            if affects_req and affects_req not in d.affects_reqs:
                continue
            out.append({
                "meeting_id":   m.id,
                "meeting_title":m.title,
                **d.model_dump(mode="json"),
            })
    return out