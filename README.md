# Requirements Agent 🤖

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Requirements Agent** is an enterprise-grade autonomous agent for managing software and AI project requirements, meetings, and status reporting. Built for Data Science, ML, and AI projects where specialized requirement engineering might be absent, it provides a rigorous, auditable, and searchable source of truth.

---

## 🎯 Why this Project?

In the fast-paced world of AI and Data Science, the "Requirements Gap" is a frequent cause of project failure. Data Scientists often focus on model performance metrics while business stakeholders focus on high-level outcomes, leaving a void where technical constraints, data privacy requirements, and operational edge cases should live.

### The Problem
- **Ambiguity**: Requirements like "the model should be fast" are untestable and lead to scope creep.
- **Fragmented Truth**: Decisions are buried in Slack threads, emails, and meeting notes, making auditability impossible.
- **Missing Engineering Rigor**: Unlike traditional software, AI requirements often involve complex data dependencies that are frequently overlooked.

### The Solution: The Requirements Agent
This tool acts as a **Digital Requirements Engineer** that bridges the gap between stakeholders and implementation teams. It doesn't just store text; it enforces a lifecycle of discovery, refinement, and validation.

### Core Value Add
1. **Eliminate Assumptions**: The agent is designed to be "relentless in pursuit of clarity," forcing the translation of vague desires into testable statements.
2. **Regulatory & Audit Readiness**: By logging every change with a diff and a reason, it provides a "Black Box" for project decisions—essential for high-risk AI applications in finance, healthcare, and infrastructure.
3. **Automated Synthesis**: It reduces the administrative overhead of requirement management by automatically extracting decisions from meeting minutes and generating comprehensive status reports.
4. **Hybrid Intelligence**: Combines traditional keyword search with semantic (vector) understanding, allowing teams to find related requirements even when they use different terminology.

---

## 🌟 Key Features

- **Multi-Project Management**: Isolated environments using unique project `slugs`.
- **Hybrid Search**: Keyword and semantic (vector) search powered by `sqlite-vec`.
- **Auditable History**: Every change is logged with a diff and metadata (who, when, why).
- **Meeting Intelligence**: Log minutes, extract decisions, and track action items linked to requirements.
- **Automated Reporting**: Generate comprehensive project status reports in JSON and Markdown.
- **Pydantic Validation**: Strong typing and validation for all data models.
- **Extensible Roadmap**: Designed for future integration with Slack, MS Teams, and formal methods like FRET.

---

## 🏗️ Core Concepts

### 📂 Project Structure
Each project lives in its own directory under `projects/<slug>/`:
- `<slug>.db`: A SQLite database containing requirements, meetings, updates, issues, and vector embeddings.
- `PROJECT.md`: A human-readable summary of project aims, stakeholders, and progress.
- `logs/`: Daily operational logs.

### 🗃️ Database Schema
The agent maintains several key tables:
- `projects`: Metadata about the project (owner, sponsor, objectives).
- `requirements`: The core requirements (Functional, Non-Functional, Data, etc.).
- `updates`: A full audit trail of every requirement change.
- `meeting_minutes`: Records of meetings, attendees, and summaries.
- `decisions`: Key decisions made during meetings, linked to requirements.
- `action_items`: Tasks arising from meetings with owners and due dates.
- `issues`: Todos for the agent and coworkers.

---

## 🛡️ Core Principles & Guardrails

The Requirements Agent operates under a strict set of rules to ensure data integrity and auditability:

- **Soft-Delete Only**: Requirements are never hard-deleted from the database. They are marked as `removed` to maintain a full history.
- **Audit Traceability**: Every modification must be accompanied by a reason and is logged in the `updates` table with a before/after diff.
- **Human-in-the-Loop (HITL)**: Destructive operations (like archiving a project or bulk-modifying statuses) require explicit human confirmation and a stated reason.
- **No Ambiguity**: The agent is designed to be relentless in pursuit of clarity, asking clarifying questions until all assumptions are eliminated.
- **Regulatory Readiness**: Built with compliance in mind, ensuring all decisions have a reasoning trace for audit purposes.

---

## 🚀 Installation

The project uses `uv` for lightning-fast dependency management.

```bash
# Clone the repository
git clone https://github.com/aleksander-nitka/requirements-agent.git
cd requirements-agent

# Create virtual environment and install dependencies
uv sync
```

### Dependencies
- **Core**: `click`, `pydantic`, `sqlite-vec`, `loguru`, `openai` (for embeddings).
- **Dev**: `pytest`, `ruff`, `lazydocs`.

---

## 🛠️ CLI Toolset Reference

The agent relies on several specialized CLI tools, exposed as scripts via `pyproject.toml`.

### 1. `init-project` — Project Management
Used to create and manage project metadata.
```bash
# Create a new project
init-project new --name "AI Customer Service" --owner "Jane Doe" --phase discovery

# List all projects
init-project list

# Update project metadata
init-project update --project ai-customer-service --sponsor "John Smith"
```

### 2. `req-ops` — Requirement Operations
The primary tool for managing the requirements lifecycle.
```bash
# Add a requirement
req-ops add --project ai-customer-service --title "Login API" --type functional --priority high --by "Alice"

# Search requirements
req-ops search --project ai-customer-service --status open --priority critical

# Semantic search (requires embeddings)
req-ops vector --project ai-customer-service --query "authentication and security" --top-k 3

# View requirement history
req-ops history --project ai-customer-service --id <req_id>
```

### 3. `meeting` — Meeting Management
Capture minutes and extract actionable data.
```bash
# Log a meeting
meeting log --project ai-customer-service --title "Architecture Review" --by "Alice" \
  --decisions '[{"title": "Use OAuth2", "decision_id": "D1"}]' \
  --action-items '[{"title": "Draft security spec", "owner": "Bob"}]'

# List decisions
meeting decisions --project ai-customer-service --status open
```

### 4. `refine` — Requirement Refinement
Interactive FRET (Formal Requirements Elicitation Tool) refinement.
```bash
# List requirements needing refinement
refine pending --project ai-customer-service

# Apply a FRET statement to a requirement
refine apply --project ai-customer-service --id <req_id> \
  --fret-statement "WHEN user is logged in SHALL allow access" --by "Alice"
```

### 5. `review` — Quality Assurance
Gap analysis and conflict detection.
```bash
# Identify missing requirement types and incomplete fields
review gaps --project ai-customer-service

# Detect potential conflicts between requirements
review conflicts --project ai-customer-service

# Cross-check requirements against success criteria
review coverage --project ai-customer-service
```

### 6. `report` — Status Reporting
Generate project health snapshots.
```bash
# Generate a report to stdout
report generate --project ai-customer-service

# Save a timestamped report to the project folder
report save --project ai-customer-service
```

### 7. `db` — Direct Database Access
A Click-based CLI for granular CRUD operations.
```bash
db --project ai-customer-service req show --id <id>
db --project ai-customer-service project show
```

---

## 📈 Roadmap

### Phase 1: Foundation (Current)
- [x] Robust SQLite + `sqlite-vec` storage.
- [x] Full CLI coverage for Projects, Requirements, and Meetings.
- [x] Basic reporting and audit logging.
- [x] Pydantic model integration.

### Phase 2: Intelligence & Issues
- [ ] Automated review of requirements for ambiguity.
- [ ] Dedicated `ISSUES` table for stakeholder follow-ups.
- [ ] Introduction of formalization methods (FRET).

### Phase 3: Autonomous Ingestion
- [ ] Ingest unstructured data from PDF, TXT, and MD.
- [ ] Autonomous "Daily Wake-up" tasks for research and ideation.
- [ ] Evidence linking in the database.

### Phase 4: Enterprise Integration
- [ ] Slack, MS Teams, and Telegram listeners.
- [ ] Real-time summarization of multi-user conversations.
- [ ] Advanced audit trials for distributed decisions.

---

## 🧪 Development

### Running Tests
```bash
uv run pytest
```

### Linting & Formatting
We use `ruff` for code quality.
```bash
uv run ruff check .
uv run ruff format .
```

### Documentation
API documentation is generated via `lazydocs` and stored in the `docs/` directory.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
