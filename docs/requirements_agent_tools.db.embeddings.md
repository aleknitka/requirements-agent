<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/embeddings.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.embeddings`
Embedding generation, persistence, and vector search. 


---

<a href="../src/requirements_agent_tools/db/embeddings.py#L15"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `embed`

```python
embed(text: 'str') → list[float]
```

Embed ``text`` with the configured OpenAI-compatible endpoint. 



**Args:**
 
 - <b>`text`</b>:  The text to embed. 



**Returns:**
 
 - <b>`A list of floats of length `</b>: data:`CONSTANTS.EMBEDDING_DIM`. 



**Raises:**
 
 - <b>`RuntimeError`</b>:  If ``EMBEDDING_API_KEY`` is unset or the ``openai``  package is not installed. 


---

<a href="../src/requirements_agent_tools/db/embeddings.py#L46"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `store_embedding`

```python
store_embedding(
    conn: 'Connection',
    req_id: 'str',
    title: 'str',
    description: 'str'
) → None
```

Generate and upsert an embedding for one requirement. 

Silently skips when no API key is configured. Embedding failures are logged as warnings but do not propagate — the row is already persisted. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`req_id`</b>:  Requirement identifier. 
 - <b>`title`</b>:  Requirement title. 
 - <b>`description`</b>:  Requirement description. 


---

<a href="../src/requirements_agent_tools/db/embeddings.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `vector_search`

```python
vector_search(
    conn: 'Connection',
    query_text: 'str',
    top_k: 'int' = 10
) → list[tuple[RequirementRow, float]]
```

Return the ``top_k`` requirements closest to ``query_text``. 



**Args:**
 
 - <b>`conn`</b>:  Open DB connection. 
 - <b>`query_text`</b>:  Free-form query string; will be embedded with the  configured model. 
 - <b>`top_k`</b>:  Maximum number of hits to return. 



**Returns:**
 ``(RequirementRow, distance)`` tuples sorted by ascending distance. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
