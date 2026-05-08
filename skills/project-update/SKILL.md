---
name: project-update
description: >
  Add or update requirements in a project, search them, and view change history.
  Use this skill for: "add a requirement", "update requirement status",
  "change priority", "assign owner", "add dependency", "link to Jira",
  "list open requirements", "show critical requirements", "search for X",
  "what changed on REQ-X?", "find requirements about Y". Requirements can never
  be deleted — only their status changed. All changes are logged with diffs.
  Also handles vector/semantic search when OPENAI_API_KEY is set.
license: MIT
allowed-tools: Read Edit Grep Glob
metadata:
  author: aleksander nitka
  version: "1.0.0"
  category: requirements
---

# Project Update Skill

CRUD for requirements. All writes validated through Pydantic, logged in updates table.

## Session start

Pass `--project <slug>` to all commands, or omit if only one project exists.

```bash
# If project is ambiguous, resolve first:
uv run init-project list
```

## Commands

```bash
# If project is ambiguous, resolve first:
uv run init-project list

# Add (status defaults to 'open' — no removal, change status instead)
uv run req-ops add [--project <slug>] \
  --title "..." --by "<agent/user>" \
  --type CORE|DATA|MODEL|INFRA|OPS|UX|COMPLIANCE \
  [--description "..."] [--priority low|medium|high|critical] \
  [--owner "..."] [--tags "tag1,tag2"] \
  [--stakeholders '[{"name":"Alice","role":"approver"}]'] \
  [--predecessors '[{"kind":"internal","ref":"REQ-INFRA-XXXX"}]'] \
  [--dependencies '[{"kind":"external","ref":"Kafka v3","url":"..."}]'] \
  [--external-links '[{"system":"Jira","label":"PROJ-42","url":"..."}]']

# Update
uv run req-ops update [--project <slug>] \
  --id REQ-DATA-XXXX --by "<n>" --summary "<why>" \
  [--status open|in-progress|done|rejected] [--priority ...]

# Read
uv run req-ops get     [--project <slug>] --id REQ-DATA-XXXX
uv run req-ops list    [--project <slug>] [--type DATA] [--status open] [--has-fret] [--no-fret]
uv run req-ops search  [--project <slug>] --query "<keyword>"
uv run req-ops history [--project <slug>] --id REQ-DATA-XXXX
uv run req-ops vector  [--project <slug>] --query "<natural language>" [--top-k 10]
```

## Requirement types → IDs
CORE · DATA · MODEL · INFRA · OPS · UX · COMPLIANCE → REQ-<TYPE>-<8HEX>

Full snapshot written to updates table on status transitions: in-progress, done, rejected.
