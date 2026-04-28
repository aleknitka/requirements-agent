"""SQLite persistence layer for the requirements agent.

The package is split into focused submodules. Import the symbols you need
directly from the relevant submodule rather than the top-level package:

    from requirements_agent_tools.db.connection   import get_db, bootstrap
    from requirements_agent_tools.db.projects     import upsert_project, get_project
    from requirements_agent_tools.db.requirements import (
        insert_requirement, update_requirement, get_requirement,
        search_requirements,
    )
    from requirements_agent_tools.db.embeddings   import embed, vector_search
    from requirements_agent_tools.db.updates      import get_updates
    from requirements_agent_tools.db.minutes      import (
        insert_minute, get_minute, list_minutes, mark_integrated, list_decisions,
    )

Importing the package configures loguru's stderr sink once at INFO. A
per-project daily-rotated DEBUG file sink at
``projects/<slug>/logs/db-{date}.log`` is added the first time
``get_db()`` opens that project's database.
"""

from __future__ import annotations

from ._logging import configure_logging

configure_logging()
