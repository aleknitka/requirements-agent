---
name: review-requirements
description: >
  Review requirements for completeness, gaps, conflicts, and coverage againstsuccess criteria. Use this skill when the user asks to "review requirements", "check for gaps", "are we missing any requirement types?", "do we have conflicts?", "are our requirements covering the success criteria?", "requirements health check", or before moving to the next project phase.
---

# Review Requirements Skill

Runs automated checks across the full requirements set and reports issues.

## Checks performed

- **Gaps:** Missing requirement types, requirements without descriptions/owners/FRET, open critical items
- **Conflicts:** Contradictory timing constraints on the same component, circular predecessor chains
- **Coverage:** Cross-references success criteria against requirement content

## Commands

```bash
python skills/review-requirements/scripts/review.py report    # full review (recommended)
python skills/review-requirements/scripts/review.py gaps      # gaps only
python skills/review-requirements/scripts/review.py conflicts # conflicts only
python skills/review-requirements/scripts/review.py coverage  # success criteria coverage
```

## After review
For each flagged issue, use `project-update` skill to fix requirements or
`project-init` skill to add missing success criteria.