<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/CONSTANTS.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.CONSTANTS`
CONSTANTS.py — single source of truth for all configuration. 

PROJECTS_DIR defaults to a path relative to this file's location (requirements-agent/projects/), so scripts work correctly regardless of the working directory they are launched from. 

To migrate to S3 later: replace PROJECTS_DIR with an S3-backed path abstraction — no skill code needs to change. 

**Global Variables**
---------------
- **EMBEDDING_API_BASE**
- **EMBEDDING_API_KEY**
- **EMBEDDING_MODEL**
- **EMBEDDING_DIM**
- **SNAPSHOT_ON_STATUSES**
- **MD_NOTES_BEGIN**
- **MD_NOTES_END**

---

<a href="../src/requirements_agent_tools/CONSTANTS.py#L54"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `project_dir`

```python
project_dir(slug: str) → Path
```

Return (and create) the directory for a given project slug. 


---

<a href="../src/requirements_agent_tools/CONSTANTS.py#L61"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `db_path`

```python
db_path(slug: str) → Path
```

Return the SQLite database file path for a given project slug. 



**Args:**
 
 - <b>`slug`</b>:  Project slug (directory name under PROJECTS_DIR). 



**Returns:**
 Path to the .db file at PROJECTS_DIR/<slug>/<slug>.db. 


---

<a href="../src/requirements_agent_tools/CONSTANTS.py#L73"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `md_path`

```python
md_path(slug: str) → Path
```

Return the PROJECT.md path for a given project slug. 



**Args:**
 
 - <b>`slug`</b>:  Project slug (directory name under PROJECTS_DIR). 



**Returns:**
 Path to PROJECT.md at PROJECTS_DIR/<slug>/PROJECT.md. 


---

<a href="../src/requirements_agent_tools/CONSTANTS.py#L85"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `slugify`

```python
slugify(name: str) → str
```

Convert a human-readable name into a URL-safe slug. 

Replaces any sequence of non-alphanumeric characters with a single hyphen and strips leading/trailing hyphens. 



**Args:**
 
 - <b>`name`</b>:  Human-readable name to slugify. 



**Returns:**
 Lowercase hyphen-separated slug string. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
