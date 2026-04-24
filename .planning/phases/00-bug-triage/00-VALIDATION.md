---
phase: 0
slug: bug-triage
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-22
---

# Phase 0 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (version per uv.lock) |
| **Config file** | none detected (use default discovery) |
| **Quick run command** | `uv run pytest tests/ -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 00-01-01 | 01 | 1 | BUG-01 | — | N/A | smoke | `uv run python -c "import shared.db"` | N/A (shell) | ⬜ pending |
| 00-01-02 | 01 | 1 | BUG-03 | — | N/A | unit | `uv run pytest tests/test_db.py::test_list_projects -x` | ❌ W0 | ⬜ pending |
| 00-01-03 | 01 | 1 | BUG-04 | — | N/A | unit | `uv run pytest tests/test_db.py::test_get_project_by_slug -x` | ❌ W0 | ⬜ pending |
| 00-02-01 | 02 | 1 | BUG-05 | — | N/A | unit | `uv run pytest tests/test_models.py::test_requirement_in_instantiation -x` | ❌ W0 | ⬜ pending |
| 00-02-02 | 02 | 1 | BUG-05 | — | N/A | unit | `uv run pytest tests/test_models.py::test_no_fret_fields -x` | ❌ W0 | ⬜ pending |
| 00-03-01 | 03 | 1 | BUG-02 | — | N/A | subprocess | `uv run python skills/new-project-initiation/scripts/init.py --help` | N/A (shell) | ⬜ pending |
| 00-05-01 | 05 | 1 | BUG-07 | — | N/A | subprocess | `uv run python skills/refine-requirements/scripts/refine.py --help` | N/A (shell) | ⬜ pending |
| 00-06-01 | 06 | 1 | BUG-08 | — | N/A | unit | `uv run pytest tests/test_db.py::test_slug_column -x` | ❌ W0 | ⬜ pending |
| 00-07-01 | 07 | 2 | BUG-09 | — | N/A | subprocess | `uv run python skills/status-report/scripts/report.py --help` | N/A (shell) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_db.py` — covers BUG-03 (list_projects), BUG-04 (get_project_by_slug), BUG-08 (slug column); uses `tmp_path` + real sqlite3 connections
- [ ] `tests/test_models.py` — covers BUG-05 (RequirementIn instantiation), D-05 (no fret fields)
- [ ] `tests/test_init.py` — REPLACE existing MagicMock file with real-SQLite subprocess tests (D-15/D-16)

*The current `tests/test_init.py` uses MagicMock and must be replaced, not updated.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `uv run pytest` full suite green | All BUG-* | Final integration gate | Run after all waves complete |
