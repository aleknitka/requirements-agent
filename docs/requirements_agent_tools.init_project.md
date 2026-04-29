<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/init_project.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.init_project`
init.py — project initialisation. 

Commands ────────  new      Interview user → create <slug>.db + PROJECT.md  list     List all existing projects  update   Update metadata fields for an existing project 


---

<a href="../src/requirements_agent_tools/init_project.py#L24"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_new`

```python
cmd_new(args: Namespace) → None
```

Create a new project database and directory. 

Validates that no project with the same slug already exists, then creates the DB, writes project metadata, and prints a JSON result with the project ID, slug, and next-step instructions. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/init_project.py#L82"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_list`

```python
cmd_list(args: Namespace) → None
```

List all existing projects found in PROJECTS_DIR. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/init_project.py#L101"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_update`

```python
cmd_update(args: Namespace) → None
```

Update metadata fields for an existing project. 

Resolves the project by slug or name, applies all non-None CLI argument values to the project metadata, and persists the change. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/init_project.py#L149"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `build_parser`

```python
build_parser() → ArgumentParser
```

Build and return the init-project argument parser. 



**Returns:**
  Configured ArgumentParser with new, list, and update subcommands. 


---

<a href="../src/requirements_agent_tools/init_project.py#L198"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main()
```

Entry point for the init-project CLI. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
