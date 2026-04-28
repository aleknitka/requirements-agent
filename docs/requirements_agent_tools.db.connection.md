<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/connection.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.connection`
Connection lifecycle: open/close DB files and apply schema migrations. 


---

<a href="../src/requirements_agent_tools/db/connection.py#L14"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_db`

```python
get_db(path: 'str') → Connection
```

Open (or create) a SQLite database and load ``sqlite-vec``. 

The connection is configured with WAL journaling, FK enforcement, and ``Row`` factory before bootstrap runs. 



**Args:**
 
 - <b>`path`</b>:  Filesystem path to the SQLite file. Parent directories are  created if missing. 



**Returns:**
 
 - <b>`An open `</b>: class:`sqlite3.Connection`. Caller owns the lifetime. 



**Raises:**
 
 - <b>`RuntimeError`</b>:  If the ``sqlite-vec`` extension cannot be loaded. 


---

<a href="../src/requirements_agent_tools/db/connection.py#L53"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `bootstrap`

```python
bootstrap(conn: 'Connection') → None
```

Create tables and seed reference data if absent. 

Safe to call on an already-bootstrapped database. Also performs the one-shot ``ADD COLUMN slug`` migration for legacy DBs. 



**Args:**
 
 - <b>`conn`</b>:  An open SQLite connection with ``sqlite-vec`` loaded. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
