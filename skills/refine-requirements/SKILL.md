---
name: refine-requirements
description: >
  Refine requirements to be precise and testable using FRET (NASA) grammar. Use this skill when the user asks to "refine requirements", "formalise requirements", "apply FRET", "make requirements more specific", "check which requirements are vague", "what requirements need refinement", or when moving from discovery to definition phase. The agent works interactively with the user, proposing FRET statements and confirming before writing back.
license: MIT
allowed-tools: Read Edit Grep Glob
metadata:
  author: aleksander nitka
  version: "1.0.0"
  category: requirements
---

# Refine Requirements Skill
 
Applies FRET (Formal Requirements Elicitation Tool) grammar to make requirements
unambiguous and machine-checkable.
 
## MUST READ before starting
Load `skills/refine-requirements/references/fret_grammar.md` — it contains the
full FRET field reference, examples, common mistakes, and the agent refinement
process. Read it in full before interacting with the user.
 
## FRET statement structure
```
[SCOPE] [CONDITION] the COMPONENT shall [TIMING] RESPONSE
```
 
## Interactive refinement loop
 
1. Run `uv run refine pending` to find requirements needing refinement
2. Pick the highest-priority one (or let user choose)
3. Run `show` to read the current title and description
4. Follow the FRET refinement process in fret_grammar.md:
   - Identify missing/vague fields
   - Ask the user targeted questions
   - Propose a FRET statement
   - Confirm with user
5. Run `apply` to write the confirmed statement

## Commands
 
```bash
uv run refine pending [--project <slug>]           # what needs refinement
uv run refine show   --id REQ-DATA-XXXX [--project <slug>]
uv run refine apply  \
  --id REQ-DATA-XXXX --by "<agent>" \
  --fret-statement "the X shall within 100ms do Y" \
  --fret-fields '{"scope":"","condition":"","component":"the X","timing":"within 100ms","response":"do Y"}' \
  [--description "<updated plain language description>"] \
  [--project <slug>]
uv run refine coverage [--project <slug>]          # % with FRET
```
