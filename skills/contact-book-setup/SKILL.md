---
name: contact-book-setup
description: > 
    Interview the user or project stakeholder during DS/ML/AI project setup to identify key non-private project contacts, record company contact details in CONTACTS.md, and escalate missing contact names to issue-manager.
license: MIT
allowed-tools: Read Edit Grep Glob
metadata:
    author: aleksander nitka
    version: 1.0.0
    category requirements
---

# Contact Book Project Setup Skill

Use this skill during project setup for data science, machine learning, analytics, automation, or AI projects. Its purpose is to build a project contact book through a Socratic requirements-engineering interview, so future agents know whom to contact for clarifications, approvals, data access, status reporting, escalation, and domain validation.

The skill creates or updates:

```text
projects/<project-slug>/CONTACTS.md
```

Only collect professional, non-private information. Do not collect personal email addresses, private phone numbers, home addresses, personal social media profiles, protected characteristics, or unrelated biographical details.

## Inputs

Required:

- Project name
- Project slug, or enough information to create one
- User or stakeholder available for interview

Optional:

- Existing project directory
- Existing `CONTACTS.md`
- Existing stakeholder list
- Organisation/team structure
- Communication preferences already known

## Output

Create or update `projects/<project-slug>/CONTACTS.md`.

If the user cannot provide the name of a required contact, call the `issue-creator` skill to log the missing contact as an unresolved project setup issue.

## Data collection rules

Collect only company or project-relevant contact information:

- Full name, preferably name and surname
- Company email address
- Role or responsibility in this project
- Department, team, or business unit
- Organisation/company
- Project responsibility category
- Preferred professional communication channel, if relevant
- Decision authority or approval scope
- Availability constraints relevant to the project, if professional and non-private
- Notes about when to involve the person

Do not collect:

- Personal email addresses
- Private phone numbers
- Home address or private location
- Personal messaging handles
- Sensitive personal attributes
- Health, family, political, religious, or other private information
- Performance judgements or gossip

If the user gives private information accidentally, do not write it to `CONTACTS.md`. Instead, ask for a company email or professional contact route.

## Interview style

Use Socratic questions. Do not simply ask for a flat list of contacts. Help the user reason through project risks, dependencies, decision points, data access, ownership, validation, and escalation paths.

Ask concise, progressive questions. Prefer one question at a time when information is uncertain. Group questions only when the user is clearly filling a structured form.

Avoid assuming that a role exists. Ask whether it exists, who holds it, and how they should be contacted.

## Required contact categories

During the interview, try to identify contacts for the following categories. A person may fill more than one category.

### Project ownership

- Project sponsor
- Product owner or business owner
- Delivery/project manager
- Main day-to-day stakeholder

### Data and systems

- Data owner
- Data steward or data governance contact
- Source system owner
- Data engineer or platform engineer
- Cloud/platform owner
- Security or access approver

### Domain and validation

- Domain expert
- Process owner
- End-user representative
- Model/output validator
- UAT lead or acceptance approver

### ML/AI delivery

- Data scientist / ML engineer
- AI engineer / LLM engineer, if applicable
- MLOps or deployment owner
- Monitoring/operations owner
- Responsible person for model risk, compliance, or audit, if applicable

### Communication and escalation

- Status-report recipient
- Steering committee contact
- Escalation contact for blocked access
- Escalation contact for scope or priority conflicts
- Escalation contact for production incidents

## Socratic interview guide

Start with the project context:

1. What decision, workflow, or outcome is this DS/ML/AI project supposed to improve?
2. Who will notice first if the project succeeds?
3. Who will be affected first if the project produces a wrong or misleading result?
4. Who has the authority to say the project is useful enough to proceed?
5. Who can stop or materially delay the project?

Then identify ownership:

1. Who owns the business problem?
2. Who owns the budget, priority, or sponsorship?
3. Who is accountable for day-to-day decisions?
4. Who should receive routine status updates?
5. If scope changes are needed, who decides?

Then identify data responsibilities:

1. What data sources are essential for this project?
2. For each source, who owns the data from a business perspective?
3. Who understands the meaning and limitations of the data?
4. Who can approve access to the data?
5. Who can explain missing values, data quality issues, or unusual patterns?
6. Who owns the source system or pipeline?

Then identify validation and acceptance:

1. Who can judge whether the model, analysis, or AI output is correct enough?
2. Who will define acceptance criteria?
3. Who will run or approve UAT?
4. Who represents the end users?
5. Who should be consulted before results are shared broadly?

Then identify technical delivery and operations:

1. Who will build or maintain the pipeline, model, app, or agent?
2. Who owns deployment infrastructure?
3. Who will monitor quality, drift, failures, or operational issues?
4. Who should be contacted if the system breaks after launch?
5. Who approves release to production?

Then identify governance:

1. Does this project involve personal data, regulated data, automated decisions, or high-impact decisions?
2. If yes, who is the privacy, legal, risk, compliance, security, or audit contact?
3. Who must approve external data sharing, vendor access, or model deployment?
4. Who should review documentation before launch?

Then identify escalation paths:

1. If data access is blocked, who should be contacted first?
2. If priorities conflict, who resolves them?
3. If the project is at risk, who should be escalated to?
4. If a stakeholder does not respond, who is the fallback contact?

For each named person, collect:

1. Full name and surname
2. Company email address
3. Role in the project
4. Department/team
5. Organisation/company
6. When to contact them
7. Whether they are an owner, approver, contributor, reviewer, recipient, or escalation contact

## Missing contact handling

If the user identifies a required role but cannot provide the person's name, do not invent one.

Ask a follow-up Socratic question:

- Who would normally approve or own this in your organisation?
- Which team should know who this is?
- Is there a generic company mailbox or team alias for this function?
- Who could help us identify the right person?

If the name is still unknown, call `issue-manager` with an issue describing the missing contact.

Use this issue format:

```markdown
Title: Missing project contact: <contact category>
Project: <project name>
Priority: <low/medium/high/critical>
Blocking impact: <what is blocked or at risk>
Description: 
	Contact category: <category>
	Why needed: <reason this person is required>
	Known team/department: <team if known, otherwise Unknown>
Suggested next step: <suggested actions>
```

Mark the contact in `CONTACTS.md` as unresolved as well.

## Company email validation

Before writing an email address, check whether it appears to be a company or organisation email.

Accept:

- `name.surname@company.com`
- `firstname.lastname@department.company.org`
- `team-alias@company.com`

Reject or query:

- Free personal email domains such as Gmail, Yahoo, Outlook, Hotmail, Proton, iCloud, or similar, unless the organisation itself legitimately uses that domain and the user explicitly confirms it is the official company route
- Missing email addresses for named individuals, unless the user confirms they are not yet known
- Ambiguous handles without a domain

If an email is missing, write `Unknown` and add a follow-up item.

## CONTACTS.md format

Use the following structure.

```markdown
# Project Contacts

Project: <project name>
Project slug: <project-slug>
Last updated: <YYYY-MM-DD>

## Contact policy

This file contains professional project contact information only. It should not contain personal email addresses, private phone numbers, home addresses, sensitive personal information, or unrelated biographical details.

## Core contacts

| Name | Company email | Project role | Department / team | Organisation | Responsibility type | Contact for | Status |
|---|---|---|---|---|---|---|---|
| <Full name> | <company email> | <role> | <team> | <organisation> | <Owner/Approver/Contributor/Reviewer/Recipient/Escalation> | <when to contact> | Confirmed |

## Escalation paths

| Situation | Primary contact | Fallback contact | Notes |
|---|---|---|---|
| Data access blocked | <name/email> | <name/email> | <notes> |
| Scope or priority conflict | <name/email> | <name/email> | <notes> |
| Production incident | <name/email> | <name/email> | <notes> |
| Stakeholder non-response | <name/email> | <name/email> | <notes> |

## Unresolved contacts

| Needed contact | Why needed | Known team / alias | Blocking impact | Issue status |
|---|---|---|---|---|
| <role/category> | <reason> | <team or alias> | <impact> | Logged via issue-creator |

## Notes

- <Non-private project communication notes only>

## Change log

| Change Date | Change Summary | Change Reason | Change Author |
|---|---|---|---|
| <YYYY-MM-DD> | <short summary> | <reason> | <agent or person>

```

## File path rules

Create a slug from the project name if one is not supplied:

1. Lowercase the name
2. Replace spaces and separators with hyphens
3. Remove characters that are not letters, numbers, or hyphens
4. Collapse repeated hyphens
5. Trim leading and trailing hyphens

Examples:

- `Customer Churn Model` → `customer-churn-model`
- `AI Claims Assistant - Phase 1` → `ai-claims-assistant-phase-1`

Write the file to:

```text
projects/<project-slug>/CONTACTS.md
```

## Updating existing CONTACTS.md

If `CONTACTS.md` already exists:

1. Preserve confirmed contacts unless the user explicitly corrects them.
2. Add new contacts without duplicating existing people.
3. Update `Last updated`.
4. Move resolved entries out of `Unresolved contacts` once a named company contact is supplied.
5. Keep a cautious tone when uncertain; use `Needs confirmation` rather than pretending certainty.

## Completion criteria

The skill is complete when:

- `CONTACTS.md` exists at the correct path
- Core project contacts are recorded where known
- Only company/professional contact details are included
- Missing required contacts are listed as unresolved
- Each unresolved named gap has been passed to `issue-creator`
- The user receives a concise summary of confirmed contacts and outstanding gaps

## Final response format

After creating or updating the file, respond with:

```markdown
Created/updated `projects/<project-slug>/CONTACTS.md`.

Confirmed contacts: <number>
Unresolved contact gaps: <number>
Issues logged through `issue-creator`: <number>

Main gaps:
- <gap 1>
- <gap 2>
```

Do not include private information in the summary.

