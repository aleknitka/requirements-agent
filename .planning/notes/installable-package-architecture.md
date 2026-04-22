---
title: Installable package architecture + agent resilience via rendered docs
date: 2026-04-22
context: Phase 0 planning session — explore conversation
---

# Installable Package Architecture

## The Problem

All skill scripts currently live in `skills/<name>/scripts/` and bootstrap their own imports via `sys.path.insert(0, str(_ROOT / "shared"))`. This causes:

- Path-hacking in every script — fragile and non-idiomatic Python
- No clean testability — scripts can't be imported as a module without side effects
- No code reuse across skills — each script is a standalone island
- No documentation — no machine-readable surface area for the agent to introspect

## The Design

Move all skill script logic into `tools/src/requirements_agent/` — an installable Python package. `uv sync` installs it when the agent initiates.

```
tools/
  src/
    requirements_agent/
      __init__.py
      init.py          # project initialisation logic
      elicit.py        # elicitation logic
      refine.py        # FRET refinement logic
      report.py        # reporting logic
      db.py            # (re-exported from shared, or merged)
      models.py
      ...
  pyproject.toml       # package definition
```

Skill scripts become thin entry points:
```python
# skills/project-init/scripts/init.py
from requirements_agent.init import cmd_new, cmd_list
```

Or skills invoke the package CLI directly:
```bash
uv run requirements-agent init new --name "My Project"
```

## Agent Resilience via Rendered Docs

**The fallback chain when the agent hits a CLI error:**

1. Read the error message (CLI must produce clear, actionable errors)
2. If still stuck → read `docs/api/<module>.md` (committed, always current)
3. Self-correct invocation based on current documented API

**Rendering pipeline:**

- Google-style docstrings throughout the package
- pdoc (or mkdocs with mkdocstrings) renders `docs/api/` on every commit
- Pre-commit hook: `pdoc requirements_agent --output-dir docs/api/`
- `docs/api/` is committed — agent can read it with file tools

**SKILL.md template update:**

Every SKILL.md should include a `## Fallback` section:
```markdown
## Fallback
If a tool call fails, read `docs/api/requirements_agent/<module>.md` for the current API.
```

## Why This Matters

SKILL.md files describe the agent's interface to the tools. If the package changes and SKILL.md isn't updated, the agent will follow valid instructions that produce errors. The rendered-docs fallback breaks this dependency — the agent can recover from drift without human intervention.

Proactive drift detection (CI check that compares SKILL.md against package API) is a future concern — see seed: skill-contract-testing.
