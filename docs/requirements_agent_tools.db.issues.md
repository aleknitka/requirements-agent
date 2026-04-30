<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/issues.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.issues`
Issue CRUD and linking. 

Issues can be linked to multiple requirements and multiple update records to track regressions, bugs, or concerns arising from specific changes. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L26"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `insert_issue`

```python
insert_issue(
    conn: 'Connection',
    issue_in: 'IssueIn',
    created_by: 'str'
) → IssueRow
```

Insert a new issue and link it to requirements/updates. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`issue_in`</b>:  Validated issue data. 
 - <b>`created_by`</b>:  Identifier of the person/agent creating the issue. 



**Returns:**
 The full IssueRow including generated ID and timestamps. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L86"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_issue`

```python
get_issue(conn: 'Connection', issue_id: 'str') → Optional[IssueRow]
```

Return one issue by id, or ``None`` if missing. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L123"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `search_issues`

```python
search_issues(
    conn: 'Connection',
    status: 'Optional[str]' = None,
    priority: 'Optional[str]' = None,
    owner: 'Optional[str]' = None,
    requirement_id: 'Optional[str]' = None
) → list[IssueRow]
```

Search issues with optional filters. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L154"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `update_issue`

```python
update_issue(
    conn: 'Connection',
    issue_id: 'str',
    changes: 'dict',
    changed_by: 'str'
) → IssueRow
```

Apply partial updates to an issue. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L206"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `log_issue_action`

```python
log_issue_action(
    conn: 'Connection',
    action_in: 'IssueActionIn'
) → IssueActionRow
```

Record an action taken for an issue. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`action_in`</b>:  Action details. 



**Returns:**
 The full IssueActionRow. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L240"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_issue_action`

```python
get_issue_action(
    conn: 'Connection',
    action_id: 'str'
) → Optional[IssueActionRow]
```

Return one issue action by id. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L258"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `list_issue_actions`

```python
list_issue_actions(conn: 'Connection', issue_id: 'str') → list[IssueActionRow]
```

Return all actions for a given issue, newest first. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
