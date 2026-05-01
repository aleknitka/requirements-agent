<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/review.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.review`
review.py — requirements gap analysis, conflict detection, coverage checks. 

Commands ────────  gaps       Identify missing requirement types, incomplete fields, no-FRET items  conflicts  Flag potential conflicts (same component, opposing conditions/timings)  coverage   Cross-check requirements against success criteria  report     Full review report (runs all checks, outputs structured summary) 


---

<a href="../src/requirements_agent_tools/review.py#L223"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_gaps`

```python
cmd_gaps(args)
```

Run gap analysis and output identified issues as JSON. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/review.py#L235"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_conflicts`

```python
cmd_conflicts(args)
```

Run conflict detection and output flagged conflicts as JSON. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/review.py#L246"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_coverage`

```python
cmd_coverage(args)
```

Run success criteria coverage check and output results as JSON. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/review.py#L258"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_report`

```python
cmd_report(args)
```

Run all review checks and output a combined review report as JSON. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/review.py#L303"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `build_parser`

```python
build_parser()
```

Build and return the review argument parser. 



**Returns:**
  Configured ArgumentParser with gaps, conflicts, coverage,  and report subcommands. 


---

<a href="../src/requirements_agent_tools/review.py#L326"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main()
```

Entry point for the review CLI. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
