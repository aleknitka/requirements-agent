# Tech Stack Context

## 1. Document Control

| Field | Value |
|---|---|
| Project | <!-- project name or `project` if unknown --> |
| Organisation / Unit | <!-- optional safe summary --> |
| Prepared By | AI agent |
| Prepared On | <!-- YYYY-MM-DD --> |
| Confidence | Low / Medium / High |
| Status | Draft / Reviewed / Approved |

## 2. Executive Summary

<!-- 5-10 bullets describing the practical technology context a newcomer must understand. -->

- 

## 3. Current Stack At A Glance

| Area | Current Tools / Platforms | Notes | Confidence |
|---|---|---|---|
| Cloud / Hosting |  |  |  |
| Core Business Apps |  |  |  |
| Data Platforms |  |  |  |
| BI / Reporting |  |  |  |
| Integration / Automation |  |  |  |
| Source Control |  |  |  |
| CI/CD |  |  |  |
| Work Management |  |  |  |
| Documentation |  |  |  |
| Identity / Access |  |  |  |
| Security / Compliance |  |  |  |
| AI / ML / Automation |  |  |  |

## 4. Enterprise Stack Overview

### 4.1 Operating Model

- Stack type: <!-- cloud-based / SaaS-heavy / on-premise / private cloud / hybrid / unknown -->
- Strategic platforms:
  - 
- Tolerated platforms:
  - 
- Platforms being introduced:
  - 
- Platforms being retired:
  - 
- Forbidden or discouraged platforms:
  - 

### 4.2 Architecture Documentation

- Architecture diagram available: Yes / No / Unknown
- Technology catalogue available: Yes / No / Unknown
- Documentation location:
- Owner / maintainer:
- Reliability of documentation: Low / Medium / High / Unknown

## 5. Core Business Applications

| Business Area | System / Application | Scope | Source Of Truth? | Data Sensitivity | Notes |
|---|---|---|---|---|---|
| ERP |  |  |  |  |  |
| CRM |  |  |  |  |  |
| HR |  |  |  |  |  |
| Finance |  |  |  |  |  |
| Procurement |  |  |  |  |  |
| ITSM / Support |  |  |  |  |  |
| Documents / Contracts |  |  |  |  |  |
| Product / Master Data |  |  |  |  |  |
| Industry-Specific Systems |  |  |  |  |  |
| Other |  |  |  |  |  |

### 5.1 Critical, Legacy, Or Risky Systems

- Business-critical systems:
  - 
- Legacy but essential systems:
  - 
- Disliked but unavoidable systems:
  - 
- Systems being replaced:
  - 
- Systems newcomers should not update directly:
  - 

## 6. Data And Analytics Landscape

### 6.1 Main Data Stores

| Data Store / Platform | Type | Main Data Held | Owner | Refresh / Latency | Notes |
|---|---|---|---|---|---|
|  | Database / Warehouse / Lake / Lakehouse / Files / Other |  |  |  |  |

### 6.2 Reporting And BI

- BI tools:
  - 
- Main dashboards / reports:
  - 
- KPI definitions location:
- Data dictionary / catalogue / lineage location:
- Owner of data quality:
- Owner of KPI conflicts:

## 7. Data Movement And Integrations

### 7.1 Data Movement Patterns

| Flow | Source | Target | Method | Frequency | Monitoring | Owner | Notes |
|---|---|---|---|---|---|---|---|
|  |  |  | API / ETL / ELT / File / Email / Manual / Streaming / Other |  |  |  |  |

### 7.2 Integration And Automation Tools

- API gateway:
- Enterprise service bus / iPaaS:
- Event / message platform:
- Workflow / RPA / low-code tools:
- Scheduled jobs / scripts:
- Integration documentation location:
- Support ownership model:

### 7.3 Fragile Or Hidden Automation

- Known file drops:
  - 
- Excel macros / Access databases:
  - 
- Power Automate or low-code flows:
  - 
- Python scripts / cron jobs / local scripts:
  - 
- Manual copy-paste or email-based processes:
  - 

## 8. Software Delivery Model

| Area | Current Practice | Notes | Confidence |
|---|---|---|---|
| Source control |  |  |  |
| Repository model |  |  |  |
| Branching |  |  |  |
| Code review |  |  |  |
| CI/CD |  |  |  |
| Testing |  |  |  |
| Release process |  |  |  |
| Deployment ownership |  |  |  |
| Rollback process |  |  |  |
| Quality / security gates |  |  |  |

- Slowest delivery step:
- Release windows or freeze periods:
- Emergency change process:

## 9. Environments And Infrastructure

### 9.1 Environments

| Environment | Exists? | Purpose | Data Used | Access Notes | Reliability |
|---|---|---|---|---|---|
| Development | Yes / No / Unknown |  |  |  |  |
| Test | Yes / No / Unknown |  |  |  |  |
| Staging / Pre-production | Yes / No / Unknown |  |  |  |  |
| Production | Yes / No / Unknown |  |  |  |  |
| Sandbox | Yes / No / Unknown |  |  |  |  |
| Data Science / Analytics Workspace | Yes / No / Unknown |  |  |  |  |

### 9.2 Infrastructure

- Hosting model:
- Cloud provider(s):
- On-premise / data centre dependencies:
- Containers / Kubernetes:
- Virtual machines:
- Serverless:
- Managed databases:
- Object storage:
- Network restrictions:
- VPN / private endpoints / bastion hosts:
- Infrastructure as code tool:
- Infrastructure provisioning owner:
- Typical lead time for new infrastructure:

### 9.3 Production Data In Lower Environments

- Production data copied to lower environments: Yes / No / Unknown
- Masking or anonymisation used: Yes / No / Unknown
- Relevant rules:
- Risks:

## 10. Identity, Access, And Permissions

| Area | Current Practice | Notes |
|---|---|---|
| Identity provider |  |  |
| SSO | Yes / No / Unknown |  |
| MFA | Yes / No / Unknown |  |
| Groups / roles |  |  |
| Access request process |  |  |
| Approval owner |  |  |
| Typical approval time |  |  |
| Deprovisioning |  |  |
| Privileged access |  |  |
| Service accounts / managed identities |  |  |
| External vendor access |  |  |
| Geographic or data classification restrictions |  |  |

## 11. Security, Privacy, And Compliance

### 11.1 Applicable Requirements

- GDPR: Yes / No / Unknown
- Financial regulation: Yes / No / Unknown
- Health regulation: Yes / No / Unknown
- Industry regulation:
- Data residency:
- Cross-border transfer:
- Retention / deletion / legal hold:
- Customer consent:
- Employee monitoring:
- Auditability:

### 11.2 Required Reviews And Controls

| Control / Review | Required? | Owner | Typical Lead Time | Notes |
|---|---|---|---|---|
| Security architecture review | Yes / No / Unknown |  |  |  |
| Privacy impact assessment | Yes / No / Unknown |  |  |  |
| Vendor risk assessment | Yes / No / Unknown |  |  |  |
| Open-source review | Yes / No / Unknown |  |  |  |
| AI governance review | Yes / No / Unknown |  |  |  |
| Model risk review | Yes / No / Unknown |  |  |  |
| Penetration testing | Yes / No / Unknown |  |  |  |
| Vulnerability scanning | Yes / No / Unknown |  |  |  |
| Threat modelling | Yes / No / Unknown |  |  |  |

### 11.3 AI And External Tool Rules

- Company data allowed in external AI tools: Yes / No / Unknown
- Approved AI tools:
  - 
- Banned AI tools:
  - 
- Sensitive data restrictions:
- Logging restrictions:

## 12. Collaboration And Work Management

| Need | Tool / Location | Owner | Reliability | Notes |
|---|---|---|---|---|
| Project tracking |  |  |  |  |
| Documentation |  |  |  |  |
| Architecture decisions |  |  |  |  |
| Requirements |  |  |  |  |
| Meeting notes |  |  |  |  |
| Incidents |  |  |  |  |
| Changes / approvals |  |  |  |  |
| Risks |  |  |  |  |
| Tests |  |  |  |  |
| Support tickets |  |  |  |  |
| Runbooks |  |  |  |  |
| API docs |  |  |  |  |
| Data dictionaries |  |  |  |  |

- Where newcomers should search first:
- Reliable documentation:
- Outdated documentation:
- Important communication channels:
- Where decisions are recorded:
- How disagreements are resolved:

## 13. Governance, Standards, And Approvals

### 13.1 Technology Standards

- Preferred languages:
- Preferred frameworks:
- Preferred databases:
- Preferred cloud services:
- Preferred integration patterns:
- Preferred BI tools:
- Preferred AI tools:
- Forbidden or discouraged technologies:
- Exception process:

### 13.2 Approval Path

| Approval / Review | Required? | Owner | Typical Lead Time | Blocker Risk | Notes |
|---|---|---|---|---|---|
| Architecture | Yes / No / Unknown |  |  | Low / Medium / High |  |
| Security | Yes / No / Unknown |  |  | Low / Medium / High |  |
| Data governance | Yes / No / Unknown |  |  | Low / Medium / High |  |
| AI governance | Yes / No / Unknown |  |  | Low / Medium / High |  |
| Change advisory | Yes / No / Unknown |  |  | Low / Medium / High |  |
| Procurement | Yes / No / Unknown |  |  | Low / Medium / High |  |
| Licence / vendor | Yes / No / Unknown |  |  | Low / Medium / High |  |
| Production readiness | Yes / No / Unknown |  |  | Low / Medium / High |  |
| Operational readiness | Yes / No / Unknown |  |  | Low / Medium / High |  |

- Approval most likely to block this project:

## 14. AI, ML, And Automation Readiness

| Area | Current State | Notes | Confidence |
|---|---|---|---|
| Existing AI / ML systems |  |  |  |
| LLM tools |  |  |  |
| Internal chatbots / RAG |  |  |  |
| Predictive models |  |  |  |
| Document processing |  |  |  |
| Workflow agents |  |  |  |
| Coding assistants |  |  |  |
| ML platform |  |  |  |
| Model registry |  |  |  |
| Model monitoring |  |  |  |
| Evaluation datasets |  |  |  |
| Labelled data |  |  |  |
| Feedback loops |  |  |  |
| GPU resources |  |  |  |
| External model APIs |  |  |  |
| Self-hosted models |  |  |  |
| Open-source models |  |  |  |
| Synthetic data |  |  |  |

- Model governance:
- Prompt or conversation logging rules:
- Cost limits:
- Latency requirements:
- Explainability requirements:
- Human-in-the-loop requirements:
- Audit requirements:
- Restrictions on automated decisions:

## 15. Unknowns

| Unknown | Why It Matters | Who Might Know | Where To Check | Could Block Project? | Issue Needed? |
|---|---|---|---|---|---|
|  |  |  |  | Yes / No / Unknown | Yes / No |
