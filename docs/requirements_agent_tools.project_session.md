<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/project_session.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.project_session`
project_session.py — single-project connection helper. 

Every skill calls ``get_project_conn()`` at the start of its session. The single project database is at ``CONSTANTS.DB_PATH``. 

PROJECT.md is owned by the skill: write through ``project_md_cli`` (or call ``project_md.save`` / ``append_section`` directly). 


---

<a href="../src/requirements_agent_tools/project_session.py#L20"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_project_conn`

```python
get_project_conn() → Connection
```

Open the single project database. Exits with error if not initialised. 

Checks that ``DB_PATH`` exists before opening. If the project has not been set up yet (``uv run init-project setup`` not run), exits non-zero with a clear error message rather than creating an empty database. 



**Returns:**
  An open ``sqlite3.Connection`` to the project database.  Caller owns the lifetime and must close it. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
