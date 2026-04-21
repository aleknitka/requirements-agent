---
created: 2026-04-21T00:00:00
title: Requirement-level external system links
area: general
files:
  - shared/models.py
  - shared/db.py
---

## Problem

`ExternalLink` exists on `ProjectMeta` (project-level), but individual requirements have no foreign keys to external systems. This means:
- A requirement cannot be directly linked to the Jira ticket that implements it
- No connection to GitHub issues, PRs, or milestones that satisfy the requirement
- No link to Confluence pages that elaborate the requirement context
- No pointer to MLflow experiment runs that validate a ML-specific requirement
- No reference to data catalog entries (e.g., Datahub, OpenMetadata) that define the data the requirement operates on

Without requirement-level links, the agent is an island — it cannot participate in existing engineering workflows or provide clickable cross-references in status reports.

## Solution

TBD — v2 feature. Possible approach:
- Add `external_links: list[ExternalLink]` to `RequirementRow` (model already has `ExternalLink` defined)
- Extend DB schema with a `req_external_links` table (req_id FK + system + label + url)
- Expose in `refine.py` as `--link <system> <url>` flag and interactively during elicitation
- Surface clickable links in `status-report` output and `PROJECT.md`
- For MLflow: consider a dedicated `mlflow_run_id` typed field so experiment → requirement traceability is first-class
- For Jira/GitHub: consider webhook or polling sync to auto-update requirement status when linked ticket closes
