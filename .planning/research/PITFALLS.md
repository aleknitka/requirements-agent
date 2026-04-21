# Domain Pitfalls: Requirements Engineering Agent (v1 CLI)

**Domain:** CLI-first requirements elicitation agent with FRET formalisation and SQLite persistence
**Researched:** 2026-04-21
**Scope:** v1 end-to-end flow — init → interview → elicit → FRET-refine → persist → status report

---

## Critical Pitfalls

Mistakes that cause NameErrors at runtime, data loss, or schema migrations.

---

### Pitfall 1: `C.DB_PATH` referenced but never defined in CONSTANTS

**What goes wrong:** `db.py` line 92 has `def get_db(path: str = C.DB_PATH)`. `CONSTANTS.py` exposes `db_path(slug)` (a function) but no `DB_PATH` attribute. Every import of `db.py` raises `AttributeError: module 'CONSTANTS' has no attribute 'DB_PATH'` at module load time — before any function is called.

**Why it happens:** The schema shifted from a single global DB to one DB per project, but the default parameter in `get_db` was not updated. `db_path(slug)` is the correct path helper but it requires a slug argument, making it unsuitable as a default.

**Warning signs:**
- `AttributeError: module 'CONSTANTS' has no attribute 'DB_PATH'` in any test that does not pre-mock `shared.db`
- Tests work only because `test_init.py` pre-injects a `MagicMock()` for `shared.db` into `sys.modules` before collection

**Prevention:** Remove the default entirely. `get_db` should be called as `db.get_db(C.db_path(slug))` at every call site. Alternatively, make the signature `def get_db(path: Path)` with no default.

**V1 phase:** INIT-03 (db.py API consistency)

---

### Pitfall 2: `import shared.db` binds `shared`, not `db`

**What goes wrong:** In `init.py` the import is written as `import shared.db`. Python's import system binds the top-level name `shared` in the local namespace, not `db`. Every subsequent `db.get_db(...)` call raises `NameError: name 'db' is not defined` at runtime.

**Why it happens:** Standard Python gotcha: `import a.b` gives you `a`, not `b`. The correct form is `import shared.db as db` or `from shared import db`.

**Warning signs:**
- Tests work because `test_init.py` injects `init.db = _mock_db_module` after loading the module — which papers over the real import error
- Running `init.py` directly without mocks produces a NameError on the first `db.` call

**Prevention:** Change `init.py` line 21 to `import shared.db as db`. Apply the same check to every other skill script that uses `import shared.<module>`.

**V1 phase:** INIT-03

---

### Pitfall 3: `list_all_projects()` called but `db.py` exposes `list_projects(conn)`

**What goes wrong:** `init.py` and `project_session.py` call `db.list_all_projects()` with no arguments. `db.py` only has `list_projects(conn: sqlite3.Connection)`, which requires a connection. The function name and signature both differ.

**Why it happens:** The API was changed at some point (adding per-project DB files) but not all callers were updated. Additionally, `project_session.py` calls this before any connection is opened, which implies the function needs to scan the filesystem for existing project directories rather than query a single connection.

**Warning signs:**
- `AttributeError: ... has no attribute 'list_all_projects'` at runtime
- `test_init.py` mocks `db.list_all_projects` — the mock succeeds because `MagicMock` auto-creates any attribute, hiding the real missing function

**Prevention:** Decide the contract: either add a `list_all_projects()` function to `db.py` that scans `PROJECTS_DIR` for `*.db` files and opens each to read the project row, or change all callers to the existing `list_projects(conn)` signature. The filesystem-scan approach is more robust for a per-project-DB design.

**V1 phase:** INIT-03

---

### Pitfall 4: `project_session.py` calls `db.get_project(conn)` with one argument but `db.py` signature is `get_project(conn, project_id)`

**What goes wrong:** `project_session.py` line 78 calls `db.get_project(conn)` without a `project_id`. `db.py`'s `get_project(conn, project_id)` requires two arguments. This causes `TypeError: get_project() missing 1 required positional argument: 'project_id'` every time `resolve()` is called, which is called by every skill.

**Warning signs:** `ps.resolve(...)` always raises `TypeError` in integration. This is entirely masked by test mocks.

**Prevention:** Since each DB file contains exactly one project, add a `get_single_project(conn)` convenience function that fetches the only row, or pass `project_id` explicitly after resolving the slug. The single-project-per-DB invariant should be codified.

**V1 phase:** INIT-03

---

### Pitfall 5: `RequirementType` is a Pydantic model, not an Enum — breaks DB serialisation and model consistency

**What goes wrong:** `models.py` defines `RequirementType` as a `BaseModel` with `code`, `name`, `description` fields. `db.py` stores it as `req_type TEXT` in SQLite and calls `RequirementType(d["req_type"])` to reconstruct it — but `RequirementType` is not callable with a positional string; it requires keyword arguments. `RequirementIn` references `RequirementArea` (which does not exist in the file) rather than `RequirementType`.

**Why it happens:** Models diverged between `models.py` and `db.py`. `models.py` appears partially migrated — `RequirementIn` still references `RequirementArea` (a name that no longer exists), while `db.py` assumes enum-style construction.

**Warning signs:**
- `NameError: name 'RequirementArea' is not defined` on any import of `models.py` where `RequirementIn` is constructed
- `make_req_id(req_type: RequirementArea)` in `models.py` also references the missing name
- `_make_req_id` in `db.py` calls `req_type.id_prefix` — but `RequirementType` has no `id_prefix` field

**Prevention:** Decide: Enum or model? For storage simplicity, convert `RequirementType` to a `str` enum using the three-letter `code` as the value. Store the full metadata in a separate lookup table or constants dict. Remove `RequirementArea` references completely. Ensure `_make_req_id` uses the correct attribute.

**V1 phase:** INIT-03 / PERSIST-01

---

### Pitfall 6: `search_requirements(conn)` called without `project_id` in multiple places

**What goes wrong:** `project_session.py` line 87 calls `db.search_requirements(conn)` — no `project_id` argument. `db.py`'s signature is `search_requirements(conn, project_id, ...)` where `project_id` is required. The same issue appears in `report.py` lines 29–31.

**Warning signs:** `TypeError: search_requirements() missing 1 required positional argument: 'project_id'` every time `refresh_md()` or a report is generated.

**Prevention:** Either make `project_id` optional with a fallback to "all projects", or pass `project_id` consistently from the resolved slug. Given per-project DBs, "all requirements in this DB" is the natural default — make `project_id` optional with `None` meaning "no filter".

**V1 phase:** INIT-03 / REPORT-01

---

### Pitfall 7: `refine.py` passes `update_requirement` with wrong argument count

**What goes wrong:** `refine.py` line 90 calls `db.update_requirement(conn, args.id, changes, changed_by=args.by, summary=...)` — three positional args. `db.py`'s signature is `update_requirement(conn, req_id, project_id, changes, ...)` — `project_id` is the third positional argument, not `changes`. `changes` is the fourth.

**Warning signs:** `TypeError` on every `refine apply` invocation. Passing a dict where a string `project_id` is expected.

**Prevention:** The `project_id` parameter in `update_requirement` is redundant because `req_id` is globally unique (UUIDs). Remove `project_id` from the signature, or make it optional and ignore it. Then all callers can pass `(conn, req_id, changes, ...)` cleanly.

**V1 phase:** ELICIT-03

---

### Pitfall 8: `refine.py` passes `has_fret=False` to `search_requirements` — parameter does not exist

**What goes wrong:** `refine.py` line 31 calls `db.search_requirements(conn, has_fret=False)`. `db.py`'s `search_requirements` signature has no `has_fret` parameter. The filter is silently ignored and all requirements are returned.

**Warning signs:** `cmd_pending` always returns all requirements, never filtered — no error, just wrong behaviour.

**Prevention:** Add `has_fret: Optional[bool] = None` to `search_requirements` and implement the filter: `WHERE (fret_statement IS NULL OR fret_statement = '')` when `has_fret=False`.

**V1 phase:** ELICIT-03

---

### Pitfall 9: FRET fields (`fret_statement`, `fret_fields`) not in SQLite schema but exist in `RequirementIn`

**What goes wrong:** `models.py` defines `fret_statement: Optional[str]` and `fret_fields: Optional[dict]` on `RequirementIn`. The `requirements` table in `db.py` has no `fret_statement` or `fret_fields` columns. `_row_to_requirement` will not set them (columns absent from `SELECT *`), and `insert_requirement`/`update_requirement` do not write them.

**Why it happens:** The FRET fields were added to the model but the schema and persistence layer were not updated in sync.

**Warning signs:** `refine apply` writes to the DB without error but `fret_statement` is always `None` when read back. The entire `refine-requirements` skill produces no durable output.

**Prevention:** Add `fret_statement TEXT` and `fret_fields TEXT` columns to the `requirements` table in `bootstrap()`. Update `insert_requirement` and `update_requirement` to write them. Update `_row_to_requirement` to read them. Add `fret_statement` and `fret_fields` to the `updatable` set in `update_requirement`.

**V1 phase:** PERSIST-01

---

## Moderate Pitfalls

Mistakes that produce wrong output, hard-to-trace bugs, or painful future migrations.

---

### Pitfall 10: `ProjectMeta` has `slug` field but `projects` table has no `slug` column

**What goes wrong:** `ProjectMeta` has a `slug: str = ""` field. The `projects` table schema has no `slug` column. `upsert_project` does not write `slug`. `_row_to_project` does not read it (it will always be the empty default). Anything that uses `meta.slug` after loading from the DB will get `""`.

**Warning signs:** `ps.resolve()` returns `slug` from filesystem scan but after `db.get_project(conn)` the returned `meta.slug` is `""`. Code using `meta.slug` to construct file paths will write to the root of `PROJECTS_DIR`.

**Prevention:** Add a `slug TEXT NOT NULL` column to the `projects` table and persist it. Since slug is derived from name, it can also be re-derived on read with `C.slugify(meta.name)` — but storing it is safer and avoids divergence if names change.

**V1 phase:** INIT-03

---

### Pitfall 11: `update_requirement` does not allow `fret_statement`/`fret_fields` in `updatable` set

**What goes wrong:** The `updatable` set on line 446 in `db.py` does not include `"fret_statement"` or `"fret_fields"`. Any attempt to update these fields raises `ValueError: Fields not updatable: {'fret_statement'}`. The `refine apply` command will always fail.

**Prevention:** Once the schema columns are added (Pitfall 9), add `"fret_statement"` and `"fret_fields"` to `updatable` and to `col_map`.

**V1 phase:** ELICIT-03 / PERSIST-01

---

### Pitfall 12: `db.list_decisions(conn)` called without `project_id` in `project_session.py` and `report.py`

**What goes wrong:** `project_session.py` line 100 and `report.py` line 31 call `db.list_decisions(conn)` — no `project_id`. `db.py`'s signature is `list_decisions(conn, project_id, ...)` where `project_id` is required.

**Warning signs:** `TypeError` on every `refresh_md()` and every status report generation.

**Prevention:** Pass `project_id` explicitly, or make it optional (all decisions in the DB).

**V1 phase:** REPORT-01

---

### Pitfall 13: `db.list_minutes(conn)` called without `project_id` in `project_session.py` and `report.py`

**What goes wrong:** Same pattern — `project_session.py` line 102 and `report.py` line 30 call `db.list_minutes(conn)` without `project_id`. `db.py` requires it.

**Prevention:** Same fix as Pitfall 12.

**V1 phase:** REPORT-01

---

### Pitfall 14: `_parse_json` in `init.py` silently drops the return value path on invalid JSON

**What goes wrong:** `_parse_json` calls `_err(...)` on bad input, which calls `sys.exit(1)`. However the function has no explicit `return` after the `except` block. If `_err` is ever mocked or patched to not exit, `_parse_json` returns `None` instead of `[]`, causing downstream `for s in None` to raise `TypeError`.

**Warning signs:** Tests that mock `_err` will see `None` from `_parse_json`, causing silent failures if assertions only check exit code.

**Prevention:** Add `return []` after the `_err(...)` call as a safety net. In production `_err` always exits, but defensive returns prevent footguns in test code.

**V1 phase:** INIT-01

---

### Pitfall 15: Embedding always attempted on `insert_requirement` even when API key is absent — race condition on first `conn.commit()`

**What goes wrong:** `insert_requirement` calls `_store_embedding(...)` before `conn.commit()`. If embedding succeeds, the requirement row and embedding are committed together. If embedding fails silently (API key absent), the requirement is still committed (line 420 `conn.commit()`) — which is the intended behaviour. However, `_store_embedding` issues its own `conn.execute(INSERT INTO req_embeddings)` inside a try/except without committing. If the function raises after the req insert but before the outer `commit()`, the embedding insert is rolled back but the requirement insert is not (WAL mode with implicit transaction). This is actually correct, but the ordering makes it non-obvious. The real risk: if `sqlite-vec` `VIRTUAL TABLE` operations require an explicit transaction boundary that differs from regular tables, partial state can occur.

**Prevention:** Wrap the entire `insert_requirement` body in a single explicit `with conn:` context manager. SQLite's connection context manager handles rollback on exception.

**V1 phase:** PERSIST-01

---

## Minor Pitfalls

---

### Pitfall 16: `slugify` does not handle collisions — two projects with different names can produce the same slug

**What goes wrong:** `C.slugify("My Project")` and `C.slugify("my project!")` both return `"my-project"`. The duplicate-slug guard in `cmd_new` catches this, but only by calling `db.list_all_projects()` which itself is broken (Pitfall 3). Until that is fixed, the guard is inactive, and two projects could share a directory.

**Warning signs:** Second `init new` with a name that slugifies identically silently overwrites the first project's DB.

**Prevention:** Fix `list_all_projects()` first (Pitfall 3). Then the existing slug guard in `cmd_new` is sufficient.

**V1 phase:** INIT-01

---

### Pitfall 17: `db.py`'s `_make_req_id` references `req_type.id_prefix` — attribute does not exist on `RequirementType`

**What goes wrong:** `_make_req_id(req_type: RequirementType)` calls `req_type.id_prefix`. `RequirementType` has `code`, `name`, `description` — no `id_prefix`. Every `insert_requirement` call raises `AttributeError`.

**Prevention:** Change `req_type.id_prefix` to `req_type.code`. The three-letter code (e.g. `"FUN"`) is already the intended prefix.

**V1 phase:** PERSIST-01

---

### Pitfall 18: FRET grammar reference uses requirement type names (`CORE`, `DATA`, `MODEL`, `INFRA`) that do not match the model

**What goes wrong:** `fret_grammar.md` lists type categories `CORE`, `DATA`, `MODEL`, `INFRA`, `OPS`, `UX`, `COMPLIANCE`. `models.py` defines 34 types with codes like `FUN`, `DAT`, `MOD`, `OPS`, `UIX`, `COM`. The agent reading the grammar reference will propose FRET patterns for type names that do not match what the DB accepts.

**Warning signs:** Agent suggests `req_type: "CORE"` — validation fails because `"CORE"` is not a valid `RequirementType` code. Requires silent fallback or a confusing error.

**Prevention:** Update `fret_grammar.md` to use the actual `code` values from `models.py`, or add a mapping table. Keep grammar reference and model in sync — they are both in the same repo.

**V1 phase:** ELICIT-03

---

### Pitfall 19: `report.py` re-derives slug from `meta.name` via `C.slugify(meta.name)` rather than using the resolved slug

**What goes wrong:** `cmd_generate` and `cmd_save` in `report.py` call `ps.resolve(args.project)` which returns `(slug, conn, meta)` as the first element — then immediately discard it with `_, conn, meta = ps.resolve(...)`. They then re-derive slug from `C.slugify(meta.name)`. If `meta.name` has changed since the directory was created (e.g. via `update --name`), the re-derived slug differs from the actual directory slug, and `C.project_dir(slug)` will create a new directory.

**Prevention:** Use the slug returned by `ps.resolve` directly: `slug, conn, meta = ps.resolve(...)`. This is a naming consistency issue — do not discard the first tuple element.

**V1 phase:** REPORT-01

---

### Pitfall 20: CLI JSON output inconsistency between `_ok`/`_err` across skills

**What goes wrong:** Different skills implement `_ok`/`_err` differently:
- `init.py`: `_err` writes to `sys.stderr`, exits with code 1
- `report.py`: `_err` writes to `sys.stderr`, exits with code 1
- `project_session.py`: `_err` writes to `stdout` via `print()`, exits with code 1

Downstream consumers (Claude Code, test harnesses) parsing stdout will see error messages in `project_session.py`'s error path that would otherwise be expected on stderr. Any consumer that reads stdout to detect failures will silently swallow session resolution errors.

**Warning signs:** Tests for `project_session.py` that check `capsys.readouterr().err` will find empty stderr on session errors.

**Prevention:** Standardise on a single `_ok`/`_err` implementation in `shared/` and import it everywhere. `_err` always writes to `stderr`, `_ok` always writes to `stdout`.

**V1 phase:** INIT-01

---

## Conversation Design Pitfalls (LLM-driven elicitation)

---

### Pitfall 21: Agent asks all FRET fields in one turn, overwhelming the user

**What goes wrong:** The `fret_grammar.md` refinement process lists five fields to resolve. If the agent asks "What is the scope, condition, component, timing, and response for this requirement?" in a single message, stakeholders answer only part of the question or give a confused non-answer. The agent then has to re-ask, and the conversation feels like an interrogation rather than collaborative capture.

**Warning signs:** User responses contain phrases like "I don't know what you mean by 'timing'" or give a narrative that bundles multiple fields, making parsing unreliable.

**Prevention:** Resolve fields sequentially, starting with the two required fields (`component` and `response`) before asking for optional refinements (`scope`, `condition`, `timing`). One question per turn.

**V1 phase:** ELICIT-02

---

### Pitfall 22: Context loss between refinement turns corrupts the FRET statement

**What goes wrong:** FRET refinement is multi-turn. If the conversation context window is truncated or the skill is re-invoked without prior context, the agent loses previously confirmed field values and either asks again or fills in defaults. The resulting FRET statement is incomplete or contradicts what the user said.

**Warning signs:** `fret_fields` in the DB contains `null` entries for fields the user explicitly answered in earlier turns. FRET statement references component or timing values not present in `fret_fields`.

**Prevention:** Write partial FRET state to the DB incrementally, not only at final confirmation. Each confirmed field can be stored in `fret_fields` as a partial dict. The `apply` command already accepts partial `--fret-fields` JSON. Use this to checkpoint after each confirmed field.

**V1 phase:** ELICIT-03

---

### Pitfall 23: Agent accepts vague FRET statements because it does not validate against the grammar pattern

**What goes wrong:** The grammar specifies `[SCOPE] [CONDITION] the [COMPONENT] shall [TIMING] [RESPONSE]`. The agent may produce or accept statements like "the system should handle requests properly" — which uses "should" not "shall", omits component specificity, and has no measurable response. These pass through `apply` without complaint because there is no grammar validator.

**Warning signs:** `fret_statement` in the DB contains "should", "may", "quickly", "properly", "appropriately", or "the system" as component.

**Prevention:** Add a lightweight validator function (regex or Pydantic) that checks: (1) contains "shall", (2) has a named component that is not "the system" alone, (3) does not contain the vague phrases listed in `fret_grammar.md`. Run it in `cmd_apply` before writing, and surface warnings to the agent for one more user confirmation pass.

**V1 phase:** ELICIT-03

---

## Testing Pitfalls

---

### Pitfall 24: Only `init.py` has tests — no tests for `db.py`, `project_session.py`, or any other skill

**What goes wrong:** The four known bugs (Pitfalls 1–4) were not caught by tests because `db.py` has no unit tests and `project_session.py` has none. The only test file (`test_init.py`) mocks the entire `db` module, so it cannot detect when the real `db.py` breaks on import.

**Warning signs:** `uv run pytest` passes with a full mock stack while the production import path crashes on every real invocation.

**Prevention:** Add integration tests that use a real SQLite database (via `tmp_path` fixture) without mocking `db.py`. At minimum: `test_db.py` covering `get_db`, `upsert_project`, `insert_requirement`, `get_requirement`, `list_projects`. These will immediately surface Pitfalls 1, 5, 9, and 17.

**V1 phase:** INIT-04

---

### Pitfall 25: Test mocks are too permissive — `MagicMock` auto-creates any attribute, hiding API mismatches

**What goes wrong:** `test_init.py` uses `MagicMock()` for the entire `db` module. `MagicMock` auto-creates any accessed attribute as another `MagicMock`. So `self.db.list_all_projects.return_value = []` succeeds even though the real `db` has no `list_all_projects` — the test is testing mock behaviour, not real API behaviour.

**Warning signs:** All tests pass; production raises `AttributeError` on every command.

**Prevention:** Replace `MagicMock()` for the `db` module with `create_autospec(db_module)`, which fails if a method or attribute does not exist on the real module. This bridges the gap between test and production API. Requires fixing the real `db.py` imports first (Pitfall 1).

**V1 phase:** INIT-04

---

## Phase-Specific Warning Table

| V1 Phase | Topic | Likely Pitfall | Mitigation |
|----------|-------|----------------|------------|
| INIT-01 | Project creation | `list_all_projects` missing; slug collision guard inactive (Pitfall 3, 16) | Fix db.py API before testing init flow |
| INIT-03 | db.py API consistency | Five distinct API bugs that all cascade (Pitfalls 1–4, 12, 13) | Fix all API mismatches in a single db.py pass before writing any new skill code |
| INIT-04 | DB unit tests | Mocks too permissive; real import broken (Pitfall 1, 25) | Write `test_db.py` against real SQLite via `tmp_path`; use `create_autospec` |
| ELICIT-02 | LLM interview design | Multi-question overwhelm causes context loss (Pitfall 21) | One FRET field per turn; required fields first |
| ELICIT-03 | FRET refinement | `has_fret` filter missing; `update_requirement` rejects fret fields; vague statements not caught (Pitfalls 8, 11, 23) | Add `has_fret` param; add fret fields to `updatable`; add grammar validator |
| PERSIST-01 | Requirement storage | `fret_statement`/`fret_fields` columns absent from schema; `id_prefix` AttributeError (Pitfalls 9, 17) | Schema migration before any elicitation testing |
| REPORT-01 | Status report | `search_requirements`, `list_decisions`, `list_minutes` all missing `project_id`; slug re-derived from name (Pitfalls 6, 12, 13, 19) | Fix all call sites in `report.py` and `project_session.py` in one pass |

---

## Data Model Fields That Seem Optional at v1 But Cause Painful Migrations Later

| Field | Current state | Why it matters later |
|-------|--------------|---------------------|
| `slug` in `projects` table | Not persisted (Pitfall 10) | Every path helper depends on slug; if name changes, re-derived slug diverges from actual directory |
| `fret_statement` / `fret_fields` | Not in schema (Pitfall 9) | Core v1 deliverable; adding columns to an existing table with data requires a migration script |
| `fret_fields.component` | No separate column, stored as JSON blob | Cannot query "all requirements owned by component X" without JSON extraction — add a generated column if needed in v2 |
| `req_type` stored as plain `TEXT` | Code only, no lookup enforced at DB level | Adding a `CHECK` constraint later requires a table rebuild; add it now via `CHECK(req_type IN (SELECT code FROM ...))` or an enum-pattern constraint |
| `has_embedding` | Derived via LEFT JOIN, not a real column | Fine for v1; if embedding table grows large, the join becomes expensive — add a boolean column on `requirements` if embedding coverage matters |
| `version` / `deleted_at` on requirements | Not present | No soft-delete, no version history beyond the `updates` log; adding later requires a table migration and changes to all `SELECT` queries |
