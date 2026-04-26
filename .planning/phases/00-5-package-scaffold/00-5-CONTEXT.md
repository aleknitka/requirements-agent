# Phase 0.5: Package Scaffold - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Solidify `requirements_agent_tools` as the canonical CLI package: update all skill command surfaces to use installed entry points, remove dead `scripts/` directories, add a documentation toolchain (pdoc + committed docs/), configure a comprehensive pre-commit pipeline, verify the agent.yaml fallback pattern, and update CLAUDE.md to reflect the new package structure.

The scripts-to-package move is already complete on disk. This phase cleans up everything that references the old layout.

</domain>

<decisions>
## Implementation Decisions

### Skill Command Surface
- **D-01:** All 6 skills invoke CLI tools via `uv run <entry-point>` — e.g. `uv run init-project new`, `uv run report generate`. No `python skills/*/scripts/` references anywhere.
- **D-02:** Remove `skills/*/scripts/` directories entirely — no stubs, no placeholders. Clean break.
- **D-03:** All 6 skills updated to use the package CLI entry points defined in `pyproject.toml [project.scripts]`.
- **D-04:** Each SKILL.md documents all sub-commands explicitly with exact `uv run` invocations — the agent must not need to run `--help` to discover sub-commands.
- **D-05:** Update `CLAUDE.md` to reflect the new `src/requirements_agent_tools/` structure, entry-point invocations, and remove the stale `shared/` references.
- **D-06:** Full audit of all 6 skill directories for stale content: empty `scripts/`, outdated `SKILL.md` command examples, broken `references/` files.
- **D-07:** Remove the `report.py.py` double-extension entry from CLAUDE.md Known Issues — already fixed.

### Agent Fallback Pattern
- **D-08:** Verify `agent.yaml` fallback model list is sensible (current: `openai/gpt-5.2`, `openai/gpt-oss-20b`, `google/gemma-4-31b`). Add a comment block in CLAUDE.md explaining the gitagent fallback pattern (harness reads `agent.yaml`, selects next model on failure). No new code required.

### Documentation Toolchain
- **D-09:** Add `pdoc` as a dev dependency: `uv add --dev pdoc`.
- **D-10:** Generate **both** HTML and Markdown output formats.
- **D-11:** Output destination: `docs/` directory, committed to the repo.
- **D-12:** Scope: full package — all public modules in `requirements_agent_tools` including the `db/` subpackage.
- **D-13:** Docstring style: **Google** (per README requirement). All new and updated functions must use Google-style docstrings.

### Pre-commit Pipeline
- **D-14:** `ruff format` + `ruff check` — formatting and lint enforcement.
- **D-15:** `pdoc` doc regeneration — regenerate `docs/` on every commit so docs stay in sync.
- **D-16:** `pytest` — run full test suite on commit. Fails commit if any test fails.
- **D-17:** `ty` type checking (Astral's ty, not mypy) — static type analysis.
- **D-18:** `bandit` — security scanning for common Python vulnerabilities.
- **D-19:** `detect-private-key` (from `pre-commit-hooks`) — prevents accidental credential commits.
- **D-20:** `interrogate` at **90%** docstring coverage threshold — fails if public functions are undocumented.

All hooks run on commit (not push-only).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Package Configuration
- `pyproject.toml` — entry points, build system (hatchling), current dependencies. Entry points: `init-project`, `refine`, `req-ops`, `review`, `report`, `meeting`, `db`.
- `agent.yaml` — model preferences, fallback list, skill registry.

### Skills to Update
- `skills/new-project-initiation/SKILL.md` — update to `uv run init-project`
- `skills/refine-requirements/SKILL.md` — update to `uv run refine`
- `skills/project-update/SKILL.md` — update to `uv run req-ops`
- `skills/review-requirements/SKILL.md` — update to `uv run review`
- `skills/status-report/SKILL.md` — update to `uv run report`
- `skills/meeting-agent/SKILL.md` — update to `uv run meeting`

### Agent Context Files
- `CLAUDE.md` — must be updated: remove `shared/` references, add `src/requirements_agent_tools/` docs, update commands, add agent fallback pattern explanation, remove fixed known issues.
- `README.md` — Google docstrings requirement; overall architecture reference.

### Package Source
- `src/requirements_agent_tools/` — all modules; full package source.
- `src/requirements_agent_tools/db/` — db subpackage.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/requirements_agent_tools/` — all modules already present; no new modules needed for this phase
- `pyproject.toml` — `[project.scripts]` already defines 7 entry points; `pdoc` and `pre-commit` just need to be added to `[project.optional-dependencies]` or `[dependency-groups]`
- `tests/` — existing test suite (`test_db.py`, `test_models.py`, `test_init.py`, `test_project_md.py`, etc.) already passing with 74 tests; pre-commit pytest hook runs these

### Established Patterns
- Commands run via `uv run` — consistent with CLAUDE.md `## Commands` section
- All tests use `uv run pytest` — pre-commit hook follows same pattern
- `ruff check .` + `ruff format .` — already the manual lint commands in CLAUDE.md; pre-commit formalises them

### Integration Points
- `pyproject.toml` — add dev deps (`pdoc`, `pre-commit`, `interrogate`, `bandit`, `ty`) and a `[tool.interrogate]` config section
- `.pre-commit-config.yaml` — new file; runs: `pre-commit-hooks` (detect-private-key), ruff, ty, bandit, interrogate, pdoc, pytest
- `docs/` — new directory; gitignore entry NOT needed (committed to repo)
- `CLAUDE.md` — update shared library section, commands section, known issues section

</code_context>

<specifics>
## Specific Ideas

- User confirmed `report.py.py` double-extension is already fixed — CLAUDE.md Known Issues only needs cleanup, not a fix task.
- User wants **all** sub-commands documented in SKILL.md (not just top-level entry point + `--help`).
- Pre-commit is comprehensive: 8 hooks covering format, lint, types, security, docs, tests, credentials.
- `ty` is the preferred type checker (Astral's new tool, not mypy).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 0.5-Package Scaffold*
*Context gathered: 2026-04-26*
