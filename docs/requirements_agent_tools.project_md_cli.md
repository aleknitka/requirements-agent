<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/project_md_cli.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.project_md_cli`
project_md_cli.py — persist skill-authored PROJECT.md content with audit. 

Commands ────────  save     Write the full markdown body (creates or replaces the file)  append   Append a section to the existing PROJECT.md  read     Print the current PROJECT.md to stdout 


---

<a href="../src/requirements_agent_tools/project_md_cli.py#L48"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_save`

```python
cmd_save(args: 'Namespace') → None
```

Write the full PROJECT.md content, creating or replacing the file. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/project_md_cli.py#L62"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_append`

```python
cmd_append(args: 'Namespace') → None
```

Append a markdown section to the existing PROJECT.md. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/project_md_cli.py#L85"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_read`

```python
cmd_read(args: 'Namespace') → None
```

Print the current PROJECT.md content to stdout. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/project_md_cli.py#L98"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `build_parser`

```python
build_parser() → ArgumentParser
```

Build and return the project-md-cli argument parser. 



**Returns:**
  Configured ArgumentParser with save, append, and read subcommands. 


---

<a href="../src/requirements_agent_tools/project_md_cli.py#L129"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main() → None
```

Entry point for the project_md_cli CLI. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
