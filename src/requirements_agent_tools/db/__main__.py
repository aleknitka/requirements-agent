"""Allow ``python -m requirements_agent_tools.db`` to dispatch the click CLI."""

from .cli import cli

if __name__ == "__main__":
    cli()
