---
created: 2026-04-21T00:00:00
title: VCS and CI bidirectional linkage
area: general
files:
  - shared/models.py
  - shared/db.py
  - hooks/hooks.yaml
---

## Problem

The agent manages requirements in isolation from the engineering workflow. There is no active integration with VCS or CI systems:

- GitHub/GitLab issues are not automatically associated with requirement IDs — engineers must manually maintain the link in both systems
- PR descriptions have no structured field for `Satisfies: REQ-xxx`, so there is no machine-readable signal that a PR delivers a requirement
- CI test results (pass/fail, coverage) are not fed back to update requirement verification status in the DB
- Requirement status (`draft` → `verified`) cannot advance automatically when a linked PR merges and its tests pass

This means the requirements DB diverges from actual delivery state over time and cannot be used as a reliable source of truth for project status.

## Solution

TBD — v3 feature. Possible approach:
- Add a GitHub/GitLab webhook listener (or polling hook in `hooks/hooks.yaml`) that watches for PR merge events and parses `Satisfies: REQ-xxx` in PR descriptions
- On merge + green CI: auto-transition linked requirements from `implemented` → `verified` in the DB, with a `UpdateRecord` capturing the PR URL and commit SHA
- Provide a PR description template (`.github/pull_request_template.md`) that prompts engineers to fill in `Satisfies:` fields
- For CI: parse test result XML/JSON (JUnit, pytest) and match test names against Gherkin scenarios linked to requirement IDs — update `verification_evidence` field
- Surface unverified requirements (implemented but no green CI) in `status-report`
