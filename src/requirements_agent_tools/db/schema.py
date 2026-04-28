"""DDL and reference-data seeding for the per-project SQLite database."""

from __future__ import annotations

import sqlite3

from .. import CONSTANTS as C
from ..models import (
    DecisionStatus,
    MeetingSource,
    ProjectPhase,
    REQUIREMENT_TYPE_METADATA,
    RequirementPriority,
    RequirementStatus,
)


SCHEMA_SQL: str = f"""
-- ── Projects ──────────────────────────────────────────────────────────
-- Each database file holds at most one project. The ``singleton`` column
-- is constrained to the literal value 1 and has a UNIQUE index, so the
-- table can never contain more than a single row — enforced structurally
-- by the engine, not by application code.
CREATE TABLE IF NOT EXISTS projects (
    project_id        TEXT PRIMARY KEY,
    singleton         INTEGER NOT NULL DEFAULT 1 CHECK (singleton = 1),
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_singleton ON projects(singleton);

-- ── Requirements ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS requirements (
    id             TEXT PRIMARY KEY,
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
-- Polymorphic audit log. ``entity_type`` discriminates the record kind:
--   'requirement' → entity_id is a requirements.id
--   'project_md'  → entity_id is the singleton projects.project_id
CREATE TABLE IF NOT EXISTS updates (
    id             TEXT PRIMARY KEY,
    entity_type    TEXT NOT NULL CHECK (entity_type IN ('requirement', 'project_md')),
    entity_id      TEXT NOT NULL,
    changed_at     TEXT NOT NULL,
    changed_by     TEXT NOT NULL,
    summary        TEXT NOT NULL DEFAULT '',
    diffs          TEXT NOT NULL DEFAULT '[]',
    full_snapshot  TEXT
);

CREATE INDEX IF NOT EXISTS idx_upd_entity ON updates(entity_type, entity_id);

-- ── Minutes ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS minutes (
    id                      TEXT PRIMARY KEY,
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

-- ── Reference / lookup tables (enum catalogues) ───────────────────────
CREATE TABLE IF NOT EXISTS requirement_types (
    code        TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS requirement_statuses (
    value TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS requirement_priorities (
    value TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS project_phases (
    value TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS meeting_sources (
    value TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS decision_statuses (
    value TEXT PRIMARY KEY
);
"""


def seed_reference_tables(conn: sqlite3.Connection) -> None:
    """Populate the enum catalogue tables.

    Idempotent: every row is written with ``INSERT OR REPLACE`` so calling
    this on every bootstrap is safe.

    Args:
        conn: An open SQLite connection with the schema already created.
    """
    conn.executemany(
        "INSERT OR REPLACE INTO requirement_types(code, name, description) VALUES (?, ?, ?)",
        [(m.code, m.name, m.description) for m in REQUIREMENT_TYPE_METADATA],
    )
    for table, enum_cls in (
        ("requirement_statuses", RequirementStatus),
        ("requirement_priorities", RequirementPriority),
        ("project_phases", ProjectPhase),
        ("meeting_sources", MeetingSource),
        ("decision_statuses", DecisionStatus),
    ):
        conn.executemany(
            f"INSERT OR REPLACE INTO {table}(value) VALUES (?)",
            [(e.value,) for e in enum_cls],
        )
    conn.commit()
