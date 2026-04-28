<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/projects.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.projects`
Project CRUD. Each DB file holds exactly one project row. 


---

<a href="../src/requirements_agent_tools/db/projects.py#L16"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `upsert_project`

```python
upsert_project(conn: 'Connection', meta: 'ProjectMeta') → ProjectMeta
```

Insert or update the single project row in this database. 

Auto-derives ``meta.slug`` from ``meta.name`` when empty, and bumps ``updated_at`` to *now*. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`meta`</b>:  Project metadata. Mutated in place to reflect derived slug  and updated timestamp. 



**Returns:**
 The same ``meta`` instance with derived fields filled in. 



**Raises:**
 
 - <b>`sqlite3.IntegrityError`</b>:  If a different project already exists in  this DB (the ``singleton`` UNIQUE constraint blocks the insert). 


---

<a href="../src/requirements_agent_tools/db/projects.py#L100"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../src/requirements_agent_tools/db/projects.py#L113"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_project_by_slug`

```python
get_project_by_slug(conn: 'Connection', slug: 'str') → Optional[ProjectMeta]
```

Return the project with the matching slug in this database, or ``None``. 


---

<a href="../src/requirements_agent_tools/db/projects.py#L123"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `list_projects`

```python
list_projects(conn: 'Connection') → list[ProjectMeta]
```

Return every project row in this database, ordered by ``created_at``. 


---

<a href="../src/requirements_agent_tools/db/projects.py#L129"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `discover_projects`

```python
discover_projects() → list[dict]
```

Discover every project on disk by scanning ``PROJECTS_DIR``. 

Each project lives at ``PROJECTS_DIR/<slug>/<slug>.db``. Directories without a matching DB file (or whose DB has no project row) are skipped. 



**Returns:**
  A list of dicts with ``slug``, ``name``, ``code``, and ``phase``  for every discoverable project, sorted by slug. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
