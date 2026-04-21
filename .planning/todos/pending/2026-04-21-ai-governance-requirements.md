---
created: 2026-04-21T00:00:00
title: AI governance requirement elicitation and classification
area: general
files:
  - shared/models.py
  - compliance/risk-assessment.md
---

## Problem

AI governance is a mandatory concern for production ML/AI systems, but the agent has no structured support for eliciting or classifying governance requirements. Specific gaps:

- **Fairness**: no prompts for protected attribute handling, demographic parity, equalised odds thresholds
- **Explainability (XAI)**: no requirements scaffolding for SHAP/LIME outputs, counterfactual explanations, or audit trails for individual decisions
- **Bias auditing**: no structured requirement type for pre-deployment bias tests or ongoing disparity monitoring
- **EU AI Act risk tiers**: no awareness of high-risk AI system categories (Annex III) that trigger mandatory conformity assessments, transparency obligations, and human oversight requirements
- **Model registry compliance**: no requirements linking a model to its registry entry, approval workflow, or deployment gate criteria

Without this, the agent will produce technically complete requirements that are non-compliant with emerging regulation, creating legal and reputational risk for enterprise adopters.

## Solution

TBD — v2/v3 feature. Possible approach:
- Add `RequirementType` values: `fairness`, `explainability`, `bias_audit`, `regulatory_compliance`
- Add `risk_tier` field to `ProjectMeta`: `minimal`, `limited`, `high`, `unacceptable` (EU AI Act tiers)
- When `risk_tier == "high"`, automatically inject governance requirement templates during elicitation (transparency, human oversight, robustness, accuracy logging)
- Add a `compliance/eu_ai_act.md` reference document alongside existing `compliance/risk-assessment.md`
- Surface governance coverage gaps in `status-report` (e.g., "0 of 4 mandatory high-risk requirements defined")
