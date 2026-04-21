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
metadata:
  author: aleksander nitka
  version: "1.0.0"
  category: requirements
---

# Project Update Skill

CRUD for requirements. All writes validated through Pydantic, logged in updates table.

## Session start
```bash
# If project is ambiguous, resolve first:
python skills/project-init/scripts/init.py list
```
Pass `--project <slug>` to all commands, or omit if only one project exists.

## Commands

```bash
# Add (status defaults to 'open' — no removal, change status instead)
python skills/project-update/scripts/req_ops.py add \
  --title "..." --by "<agent/user>" \
  --type CORE|DATA|MODEL|INFRA|OPS|UX|COMPLIANCE \
  [--description "..."] [--priority low|medium|high|critical] \
  [--owner "..."] [--tags "tag1,tag2"] \
  [--stakeholders '[{"name":"Alice","role":"approver"}]'] \
  [--predecessors '[{"kind":"internal","ref":"REQ-INFRA-XXXX"}]'] \
  [--dependencies '[{"kind":"external","ref":"Kafka v3","url":"..."}]'] \
  [--external-links '[{"system":"Jira","label":"PROJ-42","url":"..."}]']

# Update
python skills/project-update/scripts/req_ops.py update \
  --id REQ-DATA-XXXX --by "<n>" --summary "<why>" \
  [--status open|in-progress|done|rejected] [--priority ...] [...]

# Read
python skills/project-update/scripts/req_ops.py get     --id REQ-DATA-XXXX
python skills/project-update/scripts/req_ops.py list    [--type DATA] [--status open] [--has-fret] [--no-fret]
python skills/project-update/scripts/req_ops.py search  --query "<keyword>"
python skills/project-update/scripts/req_ops.py history --id REQ-DATA-XXXX
python skills/project-update/scripts/req_ops.py vector  --query "<natural language>" [--top-k 10]
```

## Requirement types → IDs
CORE · DATA · MODEL · INFRA · OPS · UX · COMPLIANCE → REQ-<TYPE>-<8HEX>

Full snapshot written to updates table on status transitions: in-progress, done, rejected.
