# FRET Grammar Reference
## Formal Requirements Elicitation Tool (NASA)

FRET is a NASA tool for writing unambiguous, machine-checkable requirements.
This reference teaches the agent how to apply FRET grammar during the
requirement refinement skill.

---

## Why FRET?

Natural language requirements are ambiguous. "The system should respond quickly"
says nothing testable. FRET forces you to specify:
- **Who** is involved (scope, component)
- **When** it applies (condition)
- **What must happen** (response)
- **How fast / how often** (timing)

A FRET statement can be directly mapped to formal logic (LTL/MTL) and
fed into model checkers like NASA's OGMA or Kind 2.

---

## FRET Statement Structure

```
[SCOPE] [CONDITION] the [COMPONENT] shall [TIMING] [RESPONSE]
```

All fields except **COMPONENT** and **RESPONSE** are optional, but the more
fields you fill in, the more testable the requirement becomes.

---

## Fields in Detail

### 1. SCOPE
**What:** The operating mode or system state in which the requirement applies.

**Syntax:** `In <mode_name>,`  or  `When in <mode_name>,`

**Examples:**
- `In landing mode,`
- `In normal operation,`
- `During data ingestion,`
- *(omit if the requirement applies in all modes)*

**Guidance:** Use scope when the requirement only applies to a specific phase
or mode. Without scope, the requirement is assumed to apply always.

---

### 2. CONDITION
**What:** A trigger or precondition that must be true for the requirement to
activate. Think of it as the "if" clause.

**Syntax:** `if <condition_expression>,`

**Examples:**
- `if user_authenticated is true,`
- `if request_rate exceeds 1000 per second,`
- `if sensor_data is available,`
- *(omit for requirements that are unconditional)*

**Guidance:** Conditions reference observable system inputs or states. They
should be boolean expressions or thresholds, not vague descriptions.

---

### 3. COMPONENT
**What:** The system, subsystem, or software component that has the obligation.
This is **required**.

**Syntax:** `the <component_name>`

**Examples:**
- `the inference service`
- `the authentication module`
- `the data pipeline`
- `the monitoring agent`

**Guidance:** Be specific — use the actual component name from your architecture.
Avoid "the system" unless the requirement truly applies to the whole system.

---

### 4. TIMING  (the most nuanced field)
**What:** Constrains *when* or *how quickly* the response must occur.
This is where most natural language requirements are weakest.

**Syntax options:**

| Timing keyword       | Meaning                                        | Example                          |
|----------------------|------------------------------------------------|----------------------------------|
| `shall always`       | Must hold at every moment (invariant)          | `shall always encrypt data`      |
| `shall never`        | Must never occur                               | `shall never expose PII`         |
| `shall eventually`   | Must happen at some point (no time bound)      | `shall eventually notify user`   |
| `shall immediately`  | Must happen in the next computational step     | `shall immediately reject`       |
| `shall within T`     | Must happen within time bound T                | `shall within 100ms respond`     |
| `shall after E`      | Must happen after event E occurs               | `shall after login complete`     |
| `shall at most N times` | Frequency constraint                        | `shall at most 3 times retry`    |
| `shall`  (bare)      | Must hold — timing is contextual               | `shall log the transaction`      |

**Guidance:** Always prefer a time-bound (`within T`) over vague terms like
"quickly" or "in a timely manner". If you cannot specify a time, use
`shall eventually` and note it needs a bound in the next review.

---

### 5. RESPONSE
**What:** The observable action or property that must hold. This is **required**.
It describes what the component does or what state it achieves.

**Syntax:** a verb phrase describing the action or state

**Examples:**
- `respond with an HTTP 200 status code`
- `encrypt all data at rest using AES-256`
- `log the event with timestamp and user_id`
- `reject the request and return error code 429`
- `store the feature vector in the feature store`

**Guidance:**
- Use active voice: "log the event", not "the event shall be logged"
- Reference specific values, formats, or standards where known
- Avoid adjectives without definitions: "secure" → "AES-256 encrypted";
  "fast" → "within 100ms"

---

## Complete Examples

### Before FRET (typical natural language)
> The system should quickly respond to user requests and handle errors gracefully.

**Problems:** "quickly" is undefined, "gracefully" is undefined, no component
named, no condition, no timing.

### After FRET
> `the API gateway shall within 200ms return an HTTP response to the client`

> `if an upstream service returns a 5xx error, the API gateway shall within 500ms return HTTP 503 with a Retry-After header to the client`

---

### Before FRET
> Data must be stored securely.

### After FRET
> `the data pipeline shall always encrypt data at rest using AES-256 before writing to the feature store`

---

### Before FRET
> The model must meet EU AI Act requirements.

### After FRET
> `In user-facing mode, the recommendation engine shall always provide a human-readable explanation of the top recommendation reason to the end user`

> `the compliance module shall within 30 days of a user request provide a record of all automated decisions made about that user`

---

## FRET Fields JSON Structure

When storing a refined requirement, populate `fret_fields` as:

```json
{
  "scope":     "In normal operation",
  "condition": "if request_rate exceeds threshold",
  "component": "the inference service",
  "timing":    "within 100ms",
  "response":  "return a ranked list of recommendations to the client"
}
```

And `fret_statement` as the assembled sentence:

```
In normal operation, if request_rate exceeds threshold, the inference service shall within 100ms return a ranked list of recommendations to the client.
```

---

## Agent Refinement Process

When refining a requirement with the user, follow this sequence:

1. **Read** the current title and description to the user.
2. **Identify gaps**: Which FRET fields are missing or vague?
   - No component? Ask: "Which system component owns this?"
   - Vague timing? Ask: "Do you have a time bound in mind? E.g. within 100ms?"
   - No condition? Ask: "Does this always apply, or only in certain states?"
3. **Propose** a FRET statement based on answers.
4. **Confirm** with the user — show the full statement and ask for approval.
5. **Write back** via `req_ops.py update` with `--fret-statement` and `--fret-fields`.
6. **Log** the refinement as an update with summary "FRET statement applied."

---

## Common Mistakes to Catch

| Vague phrase              | Ask instead                              |
|---------------------------|------------------------------------------|
| "quickly" / "fast"        | "Within how many milliseconds/seconds?"  |
| "securely"                | "Which encryption standard or protocol?" |
| "the system"              | "Which specific component?"              |
| "should" / "may"          | "Is this a hard requirement (shall)?"    |
| "gracefully"              | "What is the exact error behaviour?"     |
| "as needed"               | "What triggers this? Define the condition"|
| "in real time"            | "What is the maximum acceptable latency?"|
| "regularly" / "often"     | "What is the maximum allowed interval?"  |
| "appropriately"           | "What specific action is expected?"      |

---

## Requirement Types and Typical FRET Patterns

| Type       | Typical timing    | Typical response pattern                        |
|------------|-------------------|-------------------------------------------------|
| CORE       | `shall always`    | Invariants, architectural properties            |
| DATA       | `shall within T`  | Freshness, throughput, storage guarantees       |
| MODEL      | `shall within T`  | Latency, accuracy thresholds, versioning        |
| INFRA      | `shall always`    | Availability, capacity, durability              |
| OPS        | `shall within T`  | Alerting time, recovery time objectives         |
| UX         | `shall within T`  | Response time, feedback, accessibility          |
| COMPLIANCE | `shall always`    | Data handling, disclosure, audit logging        |