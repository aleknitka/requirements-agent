<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/issues.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.issues`
Issue CRUD and linking. 

Issues can be linked to multiple requirements and multiple update records to track regressions, bugs, or concerns arising from specific changes. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L28"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../src/requirements_agent_tools/db/issues.py#L100"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_issue`

```python
get_issue(conn: 'Connection', issue_id: 'str') → Optional[IssueRow]
```

Return one issue by id, or ``None`` if missing. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L137"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_issue_full`

```python
get_issue_full(conn: 'Connection', issue_id: 'str') → Optional[dict]
```

Return one issue with all its linked data, including updates. 

Returns a dict with IssueRow model dump plus 'updates' list. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L167"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `search_issues`

```python
search_issues(
    conn: 'Connection',
    status: 'Optional[str]' = None,
    priority: 'Optional[str]' = None,
    owner: 'Optional[str]' = None,
    requirement_id: 'Optional[str]' = None,
    since: 'Optional[datetime]' = None,
    until: 'Optional[datetime]' = None,
    updated_since: 'Optional[datetime]' = None,
    updated_until: 'Optional[datetime]' = None,
    sort_by: 'str' = 'created_at',
    desc: 'bool' = True,
    **extra_filters: 'Any'
) → list[IssueRow]
```

Search issues with comprehensive filters and sorting. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`status`</b>:  Filter by status value. 
 - <b>`priority`</b>:  Filter by priority value. 
 - <b>`owner`</b>:  Filter by owner identifier. 
 - <b>`requirement_id`</b>:  Filter by linked requirement. 
 - <b>`since`</b>:  Created at or after this date. 
 - <b>`until`</b>:  Created at or before this date. 
 - <b>`updated_since`</b>:  Updated at or after this date. 
 - <b>`updated_until`</b>:  Updated at or before this date. 
 - <b>`sort_by`</b>:  Column to sort by (created_at, updated_at, status, priority). 
 - <b>`desc`</b>:  Sort descending if True. 
 - <b>`**extra_filters`</b>:  Key-value pairs for exact matches on other columns. 



**Returns:**
 List of matching IssueRow instances. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L255"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../src/requirements_agent_tools/db/issues.py#L307"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../src/requirements_agent_tools/db/issues.py#L341"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_issue_action`

```python
get_issue_action(
    conn: 'Connection',
    action_id: 'str'
) → Optional[IssueActionRow]
```

Return one issue action by id. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L359"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `list_issue_actions`

```python
list_issue_actions(conn: 'Connection', issue_id: 'str') → list[IssueActionRow]
```

Return all actions for a given issue, newest first. 


---

<a href="../src/requirements_agent_tools/db/issues.py#L364"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `search_issue_actions`

```python
search_issue_actions(
    conn: 'Connection',
    issue_id: 'Optional[str]' = None,
    since: 'Optional[datetime]' = None,
    until: 'Optional[datetime]' = None,
    keyword: 'Optional[str]' = None,
    sort_by: 'str' = 'occurred_at',
    desc: 'bool' = True
) → list[IssueActionRow]
```

Search issue actions with comprehensive filters. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`issue_id`</b>:  Filter by parent issue. 
 - <b>`since`</b>:  Occurred at/after (datetime). 
 - <b>`until`</b>:  Occurred before/at (datetime). 
 - <b>`keyword`</b>:  Substring match on description. 
 - <b>`sort_by`</b>:  Column to sort by (occurred_at). 
 - <b>`desc`</b>:  Sort descending if True. 



**Returns:**
 List of matching IssueActionRow instances. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
