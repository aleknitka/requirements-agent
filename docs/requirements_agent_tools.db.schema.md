<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/schema.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.schema`
DDL and reference-data seeding for the per-project SQLite database. 

**Global Variables**
---------------
- **REQUIREMENT_TYPE_METADATA**
- **BASE_SCHEMA_SQL**
- **VEC_SCHEMA_SQL**

---

<a href="../src/requirements_agent_tools/db/schema.py#L243"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `seed_reference_tables`

```python
seed_reference_tables(conn: 'Connection') → None
```

Populate the enum catalogue tables. 

Idempotent: every row is written with INSERT OR REPLACE so calling this on every bootstrap is safe. 



**Args:**
 
 - <b>`conn`</b>:  An open SQLite connection with the schema already created. 


---

<a href="../src/requirements_agent_tools/db/schema.py#L270"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `reindex_fts`

```python
reindex_fts(conn: 'Connection') → None
```

Populate FTS5 virtual tables from base tables if they are empty. 



**Args:**
 
 - <b>`conn`</b>:  Open SQLite connection. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
