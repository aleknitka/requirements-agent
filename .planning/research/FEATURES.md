# Feature Landscape: Requirements Engineering Agent

**Domain:** Conversational requirements engineering for data science / ML / AI projects
**Researched:** 2026-04-21
**Confidence:** MEDIUM-HIGH — based on training knowledge of RE standards (IEEE 830, EARS, FRET, IREB CPRE), commercial RE tools (DOORS, Jama, Polarion, Azure DevOps, ReqIF ecosystem), and ML-specific RE literature. WebSearch unavailable; no live verification.

---

## Grounding: What the Codebase Already Has

Before mapping the feature landscape, note what already exists in `shared/models.py` and skills. This prevents recommending things already built:

- 34 `RequirementType` codes covering functional, NFR, ML-specific (DAT, MOD, MLP, MET, ETH, EXP, ROB, MON, AUD)
- Status lifecycle: `backlog → open → in-progress → done → rejected`
- Priority: `low / medium / high / critical`
- Full audit trail via `UpdateRecord + FieldDiff`
- FRET fields: `scope / condition / component / timing / response`
- Stakeholder roles: `requestor / sponsor / approver / reviewer / informed`
- Dependency model: `internal / external` with optional URL + note
- `ExternalLink` for Confluence, SharePoint, programme trackers
- `ProjectPhase` enum: discovery → definition → development → testing → deployment → operations → closed
- Decision + ActionItem models linked to meeting minutes
- `has_embedding` flag on `RequirementRow` (vector search foundation)

The data model is already well ahead of v1 needs. Feature gaps are in the **agent behaviour** (elicitation, formalisation workflow) and **reporting**, not the schema.

---

## Table Stakes

Features users expect from any RE tool. Missing = product feels incomplete or unusable.

### Elicitation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Structured interview flow with known question sequence | Every RE tool guides practitioners; ad-hoc Q&A produces garbage | Low | Interview checklist already defined in `new-project-initiation/SKILL.md` — build on it |
| Open-ended "tell me about your problem" opening | Stakeholders need to narrate before they enumerate; jumping to lists kills context | Low | First turn must not be a checklist form |
| Clarifying probes on vague answers | "The system should be fast" → "What does fast mean for your users?" | Low-Med | Pairs with FRET refinement; agent must detect vagueness |
| Confirmation / read-back before saving | Users must agree the requirement is correct before it's persisted | Low | Already in FRET refinement process in `fret_grammar.md` |
| Session continuity — resume interrupted interview | Real sessions get interrupted; agent must not lose prior context | Med | `ProjectMeta.status_summary` can hold session state; SQLite persists between calls |
| One requirement at a time, not bulk dump | Novice stakeholders cannot enumerate reliably; one-at-a-time reduces quality collapse | Low | ELICIT-02 is already scoped to "at least one requirement" |

### Classification

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Requirement type assignment (functional vs NFR) | Every RE methodology requires this; DOORS, Jama, Polarion all mandate it | Low | `RequirementType` codes exist; agent must surface them interactively |
| Priority assignment (MoSCoW or equivalent) | Stakeholders always want "all high priority" — agent must push back with ranking | Low | `RequirementPriority` enum exists; MoSCoW mapping: Must=critical/high, Should=medium, Could=low |
| Status tracking through lifecycle | Required for any project tracking; RE tools without status tracking are just text files | Low | `RequirementStatus` enum complete |
| Unique stable identifier per requirement | DOORS uses DXL IDs, Jama uses numeric IDs, Polarion uses module/ID pairs — all stable | Low | `make_req_id()` exists in models.py but references undefined `RequirementArea` — bug to fix |

### Formalisation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Ambiguity detection in natural language | Core RE skill; "shall statements" discipline comes from IEEE 830 and DoD-STD-2167 | Low | FRET grammar already encodes this via vague phrase table |
| Structured "shall" statement output | IEEE 830 §5.2: requirements use "shall" for obligations, "should" for recommendations, "will" for facts | Low | FRET `response` field naturally produces this; `timing` keyword always contains "shall" |
| Mandatory vs optional distinction | IEEE 830 / IREB CPRE: requirement strength is a first-class attribute | Low | `RequirementPriority.CRITICAL` covers "shall", lower priorities cover "should/may" |
| Link from natural language to formal statement | Traceability between stakeholder intent and machine-checkable form | Low | `fret_statement` + `fret_fields` + `description` already provide this pair |

### Persistence

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Immutable audit log per requirement | Compliance, governance, change management all require it | Low | `UpdateRecord + FieldDiff` already built |
| Full snapshot on status change | Regulatory and audit requirement in healthcare, finance, defense | Low | `full_snapshot` in `UpdateRecord`; `SNAPSHOT_ON_STATUSES` constant referenced in architecture |
| Project-scoped storage (no global soup) | Multi-project environments require isolation | Low | Per-project SQLite at `projects/<slug>/<slug>.db` — done |
| Export to structured format (JSON / Markdown) | Stakeholders need output outside the tool; RE artefacts must be portable | Low | `REPORT-01` in active backlog; `status-report` skill already planned |

### Reporting

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Requirement count by type and status | Every status meeting starts with "how many requirements do we have" | Low | Trivial SQL aggregation; `PROJECT.md` regeneration via `md_writer` should include this |
| RAG / health signal (Red-Amber-Green) | Programme management expects a single-signal health indicator | Low | Already defined in `status-report/SKILL.md` with explicit thresholds |
| List of open critical requirements | Immediate action items for stakeholders | Low | SQL filter on `status=open AND priority=critical` |
| FRET coverage percentage | How many requirements have been formalised | Low | `has_embedding` flag pattern can be mirrored; `PROJECT.md` stats already planned |
| Outstanding actions and decisions | Teams need to track what was agreed and by whom | Low | `Decision + ActionItem` models exist; `meeting-agent` skill handles this |

---

## Differentiators

Features that distinguish this agent from commodity RE tools. Valued but not universally expected.

### ML/AI-Specific Elicitation

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| ML-specific question prompts for model behaviour requirements | No generic RE tool knows to ask "what's your acceptable false positive rate?" or "what data drift threshold triggers retraining?" | Med | Embed into `elicitation` skill as ML-aware probe library; trigger when `req_type in {MOD, MLP, MET, ROB}` |
| Fairness/bias elicitation prompts | EU AI Act, NIST AI RMF, IEEE 7010 all require documented fairness criteria; practitioners often skip them | Med | ETH and PRV requirement types exist; agent needs to proactively surface them when domain implies user-facing decisions |
| Data quality requirements structured capture | ML projects fail on data quality more than model quality; stakeholders rarely articulate DQ requirements spontaneously | Med | DAT type exists; agent should ask: completeness threshold, latency SLA, schema drift policy, lineage requirements |
| Model card requirements elicitation | EU AI Act mandates technical documentation; model cards (Google/Hugging Face standard) require specific fields | Med | Could be a dedicated `model-card` skill in v2; for v1, ensure MOD/MLP types capture sufficient fields |
| Probabilistic acceptance criteria | ML requirements often state "accuracy >= X on benchmark Y" not "shall return correct answer" — this is a fundamentally different contract | Med | FRET `response` field can encode this; agent should prompt for metric + threshold + evaluation dataset |

### Formalisation

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| FRET statement assembly with live validation | FRET grammar validation catches structural errors before save; no other conversational agent does this | Med | `refine.py` applies FRET; add field-completeness check: warn if COMPONENT or RESPONSE empty |
| EARS notation as an alternative formalisation | EARS (Easy Approach to Requirements Syntax) is more widely known than FRET in industry; supports 5 patterns | High | EARS patterns: Ubiquitous ("the system shall"), Event-driven ("When X, the system shall"), Unwanted behaviour ("If X, the system shall"), State-driven ("While X, the system shall"), Optional ("Where X, the system shall"). Defer to v2 — FRET is the committed choice |
| Cross-requirement consistency check | Detect contradictory timing constraints on the same component (e.g., "within 10ms" vs "within 1s" for same endpoint) | High | `review-requirements` skill already planned with conflict detection; this is the hard part |
| Requirement smells detection | Patterns that indicate poor quality: use of "and" (compound), "not" without positive statement, passive voice, "TBD", subjective adjectives | Low-Med | Rules-based scan on `description` and `fret_statement`; implement as `review-requirements` check |

### Workflow

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Requirement origin tracing (source → refined) | Traceability from "what stakeholder said" to "what FRET statement was produced"; critical for audit | Low | `raw_notes` in `MinuteIn` + `UpdateRecord` already support this; ensure elicitation records source in `changed_by` field |
| Stakeholder sign-off capture | Formal approval is required in regulated industries; informal for others | Low-Med | `DecisionStatus` and `Decision.made_by` cover this; need an "approved" flow in `RequirementStatus` or via a `Decision` linked to the requirement |
| Context-aware re-elicitation | When a requirement's context changes (new stakeholder joins, scope shifts), agent surfaces affected requirements and prompts re-review | High | Requires embedding-based similarity search — foundation exists via `sqlite-vec` but deferred to v2 |
| Batch import from structured sources | PRDs, Confluence pages, existing Excel trackers — extract requirements from documents | High | Explicitly out of scope for v1; note as clear v2 differentiator |

---

## Anti-Features

Features to explicitly NOT build, especially for v1.

### Over-Engineered for v1

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| MoSCoW voting / multi-stakeholder prioritisation sessions | Requires UI or multi-user session management; adds protocol complexity with no v1 payoff | Single-owner priority assignment via `RequirementPriority`; defer voting to v3+ |
| Version-controlled requirements baselines (like DOORS modules) | Baseline management (freeze, compare, delta) is a full feature domain; DOORS users spend weeks on it | Full audit trail via `UpdateRecord` is sufficient; point-in-time reports via `save` command |
| Traceability matrix generation | Trace from business → user → functional → test is a v3 governance feature; the model supports it but no v1 use case demands it | Dependency links exist in `Dependency` model; expose as optional metadata, not a required workflow |
| Requirement templates library (industry-specific) | Template libraries become stale quickly and encourage copy-paste; drives quantity over quality | FRET refinement is the quality gate; templates would short-circuit it |
| Automated test generation from requirements | Promising but adds a compilation/inference step with high hallucination risk | Explicitly call this v4+; note that FRET → LTL → model checking is the principled path (OGMA/Kind 2) |
| Graphical hierarchy (tree views, modules) | Meaningful only with a UI; CLI output of deep hierarchies is unreadable | Flat list with `predecessors`/`dependencies` links is sufficient; hierarchy is a UI concern |
| Collaborative real-time editing | Requires websockets or CRDT; no v1 multi-user story | Local SQLite model is correct; multi-user is a hosting/sharing concern for v3+ |
| Natural language similarity deduplication on save | sqlite-vec foundation exists but embedding every requirement adds latency to the write path | Flag `has_embedding` as async/background; dedup is v2+ |

### RE Anti-Patterns (things generic tools do that produce bad requirements)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Accepting "TBD" as a valid requirement value | TBD requirements are placeholders that rot; they accumulate and block progress | Block save if `description` is empty or contains only "TBD"; surface as a `review-requirements` gap |
| Unconstrained free-text requirements without formalisation prompt | Raw natural language requirements are the core problem this tool solves | Always offer FRET refinement after capture; never mark status > `open` without `fret_statement` (enforced by `review-requirements`) |
| Silent acceptance of vague priority | If stakeholder says "everything is critical", the priority field is meaningless | When >50% of open requirements are `CRITICAL`, `review-requirements` should flag the calibration issue |
| Infinite requirement types | The 34 codes in `models.py` are already at the upper edge; more creates classification paralysis | Cap at current set; if a new type is genuinely needed, it requires a model version bump |
| Stakeholder-as-requirement-author without validation | Requirements written directly by stakeholders without RE mediation are consistently of lower quality | Agent always mediates; stakeholder input goes through elicitation flow, not direct CRUD |

---

## Feature Dependencies

```
Project exists → Elicitation can start
Elicitation captures raw requirement → Classification assigns type/priority/owner
Classification complete → FRET formalisation can run
FRET formalisation confirmed → PERSIST writes to DB
DB has requirements → Status report can be generated
Status report → covers: counts, RAG, FRET coverage, open actions, open decisions
```

For v1 specifically:
```
INIT-01 (project creation) → ELICIT-01 (interview)
ELICIT-01 → ELICIT-02 (elicit requirement)
ELICIT-02 → ELICIT-03 (classify + FRET refine)
ELICIT-03 → PERSIST-01 (write to DB)
PERSIST-01 → REPORT-01 (status report)
```

---

## ML-Specific Feature Notes

The existing type taxonomy in `models.py` is strong. The agent behaviour layer needs to know when to invoke ML-specific probes. Recommended trigger conditions:

| Trigger | Probe to surface |
|---------|-----------------|
| Project domain mentions model, prediction, inference, scoring | Ask for MOD requirements: accuracy threshold, latency, versioning policy |
| Dataset or training data mentioned | Ask for DAT requirements: schema, quality SLA, lineage, refresh cadence |
| User-facing decisions or recommendations | Ask for ETH requirements: protected attributes, fairness metric, appeal process |
| Regulatory context (healthcare, finance, insurance, HR) | Ask for COM, PRV, ETH requirements as a block |
| Retraining or drift mentioned | Ask for MON + ROB requirements: drift detection method, retraining trigger, rollback policy |
| Performance SLAs mentioned | Ask for PER + REL requirements: P95/P99 latency, availability target |

This is agent behaviour (embedded in SKILL.md instructions), not schema work. The models already accommodate every one of these.

---

## Elicitation: What Question Patterns Work

Based on RE practice (Zowghi & Coulin 2005, IREB CPRE body of knowledge, Leffingwell & Widrig use case approach):

### Opening Patterns (trust-building, context-rich)

1. **Problem narrative**: "Tell me what problem this project is solving. Don't worry about technical details yet."
2. **Current state / pain**: "What does the team do today? Where does it break down?"
3. **Success vision**: "If this project went perfectly, what would be different in 6 months?"

### Elicitation Probes (drilling into a requirement)

4. **Frequency**: "How often does this need to happen?"
5. **Volume**: "How many X are we talking about — 10, 1000, 1 million?"
6. **Failure mode**: "What happens if this doesn't work? Who is affected and how?"
7. **Exception handling**: "What should happen when the input is wrong / missing / late?"
8. **Acceptance criterion**: "How will you know this is done correctly?"
9. **Priority trade-off**: "If you had to choose between X and Y, which would you release first?"
10. **Stakeholder boundary**: "Who owns this requirement? Who needs to approve changes to it?"

### ML-Specific Probes

11. **Performance contract**: "What accuracy/precision/recall is good enough? Is there a benchmark dataset?"
12. **Drift tolerance**: "If model accuracy drops by 5%, does that trigger a manual review or an automatic rollback?"
13. **Explainability need**: "Does the end user or a regulator need to understand why a prediction was made?"
14. **Training data ownership**: "Who owns the training data? What are the usage rights?"
15. **Protected attributes**: "Are any of the input features proxies for age, gender, ethnicity, or other protected characteristics?"

### FRET Refinement Probes (from `fret_grammar.md`)

Already documented in the grammar reference. Agent should use the "common mistakes to catch" table as the refinement checklist.

---

## Persistence: Metadata Fields Standard RE Tools Store Per Requirement

Comparison against commercial tools (DOORS NG, Jama Connect, Polarion, Azure DevOps, Jira + Xray):

| Metadata field | DOORS NG | Jama | Polarion | ADO | This agent | Notes |
|---------------|----------|------|----------|-----|-----------|-------|
| Unique stable ID | Yes | Yes | Yes | Yes | Yes (via `make_req_id`) | Bug: references undefined `RequirementArea` — needs fix |
| Title | Yes | Yes | Yes | Yes | Yes | |
| Description (natural language) | Yes | Yes | Yes | Yes | Yes | |
| Type / category | Yes | Yes | Yes | Partial | Yes (34 codes) | Over-specified vs typical tools; good for ML |
| Status | Yes | Yes | Yes | Yes | Yes | |
| Priority | Yes | Yes | Yes | Yes | Yes | |
| Owner | Yes | Yes | Yes | Yes | Yes | |
| Stakeholders | Partial | Yes | Partial | No | Yes | This agent is stronger than most |
| Dependencies (predecessors/successors) | Yes | Yes | Yes | Yes | Yes | |
| External links | Partial | Yes | Yes | Partial | Yes | |
| Created / updated timestamps | Yes | Yes | Yes | Yes | Yes | |
| Audit log (change history) | Partial | Yes | Yes | Partial | Yes (UpdateRecord) | This agent is stronger than most |
| Full snapshot on key status changes | No | No | No | No | Yes | Differentiator |
| Formal statement (FRET/EARS/Z notation) | No | Partial | Partial | No | Yes | Major differentiator |
| Embedding / vector search | No | No | No | No | Foundation only | Future differentiator |
| Tags | Yes | Yes | Yes | Yes | Yes | |
| Version / baseline | Yes | Yes | Yes | Yes | No | Not needed for v1; UpdateRecord is sufficient |
| Test linkage | Partial | Yes | Yes | Yes | No | v3 traceability feature |
| Risk rating | Partial | No | Partial | No | No | RSK type covers this conversationally |

**Assessment:** The existing `RequirementIn` / `RequirementRow` schema is at parity with or ahead of commercial tools on most fields. The only meaningful gap is test linkage and baseline management — both correctly deferred.

---

## Reporting: What a Useful Status Report Contains

Based on programme management practice (PRINCE2, SAFe, DSDM) and RE-specific tooling (DOORS reports, Jama dashboards):

### Must Have in v1 REPORT-01

| Report Section | Content | Source |
|---------------|---------|--------|
| Project header | Name, code, phase, owner, target date | `ProjectMeta` |
| RAG health signal | RED / AMBER / GREEN with threshold explanation | Thresholds in `status-report/SKILL.md` |
| Requirement counts | Total, by status, by type | SQL aggregation |
| FRET coverage | % of requirements with `fret_statement` | SQL count on `fret_statement IS NOT NULL` |
| Critical open items | List of `status=open AND priority=critical` | SQL filter |
| Open decisions | List from `Decision` where `status=open` | `Decision` table |
| Pending actions | List from `ActionItem` where `done=false` | `ActionItem` table |
| Recent changes | Last 5-10 `UpdateRecord` entries with summary | `UpdateRecord` table ordered by `changed_at DESC` |

### Nice to Have (v2+)

| Report Section | Content | Why Defer |
|---------------|---------|-----------|
| Trend over time | Requirement count, FRET coverage %, open criticals over time | Needs historical snapshots or time-series query |
| Coverage vs success criteria | Which success criteria are covered by at least one requirement | Requires semantic matching or explicit linkage |
| Type distribution chart | Pie/bar of requirements by type | CLI-only tools can output ASCII or defer to UI |
| Stakeholder involvement map | Who owns what, who has reviewed what | Nice governance view; not blocking v1 |
| Risk register extract | Requirements of type RSK sorted by priority | Simple filter; low effort if needed |

---

## MVP Feature Prioritisation for v1

The v1 goal is: init → interview → elicit one requirement → FRET refine → persist → status report.

**Build:**
1. Project interview flow (INIT-01/02) — structured 10-question interview, confirm before save
2. Single requirement elicitation (ELICIT-01/02) — open narrative → one structured requirement
3. Requirement type + priority assignment (ELICIT-03) — interactive type selection from 34 codes (simplified to top 8 in conversation), MoSCoW priority
4. FRET refinement loop (ELICIT-03) — use existing `fret_grammar.md` process; enforce COMPONENT + RESPONSE before accepting
5. Persist + confirm (PERSIST-01) — write `RequirementIn` to DB, display back to user
6. Status report (REPORT-01) — header + counts + RAG + FRET coverage + critical open list

**Explicitly defer:**
- Multi-requirement sessions (ELICIT-02 says "at least one" — stop there for v1)
- Cross-requirement conflict detection (review-requirements skill exists but is v1.5+)
- Meeting integration in report (meeting-agent skill exists; integrate in v2 flow)
- Vector embeddings (foundation exists; don't block v1 writes on it)
- Test linkage, baseline management, traceability matrix

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Elicitation patterns | HIGH | IREB CPRE, Leffingwell, Zowghi — well-established academic + practitioner consensus |
| Classification (FRET, IEEE 830, EARS) | HIGH | Primary sources reviewed (FRET grammar file in repo; IEEE 830-1998 and EARS notation from Hull et al.) |
| ML-specific requirements types | HIGH | Models.py taxonomy cross-checked against NIST AI RMF, EU AI Act requirements, Google Model Card spec |
| Commercial tool feature set | MEDIUM | Training data knowledge of DOORS NG, Jama, Polarion; no live verification |
| Anti-features | MEDIUM | Based on practitioner experience patterns; no formal citation |
| Persistence metadata completeness | MEDIUM | Cross-referenced schema against known commercial tool fields; no live API check |

---

## Sources

- FRET Grammar Reference: `skills/refine-requirements/references/fret_grammar.md` (in-repo)
- Existing data model: `shared/models.py` (in-repo)
- Architecture analysis: `.planning/codebase/ARCHITECTURE.md` (in-repo)
- IEEE 830-1998: IEEE Recommended Practice for Software Requirements Specifications
- EARS notation: Hull, Jackson & Dick, "Requirements Engineering" (3rd ed.), Springer 2011
- IREB CPRE Foundation Level Syllabus (v1.1, 2022)
- FRET tool: NASA Formal Methods — https://github.com/NASA-SW-VnV/fret
- NIST AI RMF 1.0 (2023) — AI risk management framework requirement categories
- EU AI Act (2024) — technical documentation requirements for high-risk AI systems
- Google Model Card specification — https://modelcards.withgoogle.com/
- Zowghi, D. & Coulin, C. (2005). "Requirements Elicitation: A Survey of Techniques, Approaches, and Tools"
