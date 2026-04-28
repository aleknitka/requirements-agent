# Phase 0.5: Package Scaffold - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-26
**Phase:** 0.5-Package Scaffold
**Areas discussed:** Skill command surface, Agent fallback pattern, Docs toolchain, Pre-commit scope

---

## Skill Command Surface

| Option | Description | Selected |
|--------|-------------|----------|
| `uv run <entry-point>` | Uses installed entry points, uv already required | ✓ |
| `python -m requirements_agent_tools.<module>` | More portable, no entry-point install needed | |
| Wrapper stubs in skills/*/scripts/ | Backward-compatible shims, adds maintenance overhead | |

**User's choice:** `uv run <entry-point>`

| Option | Description | Selected |
|--------|-------------|----------|
| Remove scripts/ dirs entirely | Clean break, no dead directories | ✓ |
| Keep empty scripts/ dirs | Preserves gitagent convention | |

**User's choice:** Remove scripts/ dirs entirely

| Option | Description | Selected |
|--------|-------------|----------|
| Fix report.py.py in Phase 0.5 | Packaging cleanup, fits here | |
| Out of scope | Leave for later | |

**Notes:** User clarified this is already fixed — CLAUDE.md Known Issues is outdated.

| Option | Description | Selected |
|--------|-------------|----------|
| All 6 skills | Consistent — every SKILL.md uses same pattern | ✓ |
| Only moved scripts | Minimal change | |

**User's choice:** All skills use same package CLI from src/
**Notes:** "all skills should use the same package cli developed in src"

Additional questions:
- Document all sub-commands (not just top-level entry point) ✓
- Update CLAUDE.md to reflect new src/ structure ✓
- Full audit of all 6 skill dirs for stale content ✓

---

## Agent Fallback Pattern

| Option | Description | Selected |
|--------|-------------|----------|
| Python helper reads agent.yaml | agent_config.py module for runtime model selection | |
| Document only — no new code | Update CLAUDE.md with pattern explanation | ✓ |
| --model flag on CLI entry points | Add model override to CLI tools | |

**Notes:** User was unsure what "establish the agent fallback pattern" referred to. Resolved as: verify agent.yaml fallback list is correct, add comment in CLAUDE.md explaining the gitagent pattern — no new code.

---

## Docs Toolchain

| Option | Description | Selected |
|--------|-------------|----------|
| docs/ committed to repo | Versioned alongside code, readable on GitHub | ✓ |
| docs/ gitignored | Always rebuilt from source | |
| No docs/ dir | In-editor docstrings only | |

| Option | Description | Selected |
|--------|-------------|----------|
| HTML | pdoc default, browsable | |
| Markdown | Better GitHub rendering | |
| Both | HTML + Markdown output | ✓ |

**User's choice:** Both HTML and Markdown

| Option | Description | Selected |
|--------|-------------|----------|
| Full package | All public modules including db/ | ✓ |
| Public API only | Skip private/internals | |

| Option | Description | Selected |
|--------|-------------|----------|
| pyproject.toml dev dependency | Pinned, reproducible | ✓ |
| uvx pdoc (ephemeral) | No pinning, always latest | |

---

## Pre-commit Scope

**User's choice:** ruff format + ruff check, pdoc doc regeneration, pytest on commit, ty type checks, bandit, detect-private-key, interrogate at 90% docstring coverage.

**Notes:** User specified `ty` (Astral's type checker, not mypy). "documentation" clarified as `interrogate` with 90% threshold. All hooks run on commit, not push-only.

---

## Claude's Discretion

None — all areas had explicit user decisions.

## Deferred Ideas

None — discussion stayed within phase scope.
