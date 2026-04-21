# Technology Stack Research

**Project:** requirements-agent (brownfield — subsequent milestone)
**Researched:** 2026-04-21
**Research scope:** CLI-driven requirements engineering agent in Python 2025

---

## Current Stack (Confirmed in Codebase)

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.13+ | `pyproject.toml` requires-python = ">=3.13" |
| uv | current | package manager + venv; `uv.lock` committed |
| pydantic | 2.13.3 | validation models; all DB writes go through models first |
| sqlite3 | stdlib | one `.db` per project at `projects/<slug>/<slug>.db` |
| sqlite-vec | 0.1.9 | vector similarity via `vec0` virtual table |
| openai | 2.32.0 | embeddings client (`text-embedding-3-small`, 1536 dims) |
| pytest | 9.0.3 | test runner |
| ruff | 0.15.11 | linter + formatter |
| prek | 0.3.9 | **WARNING: see below** |
| gitagent | convention | architecture pattern; no runtime pip package needed |

### Warning: prek is not a gitagent runtime

`prek` in `pyproject.toml` is a Rust-based pre-commit hook runner (alternative to `pre-commit`), NOT a gitagent framework package. The gitagent pattern is a file-convention standard (`SKILL.md` + `agent.yaml`), not a Python library. Claude Code CLI is the runtime harness. `prek` should be moved to dev tooling or removed if hooks are not yet configured.

---

## Structured CLI Output: JSON stdout/stderr Pattern

**Recommendation: keep the current pattern exactly as-is.**

The existing skill scripts implement the correct pattern for a Claude Code harness agent:

```python
def _ok(data: dict) -> None:
    print(json.dumps({"ok": True, **data}, indent=2, default=str))

def _err(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}), file=sys.stderr)
    sys.exit(1)
```

**Why this is correct:**
- Success payload on stdout with `"ok": true` envelope — harness reads stdout
- Error on stderr with non-zero exit code — harness distinguishes failure
- `default=str` on `json.dumps` handles datetime/UUID without crash
- `indent=2` makes output readable in conversation context
- stdlib only (`json`, `argparse`, `sys`) — no extra dependency

**What NOT to use:**
- **Typer**: designed for human-facing pretty CLI output; adds Click dependency; `json_output` support is bolted on not first-class; overkill for agent-facing scripts
- **Click**: same objection as Typer — human-friendly, not agent-friendly
- **Rich**: excellent for human terminals; has no benefit when stdout is consumed programmatically by the harness

**Augment with Pydantic serialization for complex payloads:**

```python
# Use model_dump_json for nested Pydantic objects in the response
_ok({"requirement": req.model_dump(mode="json")})
```

`mode="json"` ensures datetimes serialise as ISO strings and enums as their `.value` strings. Prefer this over manual `default=str` for structured model data.

---

## Requirements Classification

### The case for LLM-assisted classification (not rule-based NLP)

This agent already runs inside Claude Code with `anthropic/claude-opus-4.6`. Requirements classification is a semantic task that maps free-form text to one of 33 `RequirementType` codes (BUS, FUN, DAT, MOD, MLP, …). LLM-in-context classification outperforms rule-based or traditional NLP for this task:

- The type taxonomy is domain-specific (ML/AI projects) — no pretrained NLP model knows it
- Free-form requirement text is short (1-3 sentences) and high-variance — regex and keyword matching produce poor recall
- The LLM is already present at runtime with zero additional cost

**Recommended approach:** Prompt-based classification in the refine-requirements skill. Pass the `REQUIREMENT_TYPES` list from `models.py` as context, ask the model to assign a type code, and validate the returned code against the enum.

```python
# Validate classification output defensively
valid_codes = {rt.code for rt in REQUIREMENT_TYPES}
if assigned_code not in valid_codes:
    # fall back to FUN or ask the model to retry
```

**When rule-based classification IS appropriate:**
- Pre-screening: quick keyword filters to narrow the candidate type list before prompting (reduces token use)
- Post-validation: regex checks that a FRET statement contains required keywords (`shall`, component name)

### Python NLP libraries — situational use only

| Library | Use case | Verdict |
|---------|----------|---------|
| spaCy 3.x | Named entity extraction (stakeholder names, system names from text), dependency parsing | MEDIUM confidence — useful for entity extraction in meeting-agent, not needed for v1 |
| transformers (HuggingFace) | Fine-tuned requirement classifiers | Do NOT add — massive dependency, training data not available, LLM-in-context is better |
| NLTK | Tokenisation, basic POS tagging | Do NOT add — superseded by spaCy and LLMs |
| re (stdlib) | FRET field extraction (scope/condition patterns), keyword guards | Use freely — no new dependency |

**v1 recommendation:** No NLP library beyond stdlib `re`. Classification is handled by the LLM. Add spaCy only if entity extraction from meeting transcripts is needed (v2).

---

## FRET Grammar Tooling

### State of NASA FRET in 2025

**Confirmed (HIGH confidence via Context7):**

NASA FRET (`/nasa-sw-vnv/fret`) is an Electron desktop application. Its parser (`FretSemantics`) is written in JavaScript and lives in `app/parser/FretSemantics.js`. There is **no official Python port of the FRET parser**.

The tool exposes:
- A GUI for writing FRETish sentences and seeing temporal logic output
- JSON import/export of requirements (`reqid`, `project`, `fulltext`, `semantics`)
- A `fretcli` bash wrapper for batch formalisation (`fretcli formalize '...' --logic ft-inf`)
- IPC handlers for Electron (JavaScript-only internal API)

**What this means for the project:**

There is no `pip install fret` or Python API. The FRET grammar is defined in restricted English:

```
[SCOPE] [CONDITION] the [COMPONENT] shall [TIMING] [RESPONSE]
```

**Recommended implementation strategy:** Continue the current approach — use the FRET grammar reference document (`skills/refine-requirements/references/fret_grammar.md`) as an LLM prompt context, and validate the output with a lightweight Python regex/rule checker rather than a full parser.

A minimal Python validator to confirm basic FRET structure is sufficient:

```python
import re

FRET_SHALL_PATTERN = re.compile(
    r"the\s+\S+\s+shall\s+(always|never|eventually|immediately|within\s+\S+)?",
    re.IGNORECASE
)

def is_valid_fret_structure(statement: str) -> bool:
    return bool(FRET_SHALL_PATTERN.search(statement))
```

**If formal machine-checking is needed (future):** Call the `fretcli` subprocess from Python and parse stdout JSON. This is a v3 concern, not v1.

**What NOT to do:**
- Do not attempt to call FRET's JavaScript API from Python via subprocess JSON bridge — fragile, requires Node runtime, not worth the complexity for v1
- Do not implement a full LTL formula generator in Python — this is formally complex and the LLM can provide the logical reading in natural language

---

## sqlite-vec Usage Patterns

**Confirmed (HIGH confidence via Context7):**

The existing `db.py` implementation is broadly correct. Specific patterns to keep:

```python
# Correct: struct.pack for binary format (fastest, confirmed canonical)
def serialize_f32(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)
```

**Key confirmed patterns from sqlite-vec docs:**

1. `sqlite_vec.load(conn)` is the correct load call (already in `db.py`)
2. `distance_metric=cosine` can be specified at table-creation time in the DDL — the current `req_embeddings` table uses default L2; for semantic text similarity, cosine distance is preferable. Consider adding `distance_metric=cosine` at schema migration time.
3. KNN query syntax: `WHERE embedding MATCH ? AND k = ?` — confirmed correct in `db.py`

**Current bug in `db.py`:** `get_db(path: str = C.DB_PATH)` — `C.DB_PATH` does not exist in CONSTANTS. This must be fixed before any DB operation works. The default should be derived from `C.db_path(slug)` or removed in favour of mandatory slug passing.

**sqlite-vec version note:** 0.1.9 is the version in lockfile. The library is actively developed; check for breaking changes when upgrading. The `USING vec0(...)` virtual table API is stable.

**What NOT to do:**
- Do not use `pgvector` or any Postgres-based vector extension — the project is SQLite-first by design decision
- Do not replace sqlite-vec with FAISS or Chroma — they require separate processes or heavier dependencies and break the local-first constraint
- Do not store vectors as JSON arrays in a regular column — performance is 50-100x worse than the binary `vec0` virtual table

---

## OpenAI Embeddings Client

**Current:** `openai>=2.32.0`, `text-embedding-3-small`, 1536 dimensions.

**Confirmed (HIGH confidence via Context7):**

```python
from openai import OpenAI

client = OpenAI(api_key=key, base_url=base_url)
response = client.embeddings.create(model=model, input=text)
embedding = response.data[0].embedding  # list[float], len=1536
```

This is exactly the pattern in `db.py`. No changes needed.

**Alternatives if API key is unavailable:**
- `EMBEDDING_API_BASE` env var allows pointing to any OpenAI-compatible endpoint (Ollama, LM Studio, vLLM) — this is already wired in `CONSTANTS.py`
- For completely offline v1 operation: skip embedding generation silently (already implemented in `_store_embedding` — it returns early if no API key)

---

## Python Requirements Engineering Libraries

**Research finding: no mature Python RE library worth adopting.**

The Python RE tooling ecosystem in 2025 is thin. What exists:

| Library/Tool | Status | Assessment |
|---|---|---|
| `reqif` (Siemens ReqIF) | Active, niche | XML-based interchange format for enterprise RE tools (DOORS, Polarion). Not useful unless integrating with enterprise tooling. |
| `doorstop` | Maintained, small community | Markdown-based requirements management, file-per-requirement. Conflicts with the SQLite + FRET approach and the gitagent architecture. Do not adopt. |
| `strictdoc` | Active 2024-2025 | Python tool for structured requirements docs (ReqIF, RST, HTML). Heavy; doc-generation focus; does not add value over the existing Pydantic + SQLite layer. |
| `reqpy` | Minimal, low adoption | Thin wrapper; no active community. Not useful. |

**Conclusion:** None of these add value to this stack. The project has a better-designed requirements model (Pydantic + 33-type taxonomy + FRET fields) than any of these tools provide. Do not add any RE library as a dependency.

---

## What NOT to Add (Summary)

| Technology | Reason to avoid |
|------------|----------------|
| Typer / Click | Human-friendly CLI; overkill for agent-facing scripts; `argparse` is sufficient |
| Rich | Terminal display library; agent reads stdout programmatically, not visually |
| spaCy | Not needed for v1; add only if meeting transcript entity extraction is built |
| NLTK | Superseded; no use case here |
| HuggingFace transformers | Massive dependency; LLM-in-context is better for this domain |
| FRET Python parser (custom) | Not worth building; LLM + regex validation is sufficient for v1 |
| doorstop / strictdoc | Competing architecture; conflicts with existing design |
| FAISS / Chroma / pgvector | Overkill for local SQLite-first design; sqlite-vec is correct choice |
| SQLAlchemy / SQLModel | Abstraction layer over sqlite3 adds complexity without benefit for this schema |

---

## Recommended Additions for v1

Minimal additions only — the stack is essentially complete.

| Addition | Purpose | Priority |
|----------|---------|---------|
| `pytest-cov` (dev) | Coverage reporting for DB unit tests (INIT-04 requirement) | HIGH |
| `python-dotenv` (optional) | Load `.env` for `OPENAI_API_KEY` in dev without exporting to shell | MEDIUM |

Both can be added as dev dependencies (`uv add --dev pytest-cov python-dotenv`).

---

## Bugs Requiring Stack-Level Attention

These are not library choices but code bugs that affect the stack's correctness:

1. **`C.DB_PATH` does not exist** — `get_db()` default argument references a non-existent CONSTANTS attribute. All DB opens will fail. Fix: remove the default, require callers to always pass a path, or add `DB_PATH` to CONSTANTS as a sentinel/deprecated path.

2. **`RequirementArea` is referenced but not defined** — `models.py` lines 267, 273 reference `RequirementArea` (and `RequirementArea.CORE`), but only `RequirementType` is defined. This will raise a `NameError` at import. The enum structure needs reconciling — `RequirementType` is currently a `BaseModel` with `code`/`name`/`description`, but `RequirementIn.req_type` calls `.value` on it (which a `BaseModel` doesn't have). The type field needs to either be a string code or a proper `Enum`.

3. **`prek` dependency is miscategorised** — `prek` is a git-hook runner, not a runtime dependency. Move to dev dependencies or remove if git hooks are not yet in use.

4. **`import shared.db` binding** in `init.py` binds `shared`, not `db`. Should be `import shared.db as db`.

---

## Confidence Levels

| Area | Confidence | Source |
|------|------------|--------|
| Current stack versions | HIGH | `pyproject.toml`, `uv.lock` read directly |
| JSON stdout/stderr pattern | HIGH | Existing skill scripts; aligns with gitagent conventions |
| sqlite-vec vec0 API | HIGH | Context7 `/asg017/sqlite-vec` — confirmed current API |
| OpenAI embeddings API | HIGH | Context7 `/openai/openai-python` — confirmed v1.x API |
| NASA FRET: JavaScript-only, no Python port | HIGH | Context7 `/nasa-sw-vnv/fret` — parser is JS, CLI is bash |
| gitagent is a convention, not a pip package | HIGH | Context7 `/open-gitagent/gitagent`; `prek` is pre-commit tool |
| LLM-in-context for classification (vs NLP libs) | MEDIUM | Reasoning from architecture + domain; no direct benchmark |
| Python RE library landscape | MEDIUM | Context7 search + training knowledge; no active community signals available without web search |
