"""DDL and reference-data seeding for the per-project SQLite database."""

from __future__ import annotations

import sqlite3

from loguru import logger

from .. import CONSTANTS as C
from ..models import (
    IssuePriority,
    IssueStatus,
    ProjectPhase,
    REQUIREMENT_TYPE_METADATA,
    RequirementPriority,
    RequirementStatus,
)


BASE_SCHEMA_SQL: str = """
-- ── Projects ──────────────────────────────────────────────────────────
-- Each database file holds at most one project. The singleton column
-- is constrained to the literal value 1 and has a UNIQUE index, so the
-- table can never contain more than a single row — enforced structurally
-- by the engine, not by application code.
-- slug column removed: single-project model has no need for slug-based paths.
CREATE TABLE IF NOT EXISTS projects (
    project_id        TEXT PRIMARY KEY,
    singleton         INTEGER NOT NULL DEFAULT 1 CHECK (singleton = 1),
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

-- ── Updates (change log) ──────────────────────────────────────────────
-- Polymorphic audit log. entity_type discriminates the record kind:
--   'requirement' → entity_id is a requirements.id
--   'project'     → entity_id is the singleton projects.project_id
--   'issue'       → entity_id is an issues.id
CREATE TABLE IF NOT EXISTS updates (
    id             TEXT PRIMARY KEY,
    entity_type    TEXT NOT NULL CHECK (entity_type IN ('requirement', 'project', 'issue')),
    entity_id      TEXT NOT NULL,
    changed_at     TEXT NOT NULL,
    changed_by     TEXT NOT NULL,
    summary        TEXT NOT NULL DEFAULT '',
    diffs          TEXT NOT NULL DEFAULT '[]',
    full_snapshot  TEXT
);

CREATE INDEX IF NOT EXISTS idx_upd_entity ON updates(entity_type, entity_id);

-- ── Issues ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS issues (
    id             TEXT PRIMARY KEY,
    title          TEXT NOT NULL,
    description    TEXT NOT NULL DEFAULT '',
    status         TEXT NOT NULL DEFAULT 'open',
    priority       TEXT NOT NULL DEFAULT 'medium',
    owner          TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_issue_status   ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issue_priority ON issues(priority);

-- ── Issue Links (Many-to-Many) ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS issue_requirements (
    issue_id       TEXT NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    requirement_id TEXT NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
    PRIMARY KEY (issue_id, requirement_id)
);

CREATE TABLE IF NOT EXISTS issue_updates (
    issue_id       TEXT NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    update_id      TEXT NOT NULL REFERENCES updates(id) ON DELETE CASCADE,
    PRIMARY KEY (issue_id, update_id)
);

CREATE TABLE IF NOT EXISTS issue_actions_log (
    id             TEXT PRIMARY KEY,
    issue_id       TEXT NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    occurred_at    TEXT NOT NULL,
    description    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_issue_action_issue ON issue_actions_log(issue_id);

-- ── Vector metadata (always present to avoid join failures) ──────────
CREATE TABLE IF NOT EXISTS req_embeddings (
    requirement_id TEXT PRIMARY KEY REFERENCES requirements(id) ON DELETE CASCADE,
    embedding      BLOB
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

CREATE TABLE IF NOT EXISTS issue_statuses (
    value TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS issue_priorities (
    value TEXT PRIMARY KEY
);

-- ── Full Text Search (FTS5) ──────────────────────────────────────────
CREATE VIRTUAL TABLE IF NOT EXISTS fts_requirements USING fts5(
    id UNINDEXED,
    title,
    description,
    tokenize="unicode61 remove_diacritics 1"
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_issues USING fts5(
    id UNINDEXED,
    title,
    description,
    tokenize="unicode61 remove_diacritics 1"
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_updates USING fts5(
    entity_id UNINDEXED,
    entity_type UNINDEXED,
    summary,
    tokenize="unicode61 remove_diacritics 1"
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_issue_actions USING fts5(
    issue_id UNINDEXED,
    description,
    tokenize="unicode61 remove_diacritics 1"
);

-- ── FTS Triggers ─────────────────────────────────────────────────────

-- Requirements
CREATE TRIGGER IF NOT EXISTS tr_req_fts_ins AFTER INSERT ON requirements BEGIN
    INSERT INTO fts_requirements(id, title, description) VALUES (new.id, new.title, new.description);
END;
CREATE TRIGGER IF NOT EXISTS tr_req_fts_upd AFTER UPDATE ON requirements BEGIN
    UPDATE fts_requirements SET title = new.title, description = new.description WHERE id = new.id;
END;
CREATE TRIGGER IF NOT EXISTS tr_req_fts_del AFTER DELETE ON requirements BEGIN
    DELETE FROM fts_requirements WHERE id = old.id;
END;

-- Issues
CREATE TRIGGER IF NOT EXISTS tr_issue_fts_ins AFTER INSERT ON issues BEGIN
    INSERT INTO fts_issues(id, title, description) VALUES (new.id, new.title, new.description);
END;
CREATE TRIGGER IF NOT EXISTS tr_issue_fts_upd AFTER UPDATE ON issues BEGIN
    UPDATE fts_issues SET title = new.title, description = new.description WHERE id = new.id;
END;
CREATE TRIGGER IF NOT EXISTS tr_issue_fts_del AFTER DELETE ON issues BEGIN
    DELETE FROM fts_issues WHERE id = old.id;
END;

-- Updates
CREATE TRIGGER IF NOT EXISTS tr_upd_fts_ins AFTER INSERT ON updates BEGIN
    INSERT INTO fts_updates(entity_id, entity_type, summary) VALUES (new.entity_id, new.entity_type, new.summary);
END;
CREATE TRIGGER IF NOT EXISTS tr_upd_fts_del AFTER DELETE ON updates BEGIN
    DELETE FROM fts_updates WHERE entity_id = old.entity_id AND entity_type = old.entity_type AND summary = old.summary;
END;

-- Issue Actions
CREATE TRIGGER IF NOT EXISTS tr_action_fts_ins AFTER INSERT ON issue_actions_log BEGIN
    INSERT INTO fts_issue_actions(issue_id, description) VALUES (new.issue_id, new.description);
END;
CREATE TRIGGER IF NOT EXISTS tr_action_fts_del AFTER DELETE ON issue_actions_log BEGIN
    DELETE FROM fts_issue_actions WHERE issue_id = old.issue_id AND description = old.description;
END;
"""


VEC_SCHEMA_SQL: str = f"""
-- ── Vec virtual table for requirement embeddings ───────────────────────
-- Created only when sqlite_vec: true in config/project.yaml.
CREATE VIRTUAL TABLE IF NOT EXISTS req_embeddings_vec
USING vec0(
    requirement_id TEXT PRIMARY KEY,
    embedding      FLOAT[{C.EMBEDDING_DIM}]
);
"""


def seed_reference_tables(conn: sqlite3.Connection) -> None:
    """Populate the enum catalogue tables.

    Idempotent: every row is written with INSERT OR REPLACE so calling
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
        ("issue_statuses", IssueStatus),
        ("issue_priorities", IssuePriority),
    ):
        conn.executemany(
            f"INSERT OR REPLACE INTO {table}(value) VALUES (?)",  # noqa: S608
            [(e.value,) for e in enum_cls],
        )
    conn.commit()


def reindex_fts(conn: sqlite3.Connection) -> None:
    """Populate FTS5 virtual tables from base tables if they are empty.

    Args:
        conn: Open SQLite connection.
    """
    # Check if FTS tables are empty
    has_data = conn.execute("SELECT 1 FROM fts_requirements LIMIT 1").fetchone()
    if has_data:
        return

    logger.info("Populating initial full-text search index...")
    conn.execute(
        "INSERT INTO fts_requirements(id, title, description) SELECT id, title, description FROM requirements"
    )
    conn.execute(
        "INSERT INTO fts_issues(id, title, description) SELECT id, title, description FROM issues"
    )
    conn.execute(
        "INSERT INTO fts_updates(entity_id, entity_type, summary) SELECT entity_id, entity_type, summary FROM updates"
    )
    conn.execute(
        "INSERT INTO fts_issue_actions(issue_id, description) SELECT issue_id, description FROM issue_actions_log"
    )
    conn.commit()
    logger.success("FTS index populated")
