# External Integrations

**Analysis Date:** 2026-04-21

## APIs & External Services

**LLM Inference:**
- Anthropic Claude — primary model for agent reasoning
  - Preferred model: `anthropic/claude-opus-4.6` (configured in `agent.yaml`)
  - Fallbacks: `openai/gpt-5.2`, `openai/gpt-oss-20b`, `google/gemma-4-31b`
  - Auth: managed by the `prek` agent runtime; no direct SDK call in application code

**Embedding API:**
- OpenAI Embeddings — used for vector search on requirements
  - SDK: `openai` 2.32.0 (called directly in `shared/db.py` `embed()` function)
  - Auth: `OPENAI_API_KEY` environment variable
  - Base URL: `EMBEDDING_API_BASE` env var (defaults to `https://api.openai.com/v1`)
  - Model: `EMBEDDING_MODEL` env var (defaults to `text-embedding-3-small`)
  - Dimension: `EMBEDDING_DIM` env var (defaults to `1536`)

## Data Storage

**Databases:**
- SQLite (stdlib `sqlite3`) with `sqlite-vec` 0.1.9 extension for vector similarity
  - One database per project: `projects/<slug>/<slug>.db`
  - Connection opened via `db.get_db(path)` in `shared/db.py`
  - Vector table created by `bootstrap(conn)` using `sqlite_vec.load(conn)`

**File Storage:**
- Local filesystem only — `projects/<slug>/PROJECT.md` auto-generated markdown per project
- Override with `PROJECTS_DIR` environment variable for alternate path

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- None (local tool; no user authentication layer)
- API key authentication for OpenAI embedding calls via `OPENAI_API_KEY`
- LLM provider auth delegated to `prek` framework at agent runtime level

## Monitoring & Observability

**Error Tracking:**
- None (no third-party error tracking)

**Logs:**
- All skill scripts write structured JSON to stdout (success) and stderr (error)
- `agent.yaml` declares `audit_logging: true` with `log_format: structured_json`; implemented by `prek` runtime
- Audit log contents per spec: prompts_and_responses, tool_calls, decision_pathways, model_version, timestamps
- Retention: 6 years (configured in `agent.yaml`)

**Hooks:**
- `hooks/hooks.yaml` defines `on_session_start` → `hooks/scripts/on-start.sh` (loads project context)
- `hooks/hooks.yaml` defines `on_error` → `hooks/scripts/on-error.sh` (error handling/escalation)
- Both hooks: `fail_open: true`, `timeout: 10s`

## CI/CD & Deployment

**Hosting:**
- Local/CLI deployment only — no web hosting detected

**CI Pipeline:**
- Not detected (no GitHub Actions, CircleCI, or similar config files present)

## External Document Systems

**Supported Link Targets (metadata only — not live integrations):**
- Confluence, SharePoint, Jira, programme boards — tracked as `ExternalLink` objects in `shared/models.py` (system, label, url fields)
- These are stored as metadata; the agent does not call these APIs

## Meeting Source Tracking

**Tracked Sources (metadata only — not live integrations):**
- Teams, Slack, Zoom, email, direct, in-person — recorded as `MeetingSource` enum in `shared/models.py`
- Raw transcript text is ingested manually; no live API connections to these platforms

## Environment Configuration

**Required env vars for full functionality:**
- `OPENAI_API_KEY` — required for semantic/vector search on requirements

**Optional env vars:**
- `PROJECTS_DIR` — override projects storage directory
- `EMBEDDING_API_BASE` — override embedding endpoint (for self-hosted models)
- `EMBEDDING_MODEL` — override embedding model name
- `EMBEDDING_DIM` — override embedding vector dimension

**Secrets location:**
- Environment variables only; no `.env` file committed to the repository

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-04-21*
