<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/project_session.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.project_session`
project_session.py — shared helper for resolving the active project. 

Every skill calls `resolve(slug_or_name)` at the start of its session. Pass an explicit slug via --project <slug>. Auto-selection via .active sentinel will be added in Phase 1 (INIT-06). 

PROJECT.md is owned by the skill: write through ``project_md_cli`` (or call ``project_md.save`` / ``append_section`` directly). There is no auto-refresh. 


---

<a href="../src/requirements_agent_tools/project_session.py#L24"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `resolve`

```python
resolve(
    slug_or_name: 'Optional[str]' = None
) → tuple[str, Connection, ProjectMeta]
```

Resolve which project to work on. Returns (slug, conn, meta). 

Phase 0: requires explicit slug_or_name. Auto-selection via .active sentinel is implemented in Phase 1 (INIT-06). 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
