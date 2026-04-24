---
phase: 00-bug-triage
reviewed: 2026-04-23T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - shared/db.py
  - shared/models.py
  - shared/project_session.py
  - skills/new-project-initiation/scripts/init.py
  - skills/project-update/scripts/req_ops.py
  - skills/refine-requirements/scripts/refine.py
  - tests/test_db.py
  - tests/test_db_bugs.py
  - tests/test_models.py
  - tests/test_init.py
  - tests/test_slug_infrastructure.py
findings:
  critical: 0
  warning: 7
  info: 5
  total: 12
status: issues_found
---

# Phase 00: Code Review Report

**Reviewed:** 2026-04-23T00:00:00Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

This review covers the shared library (`db.py`, `models.py`, `project_session.py`) and three CLI skill scripts (`init.py`, `req_ops.py`, `refine.py`), plus the full test suite written for the Phase 0 bug-triage. The codebase is in a mid-fix state: several bugs documented in the triage research (BUG-01 through BUG-08) have already been addressed in the shared modules, but two callers (`init.py` and `req_ops.py`) still reference the deleted `db.list_all_projects()` function — a hard crash the moment either script is exercised. Beyond the pre-identified bugs, the review found additional warning-level issues in the production code: a project-ID mismatch risk in `vector_search`, a SQL injection risk from dynamic SQL construction in `update_requirement`, a post-delete dereference of the connection in `project_session.refresh_md`, an unhandled `None` return from `insert_minute`/`mark_integrated`, and a wrong `project_id` argument in `refine.py`'s `cmd_apply`.

---

## Warnings

### WR-01: `db.list_all_projects` called but does not exist — hard crash on `new` and `list`

**File:** `skills/new-project-initiation/scripts/init.py:49`
**Issue:** `cmd_new` calls `db.list_all_projects()` (a function that does not exist in `db.py`; the canonical name is `db.list_projects(conn)`). The same call pattern is also present inside `cmd_list` at line 85. Both commands will raise `AttributeError` at runtime. `db.list_projects` requires a `conn` argument that is also missing — the callers must first open a connection to a shared "registry" DB or iterate per-slug DBs.

**Fix:**
```python
# cmd_new — replace lines 49-53 with:
# Open a temporary connection to list projects across all DBs
# (Phase 0 note: list_projects is per-DB; iterate PROJECTS_DIR or
#  use a single registry DB as planned in INIT-06)
# Minimal safe fix — remove the duplicate-guard or reimplement it
# against C.db_path once a slug registry DB exists.

# cmd_list — replace line 85:
# projects = db.list_all_projects()  # BROKEN
# Replace with per-DB listing (see Phase 1 registry work).
```
At minimum, replace the call with a guard that does not crash:
```python
# Temporary safe no-op until registry DB is in place (Phase 1):
existing = []
```

---

### WR-02: `vector_search` filters by project via full table scan — cross-project results possible

**File:** `shared/db.py:620-628`
**Issue:** The vector KNN query returns the nearest `top_k` embeddings globally (across ALL projects), then post-filters by calling `search_requirements(conn, project_id)` which itself fetches ALL requirements for the project and builds a generator. Any requirement that matches the KNN but belongs to a different project is silently discarded — but the KNN result set is already capped at `top_k` before the filter, so fewer than `top_k` results may be returned and the caller receives cross-project IDs during the window between the two queries (race-free for SQLite, but logically wrong). More critically, if two projects share a DB (single-file deployment), cross-project requirements will leak.

```python
# Correct fix: push the project_id filter into the vec query join
vec_rows = conn.execute("""
    SELECT e.requirement_id, e.distance
    FROM req_embeddings e
    JOIN requirements r ON r.id = e.requirement_id
    WHERE r.project_id = :project_id
      AND e.embedding MATCH :blob
      AND e.k = :k
    ORDER BY e.distance
""", {"project_id": project_id, "blob": q_blob, "k": top_k}).fetchall()
```

---

### WR-03: Dynamic SQL column names in `update_requirement` — no parameterisation of column identifiers

**File:** `shared/db.py:521-524`
**Issue:** The `sets` list is built from `col_map` keys that are validated against the `updatable` set at line 469, so direct SQL injection via user input is blocked. However, the `col_map` keys (column names) are interpolated directly into the SQL string via `f"UPDATE requirements SET {', '.join(sets)} WHERE id = :req_id"`. If `col_map` is ever extended with a key derived from user input, or if `updatable` and `col_map` diverge, this becomes an injection vector. Additionally, a collision exists: if a field name like `req_id` is in `changes`, it will silently overwrite the `params["req_id"]` sentinel used in the WHERE clause (line 519), producing a silent no-update.

**Fix:**
```python
# Add a hard assertion that no change key collides with the sentinel:
assert "req_id" not in changes, "Field name 'req_id' is reserved"
# Or rename the sentinel parameter to an unambiguous name:
params["_where_req_id"] = req_id
conn.execute(
    f"UPDATE requirements SET {', '.join(sets)} WHERE id = :_where_req_id",
    params
)
```

---

### WR-04: `project_session.refresh_md` dereferences `meta` after None-guard returns wrong value

**File:** `shared/project_session.py:57-80`
**Issue:** At line 58, `meta = db.get_project_by_slug(conn, slug)`. If the project is not found, `meta` is `None`. Lines 63-69 are only reached when `meta` is truthy (the `if meta` guards are applied to `reqs`, `all_decs`, and `mins`), but line 77 calls `md_writer.regenerate(slug, meta, ...)` unconditionally — passing `None` as `meta`. This will raise `AttributeError` inside `md_writer.regenerate` when it accesses any field on `meta`. Since `refresh_md` is called after every write in all skill scripts, this can only manifest if a slug is renamed or the DB row is deleted between the write and the refresh, but the code offers no guard.

**Fix:**
```python
meta = db.get_project_by_slug(conn, slug)
if not meta:
    raise ValueError(f"Project '{slug}' not found — cannot regenerate PROJECT.md")
```

---

### WR-05: `insert_minute` and `mark_integrated` dereference the return of `get_minute` without a None check

**File:** `shared/db.py:734`, `shared/db.py:771`
**Issue:** Both `insert_minute` (line 734) and `mark_integrated` (line 771) call `get_minute(conn, mid)` and return the result directly. `get_minute` returns `Optional[MinuteRow]` — it returns `None` if the row is not found. After a successful `INSERT` or `UPDATE` the row will exist, but if the DB is in WAL mode and another connection has not yet flushed, or if the `INSERT` silently failed (e.g., a constraint violation that was not raised due to a missing `RAISE`), the caller will receive `None` instead of a `MinuteRow`, causing a `TypeError` further up the call stack.

**Fix:**
```python
# insert_minute
result = get_minute(conn, mid)
if result is None:
    raise RuntimeError(f"Failed to retrieve inserted minute '{mid}'")
return result
```

---

### WR-06: `refine.py` `cmd_apply` passes `slug` as `project_id` to `db.update_requirement`

**File:** `skills/refine-requirements/scripts/refine.py:79-83`
**Issue:** `db.update_requirement(conn, args.id, slug, ...)` — the third positional argument is `project_id` (see `db.py` signature at line 448). `slug` is a human-readable string like `"my-ml-project"`, not a UUID `project_id`. The function does not use `project_id` for the UPDATE itself (it only validates the requirement exists via `get_requirement`) so this currently causes no data corruption, but it is semantically wrong and will break any future validation that checks `project_id` consistency.

**Fix:**
```python
slug, conn, meta = ps.resolve(args.project)
# ...
row = db.update_requirement(
    conn, args.id, meta.project_id,   # pass meta.project_id, not slug
    changes, changed_by=args.by, summary=args.summary or "FRET statement applied.",
)
```

---

### WR-07: `_parse_json` in `init.py` can return `None` implicitly — callers dereference the result unsafely

**File:** `skills/new-project-initiation/scripts/init.py:34-42`
**Issue:** `_parse_json` calls `_err(...)` on parse failure, which calls `sys.exit(1)`. In a test environment where `sys.exit` is intercepted (e.g., `pytest.raises(SystemExit)`), `_err` returns `None`, and `_parse_json` then falls through and implicitly returns `None`. The callers (lines 63-68) then pass `None` directly into list comprehensions like `[Stakeholder(**s) for s in _parse_json(...)]`, which would raise `TypeError: 'NoneType' is not iterable`. While this only manifests in test isolation, the function's return type is also technically `list | None`, not `list`.

**Fix:**
```python
def _parse_json(raw, label):
    if not raw:
        return []
    try:
        v = json.loads(raw)
        if not isinstance(v, list):
            raise ValueError("not a list")
        return v
    except Exception:
        _err(f"--{label} must be a valid JSON array")
        return []   # unreachable in production; prevents None return in tests
```

---

## Info

### IN-01: `now` variable assigned but never used in `insert_requirement` and `upsert_project`

**File:** `shared/db.py:403`, `shared/db.py:316`
**Issue:** `now = _now()` is assigned at line 403 in `insert_requirement` and at line 316 in `upsert_project`, but neither function uses the `now` variable — they call `_now()` again inline or via the params dict. The `now` assignment in `insert_requirement` (line 403) is actually used in the params dict; the dead assignment is in `upsert_project` at line 316, where `now` is never referenced.

**Fix:** Remove `now = _now()` at line 316 of `upsert_project`.

---

### IN-02: `test_db_bugs.py` asserts `list_all_projects` does NOT exist — but `init.py` still calls it

**File:** `tests/test_db_bugs.py:83-93`
**Issue:** `TestListProjectsCanonicalName.test_list_all_projects_does_not_exist` correctly verifies that `shared.db` does not expose `list_all_projects`. This test passes. However, `skills/new-project-initiation/scripts/init.py` still calls `db.list_all_projects()` at line 49. The test suite does not cover this caller path, so the fix is only half-complete. A complementary test importing `init.py` and invoking `cmd_new`/`cmd_list` in isolation would catch this regression.

**Fix:** See WR-01. Additionally add an integration test for `cmd_list` that would expose the `AttributeError`.

---

### IN-03: `_make_req_id` imports `uuid` inside the function on every call

**File:** `shared/db.py:393-394`
**Issue:** `import uuid` is executed inside `_make_req_id` on every invocation. Python caches module imports in `sys.modules` so this is not a correctness issue, but it is an unusual pattern inconsistent with the top-level imports elsewhere in the file.

**Fix:** Move `import uuid` to the top-level import block alongside other standard library imports.

---

### IN-04: `test_db_bugs.py` clears `sys.modules["db"]` and `sys.modules["shared.db"]` in every test method — fragile cache-busting

**File:** `tests/test_db_bugs.py:32-36`, `44-47`, `57-59`, `72-74`, `82-84`, `98-100`
**Issue:** Each test method manually purges both module keys before re-importing. This is an unusual pattern that can cause test ordering issues if the module has side effects on import (e.g., the `sys.path.insert` at line 46 of `db.py` will run repeatedly). It also means any module-level state in `db.py` is reset between tests within the same class, which could mask real shared-state bugs. The pattern works but is fragile; a conftest-level fixture or `importlib.reload` would be cleaner.

**Fix:** Consolidate into a module-scoped fixture or use `importlib.reload(shared.db)` once per class.

---

### IN-05: `search_requirements` tag-filter builds a JOIN but leaves a dangling clause addition before cleanup

**File:** `shared/db.py:566-581`
**Issue:** When `tag` is provided, a clause `"json_each.value = :tag"` is first appended to `clauses` (line 567), then the `tag_join` string is built (lines 575-577), and finally the clause is removed again (lines 580-581). This round-trip add-then-remove is confusing and error-prone. If the removal regex ever fails to match (e.g., due to whitespace changes), the WHERE clause will include `json_each.value = :tag` twice, causing a SQL syntax error.

**Fix:** Restructure so the tag clause is never added to `clauses` in the first place:
```python
if tag:
    params["tag"] = tag
    # clause is handled entirely via the JOIN — do not add to clauses
tag_join = "JOIN json_each(r.tags) ON json_each.value = :tag" if tag else ""
```

---

_Reviewed: 2026-04-23T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
