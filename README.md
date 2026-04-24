# Requirements Agent

A multi-skill agent for managing software and AI project requirements, meetings, and status reporting. Built on SQLite + sqlite-vec with Pydantic validation and optional OpenAI-compatible embedding for semantic search.

---

## Structure

```
requirements-agent/
├── README.md
├── shared/                        ← imported by all skills
│   ├── CONSTANTS.py               ← all config: paths, embedding backend
│   ├── models.py                  ← Pydantic models (validation gate)
│   ├── db.py                      ← SQLite persistence + sqlite-vec
│   ├── md_writer.py               ← PROJECT.md generation
│   └── project_session.py         ← session resolution (which project?)
│
├── projects/                      ← created automatically
│   └── <project-slug>/
│       ├── <project-slug>.db      ← SQLite database
│       ├── PROJECT.md             ← auto-generated header + protected notes
│       └── STATUS-<timestamp>.md  ← saved status reports (optional)
│
└── skills/
    ├── project-init/              ← create / update project metadata
    ├── project-update/            ← requirement CRUD + search
    ├── refine-requirements/       ← FRET grammar refinement
    ├── review-requirements/       ← gap analysis, conflicts, coverage
    ├── meeting-agent/             ← log minutes, decisions, actions
    └── status-report/             ← generate project status reports
```

---

## Skills reference

| Skill | Script | Key commands |
|-------|--------|--------------|
| project-update | `req_ops.py` | `add` `update` `get` `list` `search` `history` `vector` |
| refine-requirements | `refine.py` | `pending` `show` `apply` `coverage` |
| review-requirements | `review.py` | `report` `gaps` `conflicts` `coverage` |
| meeting-agent | `meeting.py` | `log` `get` `list` `decisions` `update_decision` `close_action` `integrate` |
| status-report | `report.py` | `generate` `save` |

All scripts accept `--project <slug-or-partial-name>` to select the active project.
If only one project exists, it is selected automatically.

---

## Configuration (`shared/CONSTANTS.py`)

| Variable | Default | Override |
|----------|---------|----------|
| `PROJECTS_DIR` | `<agent-root>/projects` | `PROJECTS_DIR` env var (absolute path) |
| `EMBEDDING_API_BASE` | `https://api.openai.com/v1` | `EMBEDDING_API_BASE` env var |
| `EMBEDDING_API_KEY` | `$OPENAI_API_KEY` | `OPENAI_API_KEY` env var |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | `EMBEDDING_MODEL` env var |
| `EMBEDDING_DIM` | `1536` | `EMBEDDING_DIM` env var |

---

## Database layout

Each project has its own SQLite file at `projects/<slug>/<slug>.db`.

| Table | Contents |
|-------|----------|
| `project` | One row — all project metadata |
| `requirements` | One row per requirement, with JSON columns for lists |
| `req_embeddings` | sqlite-vec virtual table for vector search |
| `updates` | Append-only change log with field diffs + status-transition snapshots |
| `minutes` | Meeting records with embedded decisions and action items |

---

## Requirement IDs

Requirements get typed IDs derived from their category:

| Type | ID prefix | Use for |
|------|-----------|---------|
| `CORE` | `REQ-CORE-` | Cross-cutting, foundational |
| `DATA` | `REQ-DATA-` | Pipelines, storage, data quality |
| `MODEL` | `REQ-MODEL-` | ML training, inference, evaluation |
| `INFRA` | `REQ-INFRA-` | Cloud, networking, infrastructure |
| `OPS` | `REQ-OPS-` | Monitoring, alerting, operations |
| `UX` | `REQ-UX-` | User experience, UI |
| `COMPLIANCE` | `REQ-COMPLIANCE-` | Risk, ethics, EU AI Act |

Requirements are **never deleted** — only their status changes
(`open → in-progress → done / rejected`).

---

## FRET grammar

FRET (NASA Formal Requirements Elicitation Tool) produces unambiguous,
machine-checkable requirements in the form:

```
[SCOPE] [CONDITION] the COMPONENT shall [TIMING] RESPONSE
```

Full reference: `skills/refine-requirements/references/fret_grammar.md`

---

## Migrating to remote storage

Change `PROJECTS_DIR` in `shared/CONSTANTS.py` or via the `PROJECTS_DIR`
environment variable to any mounted path (NFS, S3 via rclone, etc.).
No skill code changes are required.
