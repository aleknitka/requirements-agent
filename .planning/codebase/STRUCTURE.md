# Codebase Structure

**Analysis Date:** 2026-04-21

## Directory Layout

```
requirements-agent/
├── agent.yaml                    # Root agent spec (model, skills, compliance)
├── main.py                       # Minimal stub entry point
├── pyproject.toml                # Python packaging + dependencies
├── uv.lock                       # Dependency lockfile
├── RULES.md                      # Agent behavioral constraints
├── SOUL.md                       # Agent identity and communication style
├── AGENTS.md                     # Top-level agent documentation
├── CLAUDE.md                     # Claude Code instructions
│
├── shared/                       # Shared library (all skills import from here)
│   ├── CONSTANTS.py              # Paths, embedding config, path helpers
│   ├── models.py                 # Pydantic validation models
│   ├── db.py                     # SQLite CRUD + vector search
│   ├── md_writer.py              # PROJECT.md generation/maintenance
│   └── project_session.py        # Project resolution helper
│
├── agents/                       # Specialized sub-agents
│   └── project-initiation-assistant/
│       ├── agent.yaml            # Sub-agent spec
│       ├── SOUL.md               # Sub-agent identity
│       └── skills/
│           └── new-project-initiation/
│               ├── SKILL.md      # Skill instructions + frontmatter
│               └── scripts/
│                   └── init.py   # CLI: create/update/list projects
│
├── skills/                       # Root agent skills
│   ├── project-update/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── req_ops.py        # CLI: requirement CRUD, search, history
│   ├── refine-requirements/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── fret_grammar.md   # Full FRET field reference + examples
│   │   ├── refine.py             # CLI at skill root (alternate location)
│   │   └── scripts/
│   │       └── refine.py         # CLI: FRET refinement commands
│   ├── review-requirements/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── review.py         # CLI: gap/conflict/coverage analysis
│   ├── status-report/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── report.py         # CLI: health signal + stats report
│   └── meeting-agent/
│       ├── SKILL.md
│       └── scripts/
│           └── meeting.py        # CLI: meeting log, decisions, actions
│
├── tests/
│   └── test_init.py              # Unit tests for init.py (project creation)
│
├── projects/                     # Runtime data (per-project, gitignored)
│   └── <slug>/
│       ├── <slug>.db             # SQLite database for the project
│       └── PROJECT.md            # Auto-generated project status document
│
├── compliance/
│   ├── risk-assessment.md        # Completed risk assessment template
│   ├── regulatory-map.yaml       # Regulatory framework mapping
│   └── validation-schedule.yaml  # Model validation schedule
│
├── config/
│   └── default.yaml              # Runtime defaults + hook definitions
│
├── hooks/
│   ├── hooks.yaml                # Hook event → script mappings
│   └── scripts/
│       ├── on-start.sh           # Session start: load project context
│       └── on-error.sh           # Error handler / escalation
│
├── knowledge/
│   └── index.yaml                # Knowledge document index (currently empty)
│
├── memory/
│   ├── memory.yaml               # Memory layer config (working + archive)
│   └── archive/                  # Archived memory entries (YAML, quarterly rotation)
│
├── tools/                        # Custom tool definitions (currently empty)
├── workflows/                    # Workflow definitions (currently empty)
│
└── .planning/
    └── codebase/                 # GSD codebase analysis documents
```

## Directory Purposes

**`shared/`:**
- Purpose: Single shared library imported by all skill scripts via `sys.path.insert(0, str(_ROOT / "shared"))`
- Contains: Path constants, Pydantic models, SQLite CRUD, markdown generation, project session resolver
- Key files: `CONSTANTS.py`, `models.py`, `db.py`, `md_writer.py`, `project_session.py`

**`agents/`:**
- Purpose: Specialized sub-agents with narrower scope than the root agent
- Contains: Each sub-agent has its own `agent.yaml`, `SOUL.md`, and a `skills/` subdirectory
- Key files: `agents/project-initiation-assistant/agent.yaml`, `agents/project-initiation-assistant/skills/new-project-initiation/scripts/init.py`

**`skills/`:**
- Purpose: Root agent skill implementations — one directory per capability
- Contains: `SKILL.md` (LLM instructions with YAML frontmatter), `scripts/` (Python CLI executables), `references/` (domain reference docs)
- Key files: `skills/refine-requirements/references/fret_grammar.md` (critical FRET reference)

**`projects/`:**
- Purpose: Runtime data storage — created at agent runtime, not committed to git
- Contains: One subdirectory per project, each with a SQLite `.db` file and a `PROJECT.md`
- Generated: Yes — created by `init.py new` and `db.get_db()`
- Committed: No (runtime data)

**`tests/`:**
- Purpose: Automated unit tests
- Contains: `test_init.py` — tests for project creation, argument parsing, output helpers
- Key files: `tests/test_init.py`

**`compliance/`:**
- Purpose: Regulatory and risk documentation templates
- Contains: Pre-filled risk assessment, regulatory map, validation schedule
- Generated: No — manually authored templates

**`hooks/`:**
- Purpose: Session lifecycle automation via shell scripts
- Contains: `hooks.yaml` (event → script mapping), `scripts/` (shell scripts)
- Key files: `hooks/scripts/on-start.sh`, `hooks/scripts/on-error.sh`

**`config/`:**
- Purpose: Default runtime configuration
- Contains: `default.yaml` with `log_level`, `compliance_mode`, and hook references

**`memory/`:**
- Purpose: Agent memory persistence (working memory + quarterly archive)
- Contains: `memory.yaml` (layer config), `archive/` directory for rotated YAML entries

## Key File Locations

**Entry Points:**
- `agent.yaml`: Root agent specification — start here to understand the agent
- `agents/project-initiation-assistant/agent.yaml`: Project initiation sub-agent
- `main.py`: Minimal Python entry point (stub only)

**Shared Library:**
- `shared/CONSTANTS.py`: All path configuration and embedding settings
- `shared/models.py`: All Pydantic data models — reference before any DB write
- `shared/db.py`: Complete SQLite API — all DB functions documented in module docstring
- `shared/md_writer.py`: `PROJECT.md` generation logic
- `shared/project_session.py`: `resolve(slug)` — first call in every skill script

**Skill CLIs:**
- `agents/project-initiation-assistant/skills/new-project-initiation/scripts/init.py`
- `skills/project-update/scripts/req_ops.py`
- `skills/refine-requirements/scripts/refine.py`
- `skills/review-requirements/scripts/review.py`
- `skills/status-report/scripts/report.py`
- `skills/meeting-agent/scripts/meeting.py`

**Domain Reference:**
- `skills/refine-requirements/references/fret_grammar.md`: FRET grammar — must be loaded before any refinement work

**Behavioral Constraints:**
- `RULES.md`: Hard behavioral rules for the agent (escalation, PII, audit)
- `SOUL.md`: Agent identity and communication style

## Naming Conventions

**Files:**
- Skill scripts: lowercase with underscores (`req_ops.py`, `md_writer.py`)
- Shared modules: UPPERCASE for constants (`CONSTANTS.py`), lowercase for others
- Test files: `test_<subject>.py`

**Directories:**
- Skills: kebab-case (`refine-requirements`, `project-update`, `meeting-agent`)
- Agents: kebab-case (`project-initiation-assistant`)
- Projects (runtime): kebab-case slug derived from project name via `slugify()` in `CONSTANTS.py`

**Identifiers:**
- Requirement IDs: `REQ-<TYPE>-<8-char-UUID>` (e.g., `REQ-DATA-3F2A1B4C`)
- Decision IDs: `DEC-<8-char-UUID>`
- Action IDs: `ACT-<8-char-UUID>`

## Where to Add New Code

**New Skill (root agent):**
- Create directory: `skills/<skill-name>/`
- Add instructions: `skills/<skill-name>/SKILL.md` with frontmatter (`name`, `description`, `license`, `allowed-tools`, `metadata`)
- Add CLI script: `skills/<skill-name>/scripts/<name>.py`
- Register in root agent: add skill name to `agent.yaml` under `model.skills`
- Follow shared library import pattern: `sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))`

**New Sub-Agent:**
- Create directory: `agents/<agent-name>/`
- Add `agents/<agent-name>/agent.yaml` (see `agents/project-initiation-assistant/agent.yaml` as template)
- Add `agents/<agent-name>/SOUL.md`
- Add skills under `agents/<agent-name>/skills/`
- Add delegation triggers to root `agent.yaml`

**New Shared Module:**
- Add to `shared/<module>.py`
- Follows same `sys.path.insert` import pattern as existing modules
- Add constants/config to `shared/CONSTANTS.py`, not inline in modules

**New Pydantic Model:**
- Add to `shared/models.py`
- Use `BaseModel` from pydantic; add enums near top of file
- Validate all fields; use `Field(default_factory=...)` for mutable defaults

**New Tests:**
- Add to `tests/test_<subject>.py`
- Use `monkeypatch` to mock `db` and `ps` modules (see `tests/test_init.py` for pattern)
- Pre-inject mocks for broken imports via `sys.modules.setdefault()` before module loading

**Reference Material:**
- Place in `skills/<skill-name>/references/`
- Reference from `SKILL.md` with explicit load instruction (see `skills/refine-requirements/SKILL.md`)

## Special Directories

**`projects/`:**
- Purpose: Runtime project data (SQLite DBs and generated Markdown)
- Generated: Yes — created by `shared/CONSTANTS.py` `project_dir()` helper
- Committed: No — contains user data; add to `.gitignore` if not already

**`.venv/`:**
- Purpose: Python virtual environment created by `uv sync`
- Generated: Yes
- Committed: No

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents
- Generated: Yes (by GSD tooling)
- Committed: Optional (analysis artifacts)

**`tools/` and `workflows/`:**
- Purpose: Reserved for custom tool definitions and workflow specs
- Currently: Empty
- Committed: Yes (empty directories)

---

*Structure analysis: 2026-04-21*
