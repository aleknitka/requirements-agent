<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/updates.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.updates`
Append-only change log for any auditable entity in the project DB. 

Two entity kinds share this table: 
  - ``requirement`` — entity_id is the requirement id (e.g. ``REQ-FUN-...``) 
  - ``project_md`` — entity_id is the singleton project_id; one row per  PROJECT.md write or section append. 


---

<a href="../src/requirements_agent_tools/db/updates.py#L21"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `write_update`

```python
write_update(conn: 'Connection', record: 'UpdateRecord') → None
```

Persist one :class:`UpdateRecord` to the ``updates`` table. 

The caller owns the transaction (no implicit ``commit()``). 


---

<a href="../src/requirements_agent_tools/db/updates.py#L55"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../src/requirements_agent_tools/db/updates.py#L73"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_project_md_history`

```python
get_project_md_history(
    conn: 'Connection',
    project_id: 'str'
) → list[UpdateRecord]
```

Return the full PROJECT.md change history for a project, oldest first. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
