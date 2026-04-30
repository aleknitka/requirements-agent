<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/models.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.models`
models.py — Pydantic validation models. Nothing here touches the database. Every write goes through these first. 

**Global Variables**
---------------
- **REQUIREMENT_TYPE_METADATA**


---

<a href="../src/requirements_agent_tools/models.py#L21"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `RequirementStatus`
Lifecycle states for a requirement. 





---

<a href="../src/requirements_agent_tools/models.py#L31"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `RequirementPriority`
Priority tiers for triaging and scheduling requirements. 





---

<a href="../src/requirements_agent_tools/models.py#L40"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `RequirementType`
Three-letter codes for requirement types. Value == code string. 





---

<a href="../src/requirements_agent_tools/models.py#L79"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `RequirementTypeMeta`
Metadata tuple binding a type code to its display name and description. 



**Attributes:**
 
 - <b>`code`</b>:  Three-letter type code matching RequirementType enum values. 
 - <b>`name`</b>:  Human-readable type name. 
 - <b>`description`</b>:  One-sentence description of what this type covers. 





---

<a href="../src/requirements_agent_tools/models.py#L267"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `ProjectPhase`
Lifecycle phases for a project. 





---

<a href="../src/requirements_agent_tools/models.py#L279"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `IssueStatus`
Lifecycle states for an issue. 





---

<a href="../src/requirements_agent_tools/models.py#L289"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `IssuePriority`
Priority tiers for an issue. 





---

<a href="../src/requirements_agent_tools/models.py#L303"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `ExternalLink`
A reference to an external system or resource. 



**Attributes:**
 
 - <b>`system`</b>:  Name of the external system (e.g. "Jira", "Confluence"). 
 - <b>`label`</b>:  Display label for the link. 
 - <b>`url`</b>:  Optional URL to the specific item. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L317"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Dependency`
A directed dependency between requirements or external systems. 



**Attributes:**
 
 - <b>`kind`</b>:  Whether the dependency is internal (another requirement)  or external (outside system). 
 - <b>`ref`</b>:  Identifier of the dependency target. 
 - <b>`url`</b>:  Optional URL to the dependency. 
 - <b>`note`</b>:  Optional explanatory note. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L334"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Stakeholder`
A person with a defined role on the project. 



**Attributes:**
 
 - <b>`name`</b>:  Full name or identifier of the stakeholder. 
 - <b>`role`</b>:  Stakeholder role (requestor/sponsor/approver/reviewer/informed). 
 - <b>`contact`</b>:  Optional email or messaging handle. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L353"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `RequirementIn`
Validated input for creating a requirement. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L369"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `RequirementRow`
Full DB row — adds id and timestamps. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L383"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `FieldDiff`
A before/after change record for a single field. 



**Attributes:**
 
 - <b>`field`</b>:  Name of the changed field. 
 - <b>`old_value`</b>:  Value before the change. 
 - <b>`new_value`</b>:  Value after the change. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L397"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `UpdateRecord`
Audit record capturing a change to a database entity. 



**Attributes:**
 
 - <b>`id`</b>:  UUID for this update record. 
 - <b>`entity_type`</b>:  Kind of entity changed ('requirement', 'project', 'issue'). 
 - <b>`entity_id`</b>:  Identifier of the changed entity. 
 - <b>`changed_at`</b>:  Timestamp of the change (UTC). 
 - <b>`changed_by`</b>:  Identifier of the person who made the change. 
 - <b>`summary`</b>:  One-line description of what changed and why. 
 - <b>`diffs`</b>:  List of per-field before/after diffs. 
 - <b>`full_snapshot`</b>:  Optional full row snapshot for status transitions. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L426"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `IssueIn`
Validated input for creating an issue. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L438"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `IssueRow`
Full DB row — adds id and timestamps. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L451"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `IssueActionIn`
Validated input for logging an action against an issue. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L458"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `IssueActionRow`
Full DB row for an issue action. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 




---

<a href="../src/requirements_agent_tools/models.py#L470"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `ProjectMeta`
Full project metadata record. 



**Attributes:**
 
 - <b>`project_id`</b>:  UUID for the project. 
 - <b>`name`</b>:  Human-readable project name. 
 - <b>`code`</b>:  Optional short project code (e.g. "PROJ-24"). 
 - <b>`phase`</b>:  Current project lifecycle phase. 
 - <b>`objective`</b>:  One-sentence project objective. 
 - <b>`business_case`</b>:  Business justification narrative. 
 - <b>`success_criteria`</b>:  List of measurable success criteria statements. 
 - <b>`out_of_scope`</b>:  List of explicitly out-of-scope items. 
 - <b>`project_owner`</b>:  Name or identifier of the project owner. 
 - <b>`sponsor`</b>:  Name or identifier of the executive sponsor. 
 - <b>`stakeholders`</b>:  List of project stakeholders with roles. 
 - <b>`start_date`</b>:  Planned or actual project start date. 
 - <b>`target_date`</b>:  Target completion date. 
 - <b>`actual_end_date`</b>:  Actual completion date, if closed. 
 - <b>`external_links`</b>:  Links to external systems (e.g. Jira, Confluence). 
 - <b>`status_summary`</b>:  Current status narrative for the project. 
 - <b>`status_updated_at`</b>:  When the status summary was last updated. 
 - <b>`created_at`</b>:  When the project record was created (UTC). 
 - <b>`updated_at`</b>:  When the project record was last modified (UTC). 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 






---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
