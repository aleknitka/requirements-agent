---
phase: 1
slug: project-initialisation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-30
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_setup.py tests/test_db.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_setup.py tests/test_db.py -x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite green + all CLI help exits 0
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | INIT-01 | — | N/A | unit | `uv run pytest tests/test_setup.py::test_setup_creates_project_dir -x` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | INIT-01 | — | N/A | unit | `uv run pytest tests/test_setup.py::test_setup_creates_subdirs -x` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | INIT-02 | — | N/A | unit | `uv run pytest tests/test_setup.py::test_setup_bootstraps_db -x` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | INIT-02 | — | N/A | unit | `uv run pytest tests/test_db.py::test_projects_table_no_slug_column -x` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 1 | INIT-03 | T-V5 | Use `yaml.safe_load()` only | unit | `uv run pytest tests/test_setup.py::test_setup_writes_config_yaml -x` | ❌ W0 | ⬜ pending |
| 1-01-06 | 01 | 1 | INIT-04 | — | N/A | unit | `uv run pytest tests/test_setup.py::test_setup_interactive_prompts -x` | ❌ W0 | ⬜ pending |
| 1-01-07 | 01 | 1 | INIT-05 | — | N/A | unit | `uv run pytest tests/test_setup.py::test_setup_guard_on_second_run -x` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | INIT-06 | — | N/A | unit | `uv run pytest tests/test_setup.py::test_get_project_conn_opens_db -x` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | INIT-06 | — | N/A | unit | `uv run pytest tests/test_setup.py::test_get_project_conn_no_db -x` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 1 | INIT-06 | — | N/A | smoke | `uv run refine --help && uv run req-ops --help && uv run review --help && uv run report --help && uv run meeting --help` | ✅ | ⬜ pending |
| 1-04-01 | 04 | 2 | INIT-01–06 | — | N/A | regression | `uv run pytest` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_setup.py` — new file; stubs for INIT-01 through INIT-06 (all tests in Wave 0 column above)
- [ ] `tests/test_db.py` lines ~100–118 — update stale `minutes` bootstrap SQL to remove `project_id` FK
- [ ] `tests/test_db.py` — remove slug-specific tests: `test_upsert_project_auto_derives_slug`, `test_upsert_project_preserves_explicit_slug`, `test_upsert_project_stores_slug_in_db`, `test_get_project_by_slug_*`, `test_slug_column_exists`
- [ ] `tests/test_slug_infrastructure.py` — DELETE entirely (fully obsolete)
- [ ] `tests/test_init.py` — REWRITE entirely for `cmd_setup()` (old `cmd_new()` tests invalid)
- [ ] `pyproject.toml` — add `pyyaml` as declared dependency (currently transitively available at 6.0.3 but undeclared)

*Existing pytest/conftest infrastructure is sufficient — no new framework installation needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `.gitignore` append is idempotent (no duplicate entries on second run) | INIT-03 | Requires filesystem state inspection across two runs | Run `uv run init-project setup` twice; `grep -c 'project/logs/' .gitignore` must equal 1 |
| Interactive prompt flow with real TTY (sqlite-vec and OTel prompts render correctly) | INIT-04 | TTY interaction cannot be fully automated in pytest | Run `uv run init-project setup` manually in a terminal; verify all 3 prompts appear in order |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
