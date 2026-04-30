<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/__init__.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db`
SQLite persistence layer for the requirements agent. 

The package is split into focused submodules. Import the symbols you need directly from the relevant submodule rather than the top-level package: 

 from requirements_agent_tools.db.connection   import get_db, bootstrap  from requirements_agent_tools.db.projects     import upsert_project, get_project  from requirements_agent_tools.db.requirements import (  insert_requirement, update_requirement, get_requirement,  search_requirements,  )  from requirements_agent_tools.db.embeddings   import embed, vector_search  from requirements_agent_tools.db.updates      import get_updates  from requirements_agent_tools.db.issues       import (  insert_issue, get_issue, search_issues, update_issue,  ) 

Importing the package configures loguru's stderr sink once at INFO. A per-project daily-rotated DEBUG file sink at ``projects/<slug>/logs/db-{date}.log`` is added the first time ``get_db()`` opens that project's database. 





---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
