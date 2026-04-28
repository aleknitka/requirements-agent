<!-- markdownlint-disable -->

<a href="../src/requirements_agent_tools/db/cli.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `requirements_agent_tools.db.cli`
Click CLI exposing full CRUD over a project database. 

Each subcommand opens the SQLite file at ``projects/<slug>/<slug>.db``, runs one operation, and prints the result as JSON to stdout. Errors are logged via loguru and surfaced as a non-zero exit code. 



**Examples:**
  db --project demo project show  db --project demo req add --title "..." --by alice  db --project demo req search --status open --priority high  db --project demo req vec-search "fault tolerance" --top-k 5  db --project demo minute list --unintegrated 





---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
