---
name: project-init
description: >
    Create a new project. Use this skill whenever there are no projects in the `projects` directory or the user wants to start a new project, asks "can you create a project for me", wants to update project-level information (sponsor, phase, objectives, success criteria), or asks to list existing projects. The agent MUST interview the user to collect project metadata before calling `uv run init-project new`. Trigger on: "new project", "create project", "initialise project", "set up a project", "update project details", "change project phase", "list projects".
license: MIT
allowed-tools: Read Edit Grep Glob
metadata:
  author: aleksander nitka
  version: "1.0.0"
  category: requirements
---

# Project Init Skill
 
Creates or updates a project: SQLite DB + PROJECT.md in `projects/<slug>/`.
 
## Interview checklist (run before `uv run init-project new`)
 
Collect ALL of these before creating:
1. Project name and slug (e.g. MLPLAT-25)
2. One-paragraph objective
3. Business case — why are we doing this?
4. Success criteria (list of measurable outcomes)
5. Out of scope (explicit exclusions)
6. Project owner name and email
7. Sponsor name and email
8. Key stakeholders with roles (requestor/sponsor/approver/reviewer/informed)
9. Target dates (optional)
10. External links — Confluence, SharePoint, programme board (optional)

## Commands
 
```bash
# Create
uv run init-project new \
  --name "<n>" [--code "PROJ-25"] \
  [--phase discovery|definition|development|testing|deployment|operations|closed] \
  [--objective "<text>"] [--business-case "<text>"] \
  [--project-owner "<n>"] [--sponsor "<n>"] \
  [--success-criteria '["c1","c2"]'] [--out-of-scope '["o1"]'] \
  [--stakeholders '[{"name":"Alice","role":"sponsor","contact":"alice@co.com"}]'] \
  [--external-links '[{"system":"Confluence","label":"Charter","url":"..."}]']

# List all projects
uv run init-project list

# Update metadata
uv run init-project update \
  --project "<slug or name>" [--phase ...] [--objective ...] [--business-case ...] \
  [--project-owner ...] [--sponsor ...] [--start-date ...] [--target-date ...] \
  [--actual-end-date ...] [--status-summary ...] [--success-criteria ...] \
  [--out-of-scope ...] [--stakeholders ...] [--external-links ...]
```
 
## Output
Returns `project_id`, `slug`, `db` path, and `md` path.
The slug is derived from the name and used as the directory and file prefix.
