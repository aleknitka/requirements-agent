<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/refine.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.refine`
refine.py — interactive FRET requirement refinement. 

Commands ────────  pending   List requirements without a FRET statement  show      Show a requirement with its current FRET status  apply     Write FRET statement + fields to a requirement (after user confirms)  coverage  Show FRET coverage stats across all requirements 


---

<a href="../src/requirements_agent_tools/refine.py#L20"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_pending`

```python
cmd_pending(args)
```

List requirements that still need a FRET statement. 


---

<a href="../src/requirements_agent_tools/refine.py#L45"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_show`

```python
cmd_show(args)
```

Show a requirement with full FRET status for refinement session. 


---

<a href="../src/requirements_agent_tools/refine.py#L67"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_apply`

```python
cmd_apply(args)
```

Write a refined description to a requirement. FRET grammar fields (scope/condition/timing/response) are deferred to Phase 3. For now, only description can be updated via this command. 


---

<a href="../src/requirements_agent_tools/refine.py#L104"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_coverage`

```python
cmd_coverage(args)
```

Show FRET coverage across all requirements. 


---

<a href="../src/requirements_agent_tools/refine.py#L123"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `build_parser`

```python
build_parser()
```






---

<a href="../src/requirements_agent_tools/refine.py#L154"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main()
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
