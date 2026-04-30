---
name: project-init
description: >
    Create a new project. Use this skill whenever there are no projects in the `projects` directory or the user wants to start a new project, asks "can you create a project for me", wants to update project-level information (sponsor, phase, objectives, success criteria), or asks to list existing projects. The agent MUST interview the user to collect project metadata before calling `uv run init-project new`. Trigger on: "new project", "create project", "initialise project", "set up a project".
license: MIT
allowed-tools: Read Edit Grep Glob
metadata:
  author: aleksander nitka
  version: "1.0.0"
  category: requirements
---

# Project Init Skill
 
Creates or updates a project: SQLite DB + PROJECT.md and other directories in `projects/<slug>/`.

# Steps:

## 0. Get project slug
Ask user for a short 5-10 characters project slug (codename or shorthand). It will be used as a quick way to indetify the project. If user needs help come up with a project slug yourself after obtaining a short description of the project from the user.

## 1. Create project structure
If the directories do not exist, create them:
```
mkdir projects/<slug>
mkdir projects/<slug>/logs
mkdir projects/<slug>/notes
```

## 2. Interview checklist (run before `uv run init-project new`)
Conduct an interview with the user to gather the critical info about the project. Use `init-note-<date>.md` in `projects/<slug>/notes/` to capture information as they are being given by the user.

1. Project name and slug (if not given already)
2. One-paragraph objective
3. Business case — why are we doing this?
4. Success criteria (list of measurable outcomes)
5. Out of scope (explicit exclusions)
6. Project owner name and email
7. Sponsor name and email
8. Key stakeholders with roles (requestor/sponsor/approver/reviewer/informed)
9. Target dates (optional)
10. External links — Confluence, SharePoint, programme board (optional)

### 3. Create the DB
Once you gathered all information create a new project in the database:

```bash
uv run init-project new \
  --name "<n>" [--code "PROJ-25"] \
  [--phase discovery|definition|development|testing|deployment|operations|closed] \
  [--objective "<text>"] [--business-case "<text>"] \
  [--project-owner "<n>"] [--sponsor "<n>"] \
  [--success-criteria '["c1","c2"]'] [--out-of-scope '["o1"]'] \
  [--stakeholders '[{"name":"Alice","role":"sponsor","contact":"alice@co.com"}]'] \
  [--external-links '[{"system":"Confluence","label":"Charter","url":"..."}]']

```

## 4. Create PROJECT.md
Create a quick refenrece, human readable markdown summary of the project using the same information gathered. Create or update the `PROJECT.md` file in `projects/<slug>/`.

### Template for PROJECT.md
```
# <slug>

Phase: <phase>

## Objective
<objective summary>

## Business case
<business case summary>

## Contacts
- <list of all contacts with roles>

## Progress
- <date time> Project initiated on by <stakeholder>

## Metadata
- created: <date time>
- last updated: <date time>
```

## 5. Output
Returns `project_id`, `slug`, `db` path, and `md` path.
The slug is derived from the name and used as the directory and file prefix.
