# Architecture Patterns: Requirements Engineering Agent v1

**Domain:** Conversational requirements engineering agent (gitagent/CLI-harness pattern)
**Researched:** 2026-04-21
**Confidence:** HIGH — based on direct codebase analysis, no external dependencies

---

## Recommended Architecture

### Overall Shape

```
Claude Code CLI (harness)
        │
        ▼
  agent.yaml  ←── SOUL.md, RULES.md, hooks/
        │
        ├── Skill: project-init         ← new-project-initiation/
        ├── Skill: project-update       ← req_ops.py (CRUD)
        ├── Skill: refine-requirements  ← refine.py (FRET)
        ├── Skill: review-requirements  ← review.py
        ├── Skill: status-report        ← report.py
        └── Skill: meeting-agent        ← meeting.py
                │
                ▼
          shared/ library
          ┌────────────────────────────────────────────────┐
          │  CONSTANTS.py  →  path resolution              │
          │  models.py     →  Pydantic validation DTOs     │
          │  db.py         →  SQLite CRUD + vector search  │
          │  md_writer.py  →  PROJECT.md regeneration      │
          │  project_session.py → active project resolver  │
          └────────────────────────────────────────────────┘
                │
                ▼
          projects/<slug>/
          ├── <slug>.db        ← SQLite (requirements, updates, meetings)
          └── PROJECT.md       ← derived read-only view
```

---

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `agent.yaml` | Identity, model prefs, skill registry, compliance settings | Claude Code harness (prek/gitagent) |
| `SKILL.md` per skill | LLM instructions + allowed-tools constraint | Agent context window only |
| Skill scripts (`*.py`) | CLI entry points — validate input, call shared/, emit JSON | `shared/` library via sys.path |
| `shared/models.py` | All data validation; nothing writes to DB without these | `db.py`, skill scripts |
| `shared/db.py` | All SQLite CRUD + sqlite-vec; single persistence authority | `models.py`, `CONSTANTS.py` |
| `shared/project_session.py` | Active project auto-resolution; refresh trigger | `db.py`, `md_writer.py` |
| `shared/md_writer.py` | Derived `PROJECT.md` generation (read-only view) | `db.py` |
| `shared/CONSTANTS.py` | Path resolution, embedding config, env var gateway | All of `shared/` |
| `projects/<slug>/<slug>.db` | Authoritative state; every requirement, update, meeting | `db.py` exclusively |
| `projects/<slug>/PROJECT.md` | Human-readable derived view; `NOTES` block is editable | `md_writer.py` |

**Hard rules enforced by this boundary design:**
- Skills never import from other skills.
- Nothing writes to SQLite except through `db.py`.
- Nothing writes to `PROJECT.md` except through `md_writer.regenerate()`.
- `CONSTANTS.py` is the only file that reads environment variables.

---

## Conversation State: Where It Lives

### The Core Question

The agent operates through Claude Code CLI. Each user turn is a new message in the same Claude Code session. The question is: what must survive beyond Claude's context window, and what can stay in-context?

### Recommendation: Two-tier state model

**Tier 1 — Claude context window (ephemeral, in-session)**

- The elicitation conversation itself: user answers to interview questions
- Working memory for the current requirement being drafted
- FRET field proposals before user approval
- Clarification sub-dialogues ("what do you mean by 'quickly'?")

This state does NOT need to be persisted anywhere. Claude Code maintains it naturally across turns within one session. The agent should treat a single user session as the unit of conversation.

**Tier 2 — SQLite (persisted, cross-session)**

- Completed requirements (written only after the user confirms the FRET statement)
- Project metadata (name, stakeholders, objectives, success criteria)
- Meeting minutes, decisions, action items
- Audit trail (UpdateRecord diffs)
- FRET coverage stats

**What this means in practice:** The agent does NOT need a "session state file" or "conversation checkpoint". Claude Code's context IS the conversation state. Persistence into SQLite is a one-way gate: data enters the DB only when a discrete artifact (a project, a requirement, a FRET statement) is confirmed and complete.

### Why file-based session state is wrong for this system

A session-state file (e.g., `.session.json` with partial interview answers) would create a third source of truth alongside Claude's context and SQLite. It introduces sync bugs, stale-state risks on crashes, and complicates the "what did the user already say?" question that Claude's context already answers correctly. Avoid it.

### The only legitimate cross-session state problem

If the agent is interrupted mid-elicitation (process killed, user closes terminal), in-progress work is lost. The correct mitigation is NOT a session file — it is a "draft requirement" status. Add a `DRAFT` status to `RequirementStatus` that the agent can write early, then promote to `OPEN` on confirmation. This keeps all state in SQLite and allows resumption without a separate state file.

---

## The Boundary Between Agent Conversation and Persisted Data

### Principle: Write to DB at confirmation gates only

The agent should never persist speculative or partial data. There are three natural confirmation gates in the v1 flow:

```
Gate 1: "Here is what I understand about your project. Is this correct?"
        → db.upsert_project()  [project-init]

Gate 2: "Here is the requirement I've captured. Does this look right?"
        → db.insert_requirement() with status=OPEN  [project-update]

Gate 3: "Here is the FRET statement I propose: [...]. Confirm?"
        → db.update_requirement() setting fret_statement  [refine-requirements]
```

Between gates, all elicitation is purely conversational — in Claude's context, not in DB. This keeps the DB clean (no partial rows to clean up) and matches the user's mental model (the DB represents what they've agreed to).

---

## The v1 End-to-End Flow

```
User opens Claude Code
        │
        ▼
[1] project_session.resolve() — is there an active project?
        │
        ├── No projects → trigger project-init skill
        │       Interview user (in-context)
        │       Call init.py new --name ... [options]
        │       Gate 1 confirmation → DB write
        │       Return slug
        │
        └── One project → auto-select (silent)
            Multiple projects → agent asks user to choose
                │
                ▼
[2] Elicitation (project-update skill)
        Agent interviews user about requirements (in-context)
        Proposes requirement title + description + type
        Gate 2 confirmation → req_ops.py add --title ... --description ...
                │
                ▼
[3] FRET refinement (refine-requirements skill)
        Agent loads fret_grammar.md into context
        Calls refine.py show --id REQ-XXX
        Proposes FRET statement (in-context, multi-turn per requirement)
        Gate 3 confirmation → refine.py apply --id ... --fret-statement ...
                │
                ▼
[4] Status report (status-report skill)
        Calls report.py generate --format md
        Prints to user
```

---

## project_session.resolve() — Active Project Auto-Selection

### Current behaviour (from code)

- 0 projects → error, tells user to run init
- 1 project → auto-selects silently (correct)
- N projects → prints JSON list, exits with code 1, expects caller to re-invoke with `--project <slug>`

### Problem for v1

The "exit 1 and tell user to pass --project" pattern requires the agent to parse the error JSON and re-invoke the script. This is awkward in a conversational flow because it interrupts the conversation with a mechanical re-invocation cycle.

### Recommendation: Active project tracking via a sentinel file

Add `projects/.active` — a plain text file containing the slug of the most recently used project. Rules:
- Written by `init.py new` and any `ps.resolve()` that selects a project by name/slug
- Read by `ps.resolve()` when `slug_or_name` is None and multiple projects exist
- Overridden by explicit `--project <slug>` on any call (and updated at that point)
- Deleted when the active project's DB is removed

This avoids asking the user "which project?" on every turn while still being overrideable.

```
projects/
├── .active          ← contains "my-ml-project" (plain text, single line)
├── my-ml-project/
│   ├── my-ml-project.db
│   └── PROJECT.md
└── other-project/
    ├── other-project.db
    └── PROJECT.md
```

**`ps.resolve()` updated logic:**

```python
# Pseudocode — implementation in shared/project_session.py
def resolve(slug_or_name=None):
    projects = db.list_all_projects()
    if not projects:
        _err("No projects. Run project-init.")

    if slug_or_name:
        slug = _match(projects, slug_or_name)
        _write_active(slug)           # update sentinel
        return _open(slug)

    if len(projects) == 1:
        slug = projects[0]["slug"]
        _write_active(slug)
        return _open(slug)

    # Multiple projects — try sentinel file first
    active = _read_active()
    if active and any(p["slug"] == active for p in projects):
        return _open(active)          # silent: last-used project

    # Sentinel missing/stale — must ask
    _err_with_listing(projects)       # exit 1 with project list
```

**Why a file rather than a DB column:** There is no single shared DB — each project has its own. The sentinel file lives in `projects/` which is the only shared directory. It's a one-liner read/write, requires no schema change, and is trivially inspectable.

---

## FRET Refinement: Single Call vs Multi-Turn Per Field

### Recommendation: Multi-turn, one FRET field at a time

The refine-requirements skill already has the right structure (`refine.py pending` → `show` → `apply`). The question is how the LLM conversation between `show` and `apply` should be structured.

**Do NOT do:** Single LLM call with "here are all 5 FRET fields, fill them all in at once." This produces hallucinated field values for fields where the requirement is genuinely ambiguous, and the user cannot tell which fields are well-supported vs invented.

**Do:** Walk through FRET fields in order, one at a time, pausing when a field reveals genuine ambiguity:

```
1. COMPONENT — almost always obvious from context. Propose immediately.
2. SCOPE — ask "does this apply in all modes, or only in X?"
3. CONDITION — ask "is there a trigger/precondition, or is this always active?"
4. TIMING — ask "does this need to happen immediately? within a window?"
5. RESPONSE — often partially known; confirm the exact observable behaviour
```

For ML/DS requirements (the target domain), CONDITION and TIMING are the highest-ambiguity fields — they are often omitted from natural language requirements and need explicit elicitation. COMPONENT is low-ambiguity.

**Assembly:** After each field is confirmed in-context, the agent assembles the full statement and proposes it for Gate 3 confirmation before calling `refine.py apply`.

**Why this works with the existing CLI design:** `refine.py apply` takes the complete assembled `--fret-statement` and `--fret-fields` JSON. The multi-turn conversation is entirely in-context; the CLI call only fires once, at the end.

---

## Skill Decomposition for v1

### Current skills vs v1 needs

| Skill | Current state | v1 role | Gap |
|-------|--------------|---------|-----|
| `project-init` (new-project-initiation) | Script exists (`init.py`), has import bugs | Handles INIT-01 through INIT-05 | Fix import bugs (known); `init.py` uses `import shared.db` instead of `import db` |
| `project-update` | `req_ops.py` complete | Handles ELICIT-02, ELICIT-03, PERSIST-01 | None critical — needs `DRAFT` status for resumption |
| `refine-requirements` | `refine.py` complete | Handles ELICIT-03 (FRET), PERSIST-01 (via apply) | None — flow is correct |
| `status-report` | `report.py.py` (double extension bug) | Handles REPORT-01 | Rename file |
| `review-requirements` | Present | Not in v1 critical path | Leave as-is |
| `meeting-agent` | Present | Not in v1 critical path | Leave as-is |

### Missing skill for v1: `elicit-requirements`

The current skill set has a gap. `project-update` is a CRUD skill ("add a requirement"), not an elicitation skill ("interview me and figure out what my requirements are"). These are architecturally different:

- **CRUD skill:** Agent calls tool, writes row, done.
- **Elicitation skill:** Agent conducts multi-turn conversation, surfaces implicit needs, classifies them, then calls CRUD tool to write.

**Recommendation:** Add an `elicit-requirements` skill whose SKILL.md instructs the agent to:
1. Ask open-ended questions about the project domain
2. Identify latent requirements from user answers
3. Classify by RequirementType (BUS, FUN, DAT, MOD, etc.)
4. Propose each requirement for confirmation before writing via `req_ops.py add`

The `project-update` skill retains its current form for direct CRUD operations. The `elicit-requirements` skill wraps the conversation layer. This preserves the single-responsibility principle in the skill layer.

**Alternatively** (lower effort): Extend `project-update`'s SKILL.md with elicitation instructions. Functionally equivalent for v1, but risks making the skill too broad over time.

---

## Data Flow: v1 End-to-End

```
User message: "Let's start a new project"
        │
        ▼
Agent reads project-init SKILL.md instructions into context
Agent interviews user (5–10 turns, in-context only)
Agent calls: uv run python skills/new-project-initiation/scripts/init.py new \
             --name "..." --code "..." --objective "..." --project-owner "..."
DB write: projects/my-project/my-project.db (project row)
File write: projects/my-project/PROJECT.md
        │
        ▼
User message: "Now let's capture requirements"
        │
        ▼
Agent reads elicit-requirements (or project-update) SKILL.md
Agent interviews user about their system needs (N turns, in-context)
Agent proposes: "REQ-FUN-001: The inference service shall respond within 200ms"
User confirms
Agent calls: uv run python skills/project-update/scripts/req_ops.py add \
             --type FUN --title "..." --description "..." --by "agent"
DB write: requirements row (status=open, no fret yet)
        │
        ▼
Agent: "Let's now formalise that requirement with FRET grammar"
        │
        ▼
Agent reads fret_grammar.md into context
Agent calls: uv run python skills/refine-requirements/scripts/refine.py show \
             --id REQ-FUN-001
Multi-turn field-by-field FRET elicitation (in-context)
Agent proposes full FRET statement
User confirms
Agent calls: uv run python skills/refine-requirements/scripts/refine.py apply \
             --id REQ-FUN-001 --fret-statement "..." --fret-fields '{"component":"...",...}'
DB write: fret_statement + fret_fields on requirement row
        │
        ▼
User: "Give me a status report"
        │
        ▼
Agent calls: uv run python skills/status-report/scripts/report.py generate --format md
Reads stdout JSON/MD, presents to user
```

---

## Build Order for v1

Listed in dependency order. Each item is a discrete, testable deliverable.

### Phase 0: Fix known bugs (blockers for everything else)

1. `shared/db.py` line 92: remove `C.DB_PATH` default — use `db_path(slug)` helper instead
2. `skills/new-project-initiation/scripts/init.py`: fix `import shared.db` → `import db` (and `shared.CONSTANTS` → `CONSTANTS`, etc.)
3. `skills/new-project-initiation/scripts/init.py`: align `db.list_all_projects()` call with actual `db.py` API (`list_projects(conn)` or add `list_all_projects()` to db.py)
4. `skills/status-report/scripts/report.py.py`: rename to `report.py`

### Phase 1: Project init end-to-end (INIT-01 through INIT-05)

1. Add `list_all_projects()` to `db.py` (scans PROJECTS_DIR for `*.db` files, opens each, reads project row)
2. Add `projects/.active` sentinel: `_read_active()` and `_write_active(slug)` helpers in `project_session.py`
3. Update `ps.resolve()` multi-project branch to check sentinel before exiting 1
4. Smoke test: `init.py new --name "Test Project" --code TST` → DB created, PROJECT.md created
5. Unittest: `db.py` CRUD functions (INIT-04)

### Phase 2: Requirement elicitation and persistence (ELICIT-01 through PERSIST-01)

1. Add `DRAFT` status to `RequirementStatus` enum (for resumable elicitation)
2. Verify `req_ops.py add` works end-to-end (title, description, type, by)
3. Author `elicit-requirements` SKILL.md: interview protocol, type classification guidance, RequirementType codes
4. Wire `elicit-requirements` skill into `agent.yaml` skills list
5. Integration test: agent elicits one requirement, persists it, readable via `req_ops.py list`

### Phase 3: FRET refinement (ELICIT-03, PERSIST-01 continued)

1. Verify `refine.py pending` and `refine.py show` work against real DB
2. Update `refine-requirements` SKILL.md with explicit field-by-field conversation protocol
3. Verify `refine.py apply` writes `fret_statement` and `fret_fields` correctly
4. Integration test: requirement goes from `open` (no fret) → `open` (with fret)

### Phase 4: Status report output (REPORT-01)

1. Fix `report.py.py` → `report.py`
2. Verify `report.py generate` reads live DB and outputs correct JSON
3. Integration test: project with one FRET-refined requirement → report shows it

### Phase 5: Full end-to-end smoke test

Execute the complete flow: init → elicit → persist → refine → report. Validate each DB write and that `PROJECT.md` reflects current state after each step.

---

## Integration Points with Gitagent Pattern

| Concern | Gitagent Mechanism | This Agent's Implementation |
|---------|-------------------|----------------------------|
| Skill activation | Agent reads `SKILL.md` into context when routing to that skill | Each skill's `description:` field in SKILL.md frontmatter is the routing signal |
| Tool restriction | `allowed-tools:` in SKILL.md frontmatter | `refine-requirements` restricts to `Read Edit Grep Glob`; others should be similarly scoped |
| Script invocation | Agent calls `uv run python <path>` as a Bash tool call | All scripts accept `--project <slug>`, emit JSON stdout, non-zero exit on error |
| State | No framework-level state — agent manages via tools | SQLite is the state store; `project_session.resolve()` is the entry point |
| Sub-agents | `agents/<name>/agent.yaml` for specialized sub-agents | Currently no `agents/` directory — sub-agent for project initiation was planned but not created; flatten into root agent for v1 |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Session state files

**What:** Writing a `.session.json` or similar during elicitation to track partial interview state.

**Why bad:** Creates a third source of truth. Requires sync logic. Goes stale on crash. Claude's context already tracks conversation state within a session.

**Instead:** Use DB-backed `DRAFT` status for resumable state. Use in-context conversation for within-session state.

### Anti-Pattern 2: Eager DB writes during FRET field collection

**What:** Writing each FRET field to the DB as it is confirmed, field by field.

**Why bad:** Partial FRET rows in DB are harder to query ("is this requirement refined?"), require partial-state handling in `refine.py`, and add complexity to `UpdateRecord` diffing.

**Instead:** Assemble the complete FRET statement in-context, then write it atomically in a single `refine.py apply` call.

### Anti-Pattern 3: Single large "requirements-agent" script

**What:** Collapsing all skills into one large Python script or one SKILL.md.

**Why bad:** Violates gitagent skill decomposition principle. Cannot independently test FRET refinement without project init. Skills cannot have different `allowed-tools` constraints.

**Instead:** Maintain skill boundaries. Each skill = one capability = one SKILL.md + one CLI script.

### Anti-Pattern 4: Calling `project_session.resolve()` without `--project` in multi-project envs

**What:** Skill scripts that omit `--project <slug>` when multiple projects exist.

**Why bad:** Current `ps.resolve()` exits 1 when ambiguous — this interrupts the agent conversation with a recoverable error that requires re-invocation.

**Instead:** Implement the `.active` sentinel so `ps.resolve()` can silently auto-select the last-used project. Agent only needs to specify `--project` when explicitly switching.

### Anti-Pattern 5: Encoding FRET grammar in SKILL.md directly

**What:** Duplicating the FRET grammar reference inline in `refine-requirements/SKILL.md`.

**Why bad:** Already solved — `references/fret_grammar.md` exists and the SKILL.md correctly instructs the agent to load it. Duplicating creates drift.

**Instead:** Keep the instruction `MUST READ: load fret_grammar.md before starting` in SKILL.md and leave the grammar in `references/`. This is already correct.

---

## Scalability Considerations (v1 scope)

| Concern | v1 (1 project, <100 reqs) | Future |
|---------|--------------------------|--------|
| Project resolution | Sentinel file sufficient | Add `last_accessed_at` column to projects table |
| Requirement search | `search_requirements()` full scan is fine | sqlite-vec already in place for semantic search |
| FRET refinement throughput | One at a time, interactive | Batch mode: `refine.py apply-all` with pre-generated statements |
| Multi-project agents | Not needed v1 | Workspace-level config (`~/.requirements-agent/default_project`) |
| Import performance | sys.path.insert on every invocation is fine | Package `shared/` if startup time becomes noticeable |

---

*Architecture analysis based on direct codebase reading: 2026-04-21*
*Confidence: HIGH — all findings from authoritative source (the codebase itself)*
