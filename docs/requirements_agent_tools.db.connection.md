<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/connection.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.connection`
Connection lifecycle: open/close DB files and apply schema migrations. 


---

<a href="../src/requirements_agent_tools/db/connection.py#L14"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_db`

```python
get_db(path: 'str', sqlite_vec_enabled: 'bool' = False) → Connection
```

Open (or create) a SQLite database and optionally load sqlite-vec. 

The connection is configured with WAL journaling, FK enforcement, and Row factory before bootstrap runs. 



**Args:**
 
 - <b>`path`</b>:  Filesystem path to the SQLite file. Parent directories are  created if missing. 
 - <b>`sqlite_vec_enabled`</b>:  When True, loads the sqlite-vec extension and  creates the vec0 virtual table. Read from config/project.yaml  by callers that know the config; defaults to False. 



**Returns:**
 An open sqlite3.Connection. Caller owns the lifetime. 



**Raises:**
 
 - <b>`RuntimeError`</b>:  If sqlite_vec_enabled is True but the extension  cannot be loaded. 


---

<a href="../src/requirements_agent_tools/db/connection.py#L57"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `bootstrap`

```python
bootstrap(conn: 'Connection', sqlite_vec_enabled: 'bool' = False) → None
```

Create tables and seed reference data if absent. 

Safe to call on an already-bootstrapped database. 



**Args:**
 
 - <b>`conn`</b>:  An open SQLite connection. 
 - <b>`sqlite_vec_enabled`</b>:  When True, also creates the vec0 virtual table. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
