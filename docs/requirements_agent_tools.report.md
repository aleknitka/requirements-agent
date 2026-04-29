<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/report.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.report`
report.py — generate a structured project status report. 

Commands ────────  generate   Pull current state from DB and produce a status report (JSON + MD)  save       Write the report to a timestamped file alongside PROJECT.md 


---

<a href="../src/requirements_agent_tools/report.py#L215"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_generate`

```python
cmd_generate(args)
```

Generate a project status report and print it to stdout. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/report.py#L230"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_save`

```python
cmd_save(args)
```

Generate a project status report and save it to timestamped files. 

Writes both a Markdown file (STATUS-<timestamp>.md) and a JSON file (STATUS-<timestamp>.json) to the project directory. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/report.py#L257"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `build_parser`

```python
build_parser()
```

Build and return the report argument parser. 



**Returns:**
  Configured ArgumentParser with generate and save subcommands. 


---

<a href="../src/requirements_agent_tools/report.py#L274"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main()
```

Entry point for the report CLI. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
