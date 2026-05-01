<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/updates.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.updates`
Append-only change log for any auditable entity in the project DB. 

Three entity kinds share this table: 
  - ``requirement`` — entity_id is the requirement id (e.g. ``REQ-FUN-...``) 
  - ``project``     — entity_id is the singleton project_id 
  - ``issue``       — entity_id is the issue id 


---

<a href="../src/requirements_agent_tools/db/updates.py#L22"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `write_update`

```python
write_update(conn: 'Connection', record: 'UpdateRecord') → None
```

Persist one :class:`UpdateRecord` to the ``updates`` table. 

The caller owns the transaction (no implicit ``commit()``). 


---

<a href="../src/requirements_agent_tools/db/updates.py#L56"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_updates`

```python
get_updates(
    conn: 'Connection',
    entity_id: 'str',
    entity_type: 'str' = 'requirement'
) → list[UpdateRecord]
```

Return all change records for one entity, oldest first. 


---

<a href="../src/requirements_agent_tools/db/updates.py#L74"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `search_updates`

```python
search_updates(
    conn: 'Connection',
    entity_type: 'Optional[str]' = None,
    entity_id: 'Optional[str]' = None,
    changed_by: 'Optional[str]' = None,
    since: 'Optional[datetime]' = None,
    until: 'Optional[datetime]' = None,
    sort_by: 'str' = 'changed_at',
    desc: 'bool' = True
) → list[UpdateRecord]
```

Search the audit log with comprehensive filters. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`entity_type`</b>:  Filter by kind (requirement, project, issue). 
 - <b>`entity_id`</b>:  Filter by specific entity identifier. 
 - <b>`changed_by`</b>:  Filter by author. 
 - <b>`since`</b>:  Changed at/after (datetime). 
 - <b>`until`</b>:  Changed before/at (datetime). 
 - <b>`sort_by`</b>:  Column to sort by (changed_at, changed_by). 
 - <b>`desc`</b>:  Sort descending if True. 



**Returns:**
 List of matching UpdateRecord instances. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
