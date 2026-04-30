<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/init_project.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.init_project`
init_project.py — project initialisation. 

Commands 
--------  setup    Create project/ directory tree, bootstrap DB, write config/project.yaml 


---

<a href="../src/requirements_agent_tools/init_project.py#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_setup`

```python
cmd_setup(args: 'Namespace') → None
```

Create the project directory, bootstrap the DB, and write setup config. 

Asks three interactive questions:  1. Enable vector embeddings (sqlite-vec)?  [default: no]  2. Enable OpenTelemetry tracing flag?       [default: no]  3. Append project/logs/, project/notes/, project/*.db to .gitignore? 

Writes ``config/project.yaml`` with the setup choices. Creates the ``project/`` directory with ``logs/`` and ``notes/`` subdirectories. Bootstraps ``project/project.db`` with the canonical schema. 

Exits non-zero (code 1) if ``PROJECT_DIR`` already exists — use ``init-project reset`` (not yet implemented) to start fresh. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/init_project.py#L111"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `build_parser`

```python
build_parser() → ArgumentParser
```

Build and return the init-project argument parser. 



**Returns:**
  Configured ArgumentParser with the setup subcommand. 


---

<a href="../src/requirements_agent_tools/init_project.py#L123"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main() → None
```

Entry point for the init-project CLI. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
