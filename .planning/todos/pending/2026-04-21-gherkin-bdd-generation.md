---
created: 2026-04-21T00:00:00
title: Gherkin/BDD auto-generation from requirements
area: general
files:
  - shared/models.py
  - shared/db.py
  - skills/refine-requirements/scripts/refine.py
---

## Problem

Requirements stored in the DB are formal (FRET statements) but not directly executable as tests. Gherkin (Given/When/Then) bridges the gap between a requirement and an acceptance test, but currently:
- No tooling exists to derive Gherkin scenarios from a `RequirementRow`
- Scenarios are not linked back to their parent requirement ID, so traceability from test → requirement is broken
- Stakeholders who use BDD toolchains (Cucumber, Behave, SpecFlow) have no export path

This is particularly important for ML/AI projects where "the system SHALL classify X with accuracy ≥ 0.95" needs to become a concrete test scenario with a defined dataset and threshold assertion.

## Solution

TBD — v2 feature. Possible approach:
- Add a `gherkin_scenarios` field (list of strings) to `RequirementRow`
- Post-refinement, offer an optional LLM pass: given the FRET statement, generate one or more Given/When/Then scenarios
- Store scenarios with a `req_id` foreign key so the link is explicit in the DB
- Add a `gherkin-export` sub-command to `refine.py` (or a new skill) that writes `.feature` files grouped by component
- For ML requirements, include dataset/threshold placeholders in the generated scenario template
