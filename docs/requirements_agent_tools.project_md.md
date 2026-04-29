<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/project_md.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.project_md`
Skill-owned PROJECT.md persistence with audit trail. 

The skill drafts the markdown content and calls ``save()`` (full replace, also the create path) or ``append_section()``. Every write records a row in the ``updates`` table with ``entity_type='project_md'`` and emits a loguru log entry, so the change history is queryable both from the DB and the per-project log file. 


---

<a href="../src/requirements_agent_tools/project_md.py#L24"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `save`

```python
save(
    conn: 'Connection',
    slug: 'str',
    content: 'str',
    changed_by: 'str',
    summary: 'str'
) → Path
```

Write ``content`` as the full PROJECT.md body. 

Creates the file if it does not exist; otherwise overwrites it. In both cases an audit row is inserted in the same transaction as the file write. 



**Args:**
 
 - <b>`conn`</b>:  Open connection to the project's DB. 
 - <b>`slug`</b>:  Project slug (selects the target file path). 
 - <b>`content`</b>:  The full markdown body to persist. 
 - <b>`changed_by`</b>:  User or agent identifier for the audit row. 
 - <b>`summary`</b>:  Human-readable description of the change. 



**Returns:**
 The path that was written. 



**Raises:**
 
 - <b>`LookupError`</b>:  If the project row is missing from the DB (the audit  row's ``entity_id`` references the singleton project_id, which  must exist). 


---

<a href="../src/requirements_agent_tools/project_md.py#L90"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `append_section`

```python
append_section(
    conn: 'Connection',
    slug: 'str',
    section: 'str',
    changed_by: 'str',
    summary: 'str'
) → Path
```

Append ``section`` to the existing PROJECT.md, audit-logged. 

A blank line is inserted between the existing body and the new section. 



**Args:**
 
 - <b>`conn`</b>:  Open connection to the project's DB. 
 - <b>`slug`</b>:  Project slug. 
 - <b>`section`</b>:  Markdown text to append (no leading/trailing blank required). 
 - <b>`changed_by`</b>:  Audit author. 
 - <b>`summary`</b>:  Audit summary. 



**Raises:**
 
 - <b>`FileNotFoundError`</b>:  If PROJECT.md does not exist yet — call ``save``  first. 
 - <b>`LookupError`</b>:  If the project row is missing from the DB. 


---

<a href="../src/requirements_agent_tools/project_md.py#L153"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `read`

```python
read(slug: 'str') → Optional[str]
```

Return the current PROJECT.md content, or ``None`` if it does not exist. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
