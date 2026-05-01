<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/projects.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.projects`
Project CRUD. Each DB file holds exactly one project row. 


---

<a href="../src/requirements_agent_tools/db/projects.py#L15"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `upsert_project`

```python
upsert_project(conn: 'Connection', meta: 'ProjectMeta') → ProjectMeta
```

Insert or update the single project row in this database. 

Bumps ``updated_at`` to now on every call. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`meta`</b>:  Project metadata. Mutated in place to reflect updated timestamp. 



**Returns:**
 The same ``meta`` instance with ``updated_at`` refreshed. 



**Raises:**
 
 - <b>`sqlite3.IntegrityError`</b>:  If a different project already exists in  this DB (the ``singleton`` UNIQUE constraint blocks the insert). 


---

<a href="../src/requirements_agent_tools/db/projects.py#L92"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_project`

```python
get_project(conn: 'Connection') → Optional[ProjectMeta]
```

Return the single project stored in this database, or ``None``. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 



**Returns:**
 The project metadata, or ``None`` if no project has been inserted. 


---

<a href="../src/requirements_agent_tools/db/projects.py#L105"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `list_projects`

```python
list_projects(conn: 'Connection') → list[ProjectMeta]
```

Return every project row in this database, ordered by ``created_at``. 


---

<a href="../src/requirements_agent_tools/db/projects.py#L110"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `search_projects`

```python
search_projects(
    conn: 'Connection',
    name: 'Optional[str]' = None,
    code: 'Optional[str]' = None,
    phase: 'Optional[str]' = None,
    owner: 'Optional[str]' = None
) → list[ProjectMeta]
```

Search for projects matching the given criteria. 

Since our architecture is single-project-per-DB, this will return either zero or one row for a given set of filters. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`name`</b>:  Substring match on project name. 
 - <b>`code`</b>:  Exact match on project code. 
 - <b>`phase`</b>:  Exact match on project phase. 
 - <b>`owner`</b>:  Exact match on project owner. 



**Returns:**
 List of matching ProjectMeta instances. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
