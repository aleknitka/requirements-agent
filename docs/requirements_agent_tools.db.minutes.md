<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/minutes.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.minutes`
Meeting minutes, decisions, and action items. 


---

<a href="../src/requirements_agent_tools/db/minutes.py#L15"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `insert_minute`

```python
insert_minute(conn: 'Connection', minute_in: 'MinuteIn') → MinuteRow
```

Insert one meeting record. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`minute_in`</b>:  Validated meeting input. 



**Returns:**
 
 - <b>`The reloaded `</b>: class:`MinuteRow` with its assigned id. 


---

<a href="../src/requirements_agent_tools/db/minutes.py#L63"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_minute`

```python
get_minute(conn: 'Connection', minute_id: 'str') → Optional[MinuteRow]
```

Return one meeting by id, or ``None`` if missing. 


---

<a href="../src/requirements_agent_tools/db/minutes.py#L69"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `list_minutes`

```python
list_minutes(
    conn: 'Connection',
    source: 'Optional[str]' = None,
    unintegrated: 'bool' = False,
    since: 'Optional[str]' = None
) → list[MinuteRow]
```

List meetings ordered by ``occurred_at`` ascending. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`source`</b>:  Filter by meeting source enum value. 
 - <b>`unintegrated`</b>:  If ``True``, only meetings whose decisions/actions  have not yet been integrated into the project status. 
 - <b>`since`</b>:  ISO date/datetime string. Only meetings on/after this  instant are returned. 



**Returns:**
 
 - <b>`A list of `</b>: class:`MinuteRow`. 


---

<a href="../src/requirements_agent_tools/db/minutes.py#L106"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `mark_integrated`

```python
mark_integrated(conn: 'Connection', minute_id: 'str') → MinuteRow
```

Flag a meeting as integrated into the project status. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`minute_id`</b>:  Meeting identifier. 



**Returns:**
 
 - <b>`The reloaded `</b>: class:`MinuteRow`. 


---

<a href="../src/requirements_agent_tools/db/minutes.py#L129"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `list_decisions`

```python
list_decisions(
    conn: 'Connection',
    status: 'Optional[str]' = None,
    affects_req: 'Optional[str]' = None
) → list[dict]
```

Return a flat list of decisions across every meeting. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`status`</b>:  Optional decision-status enum value to filter on. 
 - <b>`affects_req`</b>:  Optional requirement id; only decisions whose  ``affects_reqs`` list contains this id are returned. 



**Returns:**
 A list of dicts with the decision fields plus ``meeting_id`` and ``meeting_title`` from the parent minute. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
