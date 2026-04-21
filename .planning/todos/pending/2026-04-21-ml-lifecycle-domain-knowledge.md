---
created: 2026-04-21T00:00:00
title: ML lifecycle domain knowledge for requirement elicitation
area: general
files:
  - shared/models.py
  - skills/refine-requirements/references/fret_grammar.md
---

## Problem

The agent elicits requirements generically. For ML/AI projects it lacks awareness of the ML lifecycle, meaning it will not prompt for — and may not even recognise — requirements that are essential in this domain:

- **Data quality**: requirements on input data distributions, missing value thresholds, schema contracts
- **Labeling**: annotation guidelines, inter-annotator agreement thresholds, label schema versioning
- **Model cards**: documentation requirements (intended use, out-of-scope uses, evaluation results, caveats)
- **Drift monitoring**: requirements on detecting covariate/concept drift and alerting thresholds
- **Retraining triggers**: conditions under which a model must be retrained (schedule, metric degradation, data volume)

Without this domain knowledge, the agent will miss whole classes of ML-specific requirements, leaving gaps that are only discovered at deployment or audit time.

## Solution

TBD — v2 feature. Possible approach:
- Add a `RequirementType` sub-taxonomy for ML lifecycle stages: `data_quality`, `labeling`, `model_governance`, `monitoring`, `retraining`
- Add ML-specific elicitation prompts to the `refine-requirements` skill: when `project.domain == "ml"`, ask domain-specific probing questions per lifecycle stage
- Provide a reference document (`skills/refine-requirements/references/ml_lifecycle.md`) analogous to `fret_grammar.md` that guides the agent on ML-specific requirement patterns
- Optionally integrate model card schema (Hugging Face / Google standard) as a structured output format for model governance requirements
