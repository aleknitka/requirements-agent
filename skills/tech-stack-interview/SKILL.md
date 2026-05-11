---
name: tech-stack-interview
description: >
  Gathers information about the key technological platforms and applications used in the organisation.
license: MIT
allowed-tools: Read Grep Glob Bash Write Edit
metadata:
  author: aleksander nitka
  version: "2.0.0"
  category: requirements
---

# Enterprise Tech Stack Context Interview Skill

## Purpose
This skill guides an AI agent through a structured interview for gathering enterprise technology context when onboarding a new project.
The goal is to understand the environment the project must live in, not to design the solution yet.
The output should help a newcomer understand systems, data, integrations, access, delivery, governance, risks, and practical constraints.
The agent must produce `knowledge/<project>/tech-stack-context.md` so multiple projects can coexist without overwriting one another.
The interview should be Socratic, practical, and sceptical without becoming adversarial.

## When To Use This Skill
- Use during onboarding for software, data, AI, ML, automation, reporting, integration, migration, or platform projects.
- Use before requirements engineering, architecture design, agent design, or implementation planning.

## When Not To Use This Skill
- Do not use it to gather detailed functional requirements.
- Do not use it to produce a target-state architecture.
- Do not use it to replace security, privacy, legal, procurement, or architecture review.

## Interview Principles
- Ask one focused question at a time where possible.
- Start broad, then go deeper only where the project depends on detail.
- Use plain language and explain technical terms when needed.
- Accept partial answers and mark uncertainty clearly.
- Separate confirmed facts from assumptions and guesses.
- Ask for examples when answers are vague.
- Probe for the difference between official process and actual practice.
- Look for shadow systems, spreadsheets, manual handoffs, and undocumented scripts.
- Look for single points of failure in people, systems, data, and integrations.
- Treat `I do not know` as useful information.
- Log important unknowns instead of forcing the user to guess.

## Safety And Privacy Rules
- Never ask for or store credentials.
- Never ask the user to paste secrets or production tokens.
- If credentials are exposed, advise rotation and do not store the value.
- Record sensitive data only at a safe summary level.
- Do not collect customer personal records.
- Do not collect employee private information.
- Do not suggest external AI use with internal data unless policy allows it.
- Escalate privacy, security, or compliance uncertainty by creating an issue via the requirements MCP (`create_issue` tool, type `RSK` or `BLK`) so the risk lands in the tracked issue system, not in a loose file.

## Required Outputs

```text
knowledge/<project>/tech-stack-context.md
```

- If the project name is unknown, ask once.
- If the user cannot provide a name, use `project` as the directory.
- The `<project>` segment must be a filename-safe slug (lower-case, `[a-z0-9_-]+`); fall back to `project` when the supplied name cannot be slugified.
- Do not overwrite files owned by other skills.
- If `knowledge/tech-stack-context.md` already exists, ask the user before overwriting; offer to update in place or to refuse.
- Reference related files rather than duplicating them.

## Interview Scope

### Enterprise Stack Overview
- What are the main technology platforms used in the organisation?
- Is the organisation mostly cloud-based, SaaS-heavy, on-premise, private cloud, or hybrid?
- Which cloud providers are used?
- Are data centres, private cloud, or mainframe systems still important?
- Which platforms are strategic, tolerated, being introduced, or being retired?
- Which platforms are discouraged or forbidden?
- What is the simplest honest explanation of the current stack for a newcomer?
- Is there a current enterprise architecture diagram or technology catalogue?
- Where is architecture documentation stored and who maintains it?

### Core Business Applications
- What are the core business applications?
- What is used for ERP, CRM, HR, finance, procurement, support, ITSM, documents, contracts, product information, and master data?
- What industry-specific systems are important?
- Which systems are company-wide and which are department-specific?
- Which systems are business-critical?
- Which systems are legacy but essential?
- Which systems are disliked but unavoidable?
- Which systems are being replaced?
- Which systems contain customer, employee, financial, operational, legal, or contractual data?
- Which systems are sources of truth?
- Which systems should a newcomer never update directly?


### Data And Analytics Landscape
- What operational systems hold the source data?
- What data warehouse, data lake, lakehouse, or databases are relevant?
- What BI or reporting tools are used?
- Are shared data models, business definitions, data dictionaries, catalogues, or lineage tools available?
- Who owns data quality, access approval, KPI definitions, and conflicts between numbers?

### Data Movement
- How does data move between systems?
- Is data moved through APIs, replication, ETL, ELT, files, scheduled exports, email attachments, copy-paste, or streaming?
- What is the actual refresh frequency?
- Who monitors and fixes data flows?
- Are retries, failed-record logs, reconciliation, and audit trails available?

### Integration And Automation Landscape
- What integration tools are used?
- Is there an API gateway, enterprise service bus, iPaaS, broker, event platform, workflow platform, RPA, or low-code platform?
- Are integrations centrally managed or team-owned?
- Are integrations and API contracts documented?
- Are integration standards, monitoring, and support ownership defined?
- Are there fragile point-to-point integrations, file drops, scheduled jobs, hidden scripts, Excel macros, Access databases, Power Automate flows, Python scripts, or cron jobs?

### Software Delivery Model
- Where is source code stored? Is GitHub, GitLab, Bitbucket, Azure DevOps, or another system used?
- Are repositories centralised, team-owned, monorepo-based, or split into many repositories?
- What branching, code review, CI/CD, test, release, and deployment process is used?
- Who can deploy to production?
- Are deployments automated or manual?
- Are release windows, freeze periods, rollback procedures, deployment checklists, or emergency change processes defined?
- Are quality, security, architecture, dependency, container, or static analysis gates required?
- What is the slowest delivery step?

### Environments And Infrastructure
- What environments exist: development, test, staging, pre-production, production, sandbox, vendor sandbox, data science workspace, or analytics workspace?
- Are environments consistent and reliable?
- Are lower environments refreshed from production?
- Is production data copied, masked, or anonymised?
- Are containers, Kubernetes, virtual machines, serverless services, managed databases, or object stores used?
- Are private endpoints, VPNs, bastion hosts, or network restrictions important?
- Is infrastructure as code used?
- Is Terraform, Bicep, ARM, CloudFormation, Pulumi, Ansible, or another tool used?
- Who owns infrastructure provisioning?
- How long does it take to get an environment, database, network access, or cloud approval?

### Identity, Access, And Permissions
- What identity provider is used?
- Is Entra ID, Active Directory, Okta, or another provider used?
- Are SSO and MFA used?
- How are users, groups, roles, and permissions provisioned and deprovisioned?
- Where are access requests submitted and who approves them?
- How long does access approval usually take?
- Are privileged roles, just-in-time access, service accounts, managed identities, API clients, bots, or agents allowed?
- How are service accounts approved, reviewed, and audited?
- Are external consultants or vendors allowed access?
- Are there restrictions by geography, role, or data classification?

### Security, Privacy, And Compliance
- What security, privacy, or regulatory requirements are relevant?
- Is GDPR, financial regulation, health regulation, industry regulation, data residency, or cross-border transfer relevant?
- Is customer consent, employee monitoring, auditability, retention, deletion, or legal hold relevant?
- Are encryption, secrets management, vulnerability scanning, penetration testing, threat modelling, or security architecture reviews required?
- Are privacy impact assessments, vendor risk assessments, open-source reviews, AI governance reviews, or model risk reviews required?
- Are there rules about production data in development?
- Are there rules about company data in external AI tools?
- Are there approved or banned AI tools?

#### Compliance Probes
- If the user says `GDPR-compliant`, ask which personal data is in scope.
- If the user says `we cannot use cloud`, ask whether that is policy, preference, contract, or misunderstanding.
- If the user says `AI is not allowed`, ask whether all AI is disallowed or only external AI tools.
- If the user says `security approves it`, ask what the process is called and how long it takes.

### Collaboration And Work Management
- What tool is used for project tracking?
- What tool is used for documentation?
- Where are architecture decisions, requirements, meeting notes, incidents, changes, approvals, risks, tests, support tickets, user guides, runbooks, API docs, and data dictionaries stored?
- Where should a newcomer search first?
- Which documentation is outdated?
- Which documentation is reliable?
- Which Slack, Teams, email, or meeting channels matter?
- Where are decisions recorded?
- Who can make architecture, data, security, and business process decisions?
- Are informal decisions common and how are disagreements resolved?

### Governance, Standards, And Approvals
- Are there approved technology standards?
- Are there preferred languages, frameworks, databases, cloud services, integration patterns, BI tools, or AI tools?
- Are any technologies forbidden or discouraged?
- Are procurement, licence, vendor, documentation, testing, or logging constraints relevant?
- Are architecture, security, data governance, AI governance, change advisory, production readiness, or operational readiness reviews required?
- Are exception processes available?
- How long do approvals usually take?
- Which approval is most likely to block this project?


### AI, ML, And Automation Readiness
- Are AI or ML systems already used?
- Are LLM tools, internal chatbots, RAG systems, predictive models, document processing tools, workflow agents, or coding assistants approved?
- Are Databricks, Azure ML, SageMaker, Vertex AI, Snowflake ML, MLflow, Kubeflow, feature stores, model registries, or model monitoring used?
- Is model governance defined?
- Are prompt logs, conversation logs, feedback loops, evaluation datasets, and labelled datasets allowed or available?
- Are external model APIs, self-hosted models, open-source models, GPU resources, and synthetic data allowed?
- Are cost limits, latency requirements, explainability, human-in-the-loop controls, and audit requirements defined?
- Are automated decisions restricted?

## Handling Unknowns
When the user does not know, use:
```text
That is useful to know. I will mark it as unknown rather than guess.
```
- Ask who might know.
- Ask where it might be documented.
- Ask whether the unknown could block the project.
- Ask whether it should become an issue.
- Do not pressure the user to invent an answer.

## Handling Contradictions
When answers conflict, use:
```text
I may be misunderstanding this. Earlier we said one thing, but now it sounds different. Are both true in different situations?
```
- Check whether one answer is official and the other is actual practice.
- Check whether one answer is global and the other is local.
- Check whether one answer is old and the other is new.
- Check whether one answer applies to production and the other to reporting.
- Record the contradiction as an assumption or issue if unresolved.

## tech-stack-context.md Template
To capture answers use the template at `skills/tech-stack-interview/assets/template.md`, save it to `knowledge/<project>/tech-stack-context.md`. Once created, update `knowledge/index.yaml` **idempotently** — add the entry only if it is not already there, and update it in place when it is. Do not append a duplicate row on a re-run:
```yaml
  - path: <project>/tech-stack-context.md
    tags: [tech stack]
    priority: medium
    always_load: false
```

## Completion Criteria
- `knowledge/<project>/tech-stack-context.md` exists.
- The document is useful to a newcomer.
- Main systems, data stores, and integration patterns are identified.
- Access model, delivery process, governance path, and security constraints are described.
- AI and automation readiness is described if relevant.
- Pain points, risks, and unknowns are visible.
- The user can review and correct the document.

## Final Reminder For The Agent
The value of this skill is not a perfect inventory.
The value is making enterprise context visible.
The agent should help the user discover what matters, what is uncertain, what is risky, and what a newcomer must understand before making technical decisions.
A useful imperfect context document is better than a polished document full of hidden assumptions.
