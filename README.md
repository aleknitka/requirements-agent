# Requirements Agent

A multi-skill agent for managing software and AI project requirements,
meetings, and status reporting. Built on SQLite + sqlite-vec with Pydantic
validation and optional OpenAI-compatible embedding for semantic search.

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

## Quick start

### 1. Install dependencies

```bash
uv sync
```

For vector/semantic search (optional):
```bash
export OPENAI_API_KEY="sk-..."          # or any OpenAI-compatible key
```

To use a local embedding model (Ollama, LM Studio, etc.), set env vars or edit `shared/CONSTANTS.py`:
```bash
export EMBEDDING_API_BASE="http://localhost:11434/v1"
export EMBEDDING_MODEL="nomic-embed-text"
export EMBEDDING_DIM="768"
```

### 2. Create a project

The agent should interview the user and collect:
- Name, code, objective, business case
- Success criteria, out of scope
- Project owner, sponsor, key stakeholders
- Target dates, external links (Confluence, Jira, etc.)

```bash
python skills/project-init/scripts/init.py new \
  --name "My Project" \
  --code "PROJ-25" \
  --objective "..." \
  --business-case "..." \
  --project-owner "alice" \
  --sponsor "cto-office" \
  --success-criteria '["criterion 1","criterion 2"]' \
  --stakeholders '[{"name":"Alice","role":"sponsor","contact":"alice@co.com"}]'
```

### 3. Add requirements

```bash
python skills/project-update/scripts/req_ops.py add \
  --type DATA \
  --title "Ingest clickstream events in real-time" \
  --by "alice" \
  --priority critical \
  --description "Consume Kafka topic at 100k events/sec."
```

### 4. Refine with FRET

```bash
# Find requirements needing refinement
python skills/refine-requirements/scripts/refine.py pending

# Apply a FRET statement (after user confirms)
python skills/refine-requirements/scripts/refine.py apply \
  --id REQ-DATA-XXXX \
  --by "alice" \
  --fret-statement "the data pipeline shall within 500ms ingest and deduplicate the event" \
  --fret-fields '{"component":"the data pipeline","timing":"within 500ms","response":"ingest and deduplicate the event"}'
```

### 5. Review

```bash
python skills/review-requirements/scripts/review.py report
```

### 6. Log a meeting

```bash
python skills/meeting-agent/scripts/meeting.py log \
  --title "Sprint 1 planning" \
  --by "agent-001" \
  --source teams \
  --summary "Team aligned on architecture." \
  --decisions '[{"title":"Use Kafka","made_by":["Alice"],"status":"open","affects_reqs":["REQ-DATA-XXXX"]}]' \
  --action-items '[{"description":"Provision S3 buckets","owner":"Bob","due_date":"2025-05-01"}]'
```

### 7. Generate a status report

```bash
# Preview
python skills/status-report/scripts/report.py generate --format md

# Save timestamped copy
python skills/status-report/scripts/report.py save
```

---

## Skills reference

| Skill | Script | Key commands |
|-------|--------|--------------|
| project-init | `init.py` | `new` `list` `update` |
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
