<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/req_ops.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.req_ops`
req_ops.py — requirement CRUD, search, history. 

Commands: add · update · get · list · search · history · vector 


---

<a href="../src/requirements_agent_tools/req_ops.py#L33"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_add`

```python
cmd_add(args)
```

Add a new requirement to the active project. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/req_ops.py#L71"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_update`

```python
cmd_update(args)
```

Apply a partial field update to an existing requirement. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/req_ops.py#L130"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_get`

```python
cmd_get(args)
```

Fetch and display a single requirement by ID. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/req_ops.py#L143"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_list`

```python
cmd_list(args)
```

List all requirements with optional field filters. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/req_ops.py#L181"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_search`

```python
cmd_search(args)
```

Keyword search across requirement titles and descriptions. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/req_ops.py#L206"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_history`

```python
cmd_history(args)
```

Display the full change history for a requirement. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/req_ops.py#L232"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `cmd_vector`

```python
cmd_vector(args)
```

Embedding-based similarity search over requirements. 

Requires EMBEDDING_API_KEY environment variable to be set. 



**Args:**
 
 - <b>`args`</b>:  Parsed CLI arguments from build_parser(). 


---

<a href="../src/requirements_agent_tools/req_ops.py#L262"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `build_parser`

```python
build_parser()
```

Build and return the req-ops argument parser. 



**Returns:**
  Configured ArgumentParser with add, update, get, list, search,  history, and vector subcommands. 


---

<a href="../src/requirements_agent_tools/req_ops.py#L329"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `main`

```python
main()
```

Entry point for the req-ops CLI. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
