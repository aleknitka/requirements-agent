<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/requirements.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.requirements`
Requirement CRUD and search. 


---

<a href="../src/requirements_agent_tools/db/requirements.py#L31"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `insert_requirement`

```python
insert_requirement(
    conn: 'Connection',
    req_in: 'RequirementIn',
    created_by: 'str'
) → RequirementRow
```

Insert a new requirement, log the creation, and embed it. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`req_in`</b>:  Validated requirement input. 
 - <b>`created_by`</b>:  Identifier of the user/agent writing the row. 



**Returns:**
 
 - <b>`The freshly-loaded `</b>: class:`RequirementRow`. 


---

<a href="../src/requirements_agent_tools/db/requirements.py#L129"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `update_requirement`

```python
update_requirement(
    conn: 'Connection',
    req_id: 'str',
    changes: 'dict[str, Any]',
    changed_by: 'str',
    summary: 'str'
) → RequirementRow
```

Apply a partial update and append a change-log entry. 

Only fields listed in :data:`_UPDATABLE_FIELDS` are accepted. A full row snapshot is captured when the new ``status`` value is in :data:`CONSTANTS.SNAPSHOT_ON_STATUSES`. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`req_id`</b>:  Requirement identifier to update. 
 - <b>`changes`</b>:  Mapping of field name to new value. 
 - <b>`changed_by`</b>:  Author of the change. 
 - <b>`summary`</b>:  Human-readable change summary. 



**Returns:**
 
 - <b>`The reloaded `</b>: class:`RequirementRow`. 



**Raises:**
 
 - <b>`KeyError`</b>:  If ``req_id`` does not exist. 
 - <b>`ValueError`</b>:  If ``changes`` includes non-updatable fields. 


---

<a href="../src/requirements_agent_tools/db/requirements.py#L223"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_requirement`

```python
get_requirement(conn: 'Connection', req_id: 'str') → Optional[RequirementRow]
```

Return one requirement by id, or ``None`` if missing. 

The result includes a ``has_embedding`` flag joined from ``req_embeddings``. 


---

<a href="../src/requirements_agent_tools/db/requirements.py#L242"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `search_requirements`

```python
search_requirements(
    conn: 'Connection',
    status: 'Optional[str]' = None,
    priority: 'Optional[str]' = None,
    req_type: 'Optional[str]' = None,
    owner: 'Optional[str]' = None,
    tag: 'Optional[str]' = None,
    keyword: 'Optional[str]' = None,
    since: 'Optional[datetime]' = None,
    until: 'Optional[datetime]' = None,
    updated_since: 'Optional[datetime]' = None,
    updated_until: 'Optional[datetime]' = None,
    sort_by: 'str' = 'created_at',
    desc: 'bool' = True,
    **extra_filters: 'Any'
) → list[RequirementRow]
```

Field-based search with comprehensive filters and sorting. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`status`</b>:  Filter by status enum value. 
 - <b>`priority`</b>:  Filter by priority enum value. 
 - <b>`req_type`</b>:  Filter by requirement-type code (case-insensitive). 
 - <b>`owner`</b>:  Filter by exact owner name. 
 - <b>`tag`</b>:  Filter rows whose JSON ``tags`` array contains this value. 
 - <b>`keyword`</b>:  ``LIKE %keyword%`` match against title or description. 
 - <b>`since`</b>:  Created at or after this date. 
 - <b>`until`</b>:  Created at or before this date. 
 - <b>`updated_since`</b>:  Updated at or after this date. 
 - <b>`updated_until`</b>:  Updated at or before this date. 
 - <b>`sort_by`</b>:  Column to sort by (created_at, updated_at, status, priority, req_type). 
 - <b>`desc`</b>:  Sort descending if True. 
 - <b>`**extra_filters`</b>:  Key-value pairs for exact matches on other columns. 



**Returns:**
 
 - <b>`A list of `</b>: class:`RequirementRow` matching the criteria. 


---

<a href="../src/requirements_agent_tools/db/requirements.py#L342"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `fts_search_requirements`

```python
fts_search_requirements(conn: 'Connection', query: 'str') → list[RequirementRow]
```

Search requirements using FTS5 across records and updates. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`query`</b>:  FTS5 query string. 



**Returns:**
 List of matching RequirementRow instances. 


---

<a href="../src/requirements_agent_tools/db/requirements.py#L372"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_requirement_by_title`

```python
get_requirement_by_title(
    conn: 'Connection',
    title: 'str'
) → Optional[RequirementRow]
```

Return the requirement whose ``title`` matches exactly, or ``None``. 


---

<a href="../src/requirements_agent_tools/db/requirements.py#L389"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `find_requirements_updated_between`

```python
find_requirements_updated_between(
    conn: 'Connection',
    start: 'datetime',
    end: 'datetime'
) → list[RequirementRow]
```

Return requirements whose ``updated_at`` falls within ``[start, end]``. 

Both bounds are inclusive. ISO-8601 string comparison on the stored timestamp column is correct because all timestamps are written via ``ser.now_iso`` in UTC. 


---

<a href="../src/requirements_agent_tools/db/requirements.py#L414"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `build_requirements_report`

```python
build_requirements_report(conn: 'Connection') → list[dict]
```

Return every requirement together with its full update history. 

Each entry has the shape ``{"requirement": RequirementRow, "updates": list[UpdateRecord]}``. Results are ordered by the requirement's ``created_at``. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
