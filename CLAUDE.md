# CLAUDE.md

# PRD: Requirements Management Agent with SQLite-backed MCP

## 1. Product Overview

This project defines a GitAgent-style requirements management agent supported by a local SQLite-backed MCP server. The system is designed for requirements elicitation, formulation, tracking, auditing, issue management, and evidence-based requirement updates.

The agent handles stakeholder interaction, interviewing, reasoning, and requirement formulation. The `requirements_mcp` package owns all persistence, validation, database operations, audit trails, issue tracking, evidence links, and human-facing Gradio workflows.

The repository is structured as a single Git repository with agentic configuration at the root level and Python packages under `packages/`.

---

## 2. Goals

The system must allow an AI agent to:

- Interview users and stakeholders about requirements, business goals and needs.
- Formulate structured requirements from conversations.
- Store requirements in a local SQLite database.
- Formalise requirements using a framework.
- Update requirements with full diff-based audit history.
- Track unresolved issues, risks, ambiguities, blockers, and follow-up actions.
- Use issues as an operational action log and todo list.
- Link issues to requirements.
- Provide a local Gradio frontend for human inspection and manual edits.
- Expose all database operations through MCP tools.

---

## 3. Non-Goals

The initial version will not implement:

- Multi-user authentication.
- Cloud-hosted database infrastructure.
- Full role-based access control.
- Enterprise workflow approval engine.
- Production-grade email ingestion.
- Vector search.
- Real-time collaborative editing.
- PostgreSQL deployment.
- Evidence gathering, storing and linking.
- Email reading and sending capability.
- Contact book creation.
- Ability to interact via Teams, Slack and other communication channels. 

The architecture should not block these future extensions.

---

## 4. Repository Structure

The repository uses a GitAgent-style layout at the root and a `uv` workspace for Python packages.

```text
requirements-agent/
  agent.yaml
  SOUL.md
  RULES.md
  CLAUDE.md

  memory/
  skills/
  tools/
  hooks/
  logs/
  compliance/
  config/
  knowledge/
  workflows/

  pyproject.toml
  uv.lock

  packages/
    requirements_mcp/
      pyproject.toml
      src/requirements_mcp/
      tests/

  data/
    .gitkeep
```

---

## 5. Package Responsibilities

### 5.1 Root Agentic Layer

The root-level agentic files define the agent's identity, rules, skills, tool wiring, and operating constraints.

Root-level responsibilities:

- Agent identity and behaviour.
- Skill definitions.
- MCP tool registration.
- Runtime hooks.
- Agent memory files.
- Development instructions.

The root agentic layer must not contain database persistence logic.

---

### 5.2 REMOVED
---
### 5.3 `packages/requirements_mcp`

The `requirements_mcp` package is the authoritative persistence and operational memory layer around requirements and actions.

Responsibilities:

- SQLite database initialisation.
- SQLAlchemy ORM models.
- Alembic migrations.
- Pydantic validation models.
- Requirement creation and updates.
- Requirement change logging.
- Issue creation and updates.
- Issue action log management.
- Evidence storage and linking.
- Controlled metadata seeding.
- MCP tool exposure.
- Gradio frontend for human users.

The agent must interact with this package through MCP tools, not through direct imports of repositories or database models.

---

## 6. Technology Choices

### 6.1 Python Environment

Use `uv` for dependency and workspace management.

Root workspace members:

```toml
[tool.uv.workspace]
members = [
  "packages/requirements_mcp",
]
```

### 6.2 Database

Use SQLite for the local-first database backend.

Use SQLAlchemy ORM for schema definition and persistence.

Use Alembic for migrations once schema evolution begins.

### 6.3 Validation

Use Pydantic v2 for:

- MCP tool input validation.
- Seed data validation.
- Gradio input validation.
- Internal command schemas.

SQLAlchemy models are not sufficient as validation boundaries.

### 6.4 Frontend

Use Gradio for local human-facing workflows:

- Add requirements.
- Search requirements.
- View requirement details.
- Update requirements.
- View change history.
- Create and update issues.
- View issue action logs.
- Attach or inspect evidence.

### 6.5 MCP

Use the Python MCP SDK to expose tools over local stdio transport.

The MCP server is the only supported programmatic interface for the agent.

---

## 7. Core Design Principles

### 7.1 MCP Owns Persistence

The `requirements_mcp` package owns all database operations.

The agent must never:

- Execute SQL.
- Open a SQLite connection directly.
- Import SQLAlchemy models from `requirements_mcp`.
- Mutate database records outside MCP tools.

### 7.2 Audit Trail Is Mandatory

Every meaningful update to a requirement or issue must be logged.

Requirement updates must create a `requirements_changes` row.

Issue updates and actions must create an `issue_updates` row.

No silent state changes are allowed.

### 7.3 Issues Are Operational Memory

Issues are not only bugs. They represent:

- Ambiguities.
- Missing information.
- Risks.
- Blockers.
- Conflicts.
- Stakeholder questions.
- Decisions needed.
- Evidence gaps.
- Follow-up tasks.
- Agent todo items.

The agent uses issues as an action log and todo list. Issues can be created by the user or agent.

### 7.4 REMOVED

### 7.5 Local-First, Migration-Friendly

The initial implementation is local-first with SQLite, but the schema and repository patterns should not prevent future migration to PostgreSQL.

Avoid unnecessary SQLite-specific behaviour unless clearly justified.

---

## 8. Database Schema

### 8.1 Requirements

The `requirements` table stores the current state of each requirement.

Fields:

- `id`
- `title`
- `requirement_statement`
- `type_code`
- `status_code`
- `version`
- `author`
- `date_created`
- `date_updated`
- `extended_description`
- `users`
- `triggers`
- `preconditions`
- `postconditions`
- `inputs`
- `outputs`
- `business_logic`
- `exception_handling`
- `acceptance_criteria`

Structured list-like fields may initially be stored as JSON columns. If they become heavily queried, they should be normalised later.

---

### 8.2 Requirement Changes

> Any change made to the requirement, both using the MCP (agent) or Gradio (human) must be logged into the `requirements_changes` table

The `requirements_changes` table stores all requirement updates.

Fields:

- `id`
- `requirement_id`
- `change_description`
- `diff`
- `author`
- `date`

The `diff` field must be machine-readable JSON.

Example:

```json
{
  "status_code": {
    "from": "draft",
    "to": "approved"
  },
  "acceptance_criteria": {
    "from": ["Valid credentials log the user in"],
    "to": [
      "Valid credentials log the user in",
      "Invalid credentials show a clear error message"
    ]
  }
}
```

---

### 8.3 Requirement Statuses

The `requirement_statuses` table stores lifecycle metadata.

Fields:

- `code`
- `label`
- `description`
- `is_terminal`
- `sort_order`

Default statuses, see `pacakges/requirements_mcp/src/requirements/_status.py`

---

### 8.4 Requirement Types

The `requirement_types` table stores type metadata.

Fields:

- `code`
- `key`
- `label`
- `description`
- `sort_order`

Default types - see `pacakges/requirements_mcp/src/requirements/_type.py`

---

## 9. Issues Subsystem

### 9.1 Issues

The `issues` table stores unresolved concerns, risks, blockers, ambiguities, decisions, and action items.

Fields:

- `id`
- `title`
- `description`
- `issue_type_code`
- `status_code`
- `priority_code`
- `impact`
- `risk`
- `proposed_resolution`
- `owner`
- `created_by`
- `date_created`
- `date_updated`
- `date_closed`

---

### 9.2 Issue Updates

The `issue_updates` table stores the progress history, audit trail, and action log for each issue.

Fields:

- `id`
- `issue_id`
- `update_type_code`
- `description`
- `diff`
- `action_taken`
- `action_result`
- `author`
- `date`

Issue updates must be created, for example, when:

- An issue is created.
- An issue status changes.
- An email is sent.
- An email is received.
- Evidence is added.
- A linked requirement is updated.
- A stakeholder question is asked.
- A resolution is proposed.
- An issue is resolved.
- An issue is reopened.


---

### 9.3 Issue Statuses

The `issue_statuses` table stores issue lifecycle metadata.

Fields:

- `code`
- `label`
- `description`
- `is_terminal`
- `sort_order`

Default statuses:

| Code | Label | Terminal |
|---|---|---:|
| `open` | Open | No |
| `triaged` | Triaged | No |
| `needs_clarification` | Needs Clarification | No |
| `waiting_for_stakeholder` | Waiting for Stakeholder | No |
| `in_progress` | In Progress | No |
| `blocked` | Blocked | No |
| `resolved` | Resolved | No |
| `closed` | Closed | Yes |
| `reopened` | Reopened | No |
| `cancelled` | Cancelled | Yes |

`resolved` means the agent believes the issue has been addressed. `closed` means no further action is required.

---

### 9.4 Issue Types

The `issue_types` table stores issue type metadata.

Fields:

- `code`
- `key`
- `label`
- `description`
- `sort_order`

Default issue types:

| Code | Key | Label |
|---|---|---|
| `AMB` | `ambiguity` | Ambiguity |
| `GAP` | `missing_information` | Missing Information |
| `CNF` | `conflict` | Conflict |
| `RSK` | `risk` | Risk |
| `BLK` | `blocker` | Blocker |
| `QST` | `stakeholder_question` | Stakeholder Question |
| `DEC` | `decision_needed` | Decision Needed |
| `EVD` | `evidence_needed` | Evidence Needed |
| `VAL` | `validation_issue` | Validation Issue |
| `CHG` | `change_request` | Change Request |
| `MSC` | `miscellaneous` | Miscellaneous, other |

---

### 9.5 Issue Priorities

The `issue_priorities` table stores priority metadata.

Fields:

- `code`
- `label`
- `description`
- `severity_order`
- `sort_order`

Default priorities:

| Code | Label | Severity |
|---|---|---:|
| `LOW` | Low | 10 |
| `MED` | Medium | 20 |
| `HIG` | High | 30 |
| `CRT` | Critical | 40 |

---

### 9.6 Requirement-Issue Links

The `requirement_issues` table links issues to requirements.

> A single issue can relate to multiple requirements. 

Fields:

- `requirement_id`
- `issue_id`
- `link_type`
- `rationale`
- `date_created`

Possible link types:

- `related`
- `blocks`
- `clarifies`
- `conflicts_with`
- `risk_for`
- `caused_by`
- `resolved_by`

---

## 10. REMOVED
---

## 11. MCP Tool Requirements

The `requirements_mcp` server must expose narrow, validated tools.

> Any changes to the requirements tables, must be documented in `requiremens_changes` this must be implemneted as a step in tool, that is when `create_requirement` or `update_requirement` is called by the MCP or Gradio UI then the change is automativcally logged in the the `requirements_changes` table. 

Logging with loguru should be implemented, daily logs to be saved to `logs` dir and output to stdout.

### 11.1 Requirement Tools

Required tools:

- `create_requirement`
- `update_requirement`
- `get_requirement`
- `search_requirements`
- `list_requirement_changes`
- `list_requirement_statuses`
- `list_requirement_types`

### 11.2 Issue Tools

Required tools:

- `create_issue`
- `update_issue`
- `add_issue_update`
- `get_issue`
- `search_issues`
- `list_issue_updates`
- `list_open_issues`
- `list_blocking_issues`
- `link_issue_to_requirement`
- `unlink_issue_from_requirement`

### 11.3 REMOVED

### 11.4 Prohibited Tools

The MCP must not expose:

- `run_sql`
- `execute_sql`
- unrestricted filesystem tools
- shell execution tools
- arbitrary Python execution tools

---

## 12. Gradio Frontend Requirements

The Gradio frontend must support:

### Requirements

- Add requirement.
- Search requirements.
- View requirement details.
- Update requirement.
- View requirement change history.
- Filter by status.
- Filter by type.

### Issues

- Create issue.
- Search issues.
- View issue details.
- Update issue fields.
- Change issue status.
- Add issue update.
- Link issue to requirement.
- View issue updates.

### Evidence

- Add evidence record.
- Link evidence to issue.
- Link evidence to requirement.
- View linked evidence.

The Gradio frontend must call the same service/repository layer as the MCP tools. It must not implement separate database logic.

---

## 13. Agent Workflow Examples

### 13.1 Requirement Creation

1. Skill interviews stakeholder.
2. Skill formulates requirement.
3. Agent calls `create_requirement`.
4. MCP validates input.
5. MCP writes requirement.
6. MCP returns requirement ID.

### 13.2 Requirement Update from Stakeholder Reply

1. Agent receives stakeholder reply.
2. Agent creates evidence record for email.
3. Agent links evidence to issue.
4. Agent calls `update_requirement`.
5. MCP computes diff.
6. MCP updates requirement.
7. MCP writes `requirements_changes` row.
8. Agent calls `add_issue_update` explaining the requirement update.
9. Agent changes issue status if appropriate.

### 13.3 Issue as Todo Item

1. Agent detects missing information.
2. Agent creates issue with type `GAP`.
3. Agent links issue to affected requirement.
4. Agent sends email to stakeholder.
5. Agent logs `email_sent` issue update.
6. Later, stakeholder replies.
7. Agent logs `email_received` issue update.
8. Agent updates requirement.
9. Agent logs `requirement_changed` issue update.
10. Agent marks issue `resolved` or `closed`.

---

## 14. Database Initialisation

The `requirements_mcp` package must provide a database initialisation function and CLI command.

Responsibilities:

- Check whether SQLite file exists.
- Check whether required tables exist.
- Create schema if needed.
- Seed requirement statuses.
- Seed requirement types.
- Seed issue statuses.
- Seed issue types.
- Seed issue priorities.
- Seed evidence types.

The initialisation function must be idempotent.

Example command:

```bash
uv run --package requirements-mcp requirements-db-init --db ./data/requirements.db
```

---

## 15. Configuration

The MCP must accept database path configuration.

Supported configuration sources:

1. CLI argument.
2. Environment variable.
3. Default local path.

Priority order:

```text
CLI argument > environment variable > default
```

Default path:

```text
./data/requirements.db
```

---

## 16. Git and uv Management

Use a single Git repository and a single `uv.lock` file.

Commit:

- Agent configuration.
- Skills.
- Tool definitions.
- Hooks.
- Package code.
- Tests.
- `pyproject.toml` files.
- `uv.lock`.
- Documentation.

Do not commit:

- `.venv/`
- local SQLite databases
- `.env` files
- runtime logs
- cache folders

Recommended `.gitignore` entries:

```gitignore
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.mypy_cache/
*.egg-info/

.env
.env.*

data/*.db
data/*.sqlite
data/*.sqlite3

*.log
```

---

## 17. Security Requirements

The MCP is a security boundary.

The MCP must:

- Validate all inputs with Pydantic.
- Avoid unrestricted SQL tools.
- Avoid shell execution.
- Restrict database path handling.
- Preserve audit trails.
- Avoid silent data mutation.
- Avoid trusting agent-generated data without validation.

The agent must not be able to bypass MCP validation.

---

## 18. Testing Requirements

Tests must cover:

- Database initialisation.
- Seed data validation.
- Requirement creation.
- Requirement update diff creation.
- Requirement version incrementing.
- Requirement change history.
- Issue creation.
- Issue update logging.
- Issue status changes.
- Requirement-issue linking.
- Evidence creation.
- Evidence linking.
- Transaction rollback on failure.

Critical invariant:

> No meaningful update may occur without an audit/update record.

---

## 19. Acceptance Criteria

### Repository and Workspace

- The repo contains root-level agentic files and one package: `requirements_mcp`.
- `uv sync --all-packages` succeeds.
- `uv.lock` is committed.

### MCP Server

- MCP server starts locally over stdio.
- MCP exposes requirement, issue, and evidence tools.
- MCP validates all tool inputs.
- MCP does not expose raw SQL execution.

### Database

- Database initialises automatically if missing.
- Required tables are created.
- Controlled metadata is seeded idempotently.
- SQLite database files are not committed.

### Requirements

- A requirement can be created.
- A requirement can be updated.
- Updating a requirement increments version.
- Updating a requirement writes a `requirements_changes` record.
- Requirement changes contain structured JSON diffs.

### Issues

- An issue can be created.
- An issue can be linked to one or more requirements.
- An issue update can be added without changing issue fields.
- Issue field changes are logged in `issue_updates`.
- Issues can function as an agent todo/action log.

### Gradio

- Local Gradio frontend can add and search requirements.
- Local Gradio frontend can create and update issues.
- Local Gradio frontend can view audit/update history.
- All adittions and updates are autologged

---

## 20. Open Questions

These decisions should be deferred until implementation pressure justifies them:

- Whether acceptance criteria should become a separate table.
- Whether users, triggers, inputs, and outputs should remain JSON or be normalised.
- Whether issue updates should support threaded comments.
- Whether the requirements database should eventually move to PostgreSQL.
- Whether vector search should be added for semantic retrieval.
- How the email and other communication be handled.
- What scheduled actions should the agent take and how to proceed with them.

---

## 21. Implementation Priority

### Phase 1: Core Database and Seeds

- SQLAlchemy models.
- Pydantic seed models.
- Database initialisation.
- Requirement statuses and types.
- Issue statuses, types, and priorities.
- clear and transparent package structure
- code docmented with google docstrings.

### Phase 2: Requirement Tools

- Create requirement.
- Update requirement.
- Requirement diff logging.
- Search and get requirement by id, fulltext search.

### Phase 3: Issue Tools

- Create issue.
- Update issue.
- Add issue update.
- Link issue to requirement.
- Search open issues.

### Phase 4: Gradio Frontend

- Requirement UI.
- Issue UI.
- Evidence UI.
- Audit history views.

### Phase 5: Agent Integration

- Root tool config.
- Skill-to-MCP workflows.
- End-to-end agent scenario tests.

---

## 22. Core Principle

The `requirements_mcp` package is the persistent operational memory, audit system, issue tracker, evidence register, and requirements database for the agent.

The agent may reason and decide, but the MCP validates, persists, audits, and exposes the system of record.
