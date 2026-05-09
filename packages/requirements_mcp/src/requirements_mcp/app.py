"""Gradio Blocks app exposing every MCP tool over UI + MCP-over-SSE.

When launched with ``mcp_server=True``, Gradio inspects every API
endpoint registered on the Blocks app — including those created via
:func:`gradio.api` — and exposes each as an MCP tool. The tool name
comes from the ``api_name`` argument (or the function name when
omitted), the description from the function docstring, and the
parameter / return types from the function's type hints.

Concretely: the seventeen plain-Python functions in
:mod:`requirements_mcp.tools.requirements` and
:mod:`requirements_mcp.tools.issues` are bound here in one place. There
is no parallel registration for stdio MCP — the same function powers
both the (future) UI buttons and the MCP endpoint.

Run via the ``requirements-mcp-server`` console script:

.. code-block:: bash

   uv run --package requirements-mcp \\
     requirements-mcp-server --db ./data/requirements.db --no-init
"""

from __future__ import annotations

import argparse
import inspect
from typing import Callable, Sequence

import gradio as gr
from loguru import logger
from sqlalchemy.orm import Session, sessionmaker

from requirements_mcp.config import resolve_db_path
from requirements_mcp.db.engine import make_engine, make_session_factory
from requirements_mcp.db.init import init_db
from requirements_mcp.logging import configure_logging
from requirements_mcp.schemas.issues import (
    IssueCreate,
    IssueOut,
    IssuePriorityOut,
    IssueSearchHit,
    IssueSearchQuery,
    IssueStatusOut,
    IssueTypeOut,
    IssueUpdate,
    IssueUpdateAdd,
    IssueUpdateOut,
    RequirementIssueLinkCreate,
    RequirementIssueLinkOut,
)
from requirements_mcp.schemas.requirements import (
    RequirementChangeOut,
    RequirementCreate,
    RequirementOut,
    RequirementSearchHit,
    RequirementSearchQuery,
    RequirementStatusOut,
    RequirementTypeOut,
    RequirementUpdate,
)
from requirements_mcp.tools import issues as issue_tools
from requirements_mcp.tools import requirements as req_tools
from requirements_mcp.ui import (
    build_audit_tab,
    build_issues_tab,
    build_metadata_tab,
    build_requirements_tab,
)

__all__ = ["REGISTERED_TOOLS", "build_app", "main"]

APP_TITLE = "Requirements Agent"

REGISTERED_TOOLS: tuple[str, ...] = (
    # Phase 2 — requirements
    "create_requirement",
    "update_requirement",
    "get_requirement",
    "search_requirements",
    "list_requirement_changes",
    "list_requirement_statuses",
    "list_requirement_types",
    # Phase 3 — issues
    "create_issue",
    "update_issue",
    "get_issue",
    "search_issues",
    "list_issue_updates",
    "list_open_issues",
    "list_blocking_issues",
    "add_issue_update",
    "link_issue_to_requirement",
    "unlink_issue_from_requirement",
)
"""Names of every MCP tool exposed by :func:`build_app`.

Tests assert this set against the introspected Gradio app to detect
drift.
"""


def _bind(
    fn: Callable[..., object],
    session_factory: sessionmaker[Session],
    *,
    name: str,
) -> Callable[..., object]:
    """Return a wrapper of ``fn`` with the session factory pre-bound.

    Gradio introspects callables to derive the API JSON schema and the
    MCP tool name + description. ``functools.partial`` does not produce
    a cleanly inspectable callable in this context, so we build a small
    wrapper that explicitly carries:

    * a synthesised ``__signature__`` with the leading
      ``session_factory`` parameter removed,
    * the caller-supplied ``__name__`` (used by Gradio as the MCP tool
      name; the ``api_name=`` argument to :func:`gradio.api` controls
      only the URL path),
    * the original ``__doc__`` and ``__annotations__`` (minus the
      dropped parameter),

    so that Gradio sees only the application-facing parameters and the
    public tool name.

    Args:
        fn: A tool wrapper from :mod:`requirements_mcp.tools.*` whose
            first parameter is the session factory.
        session_factory: The factory built from the resolved database
            path.
        name: The public name of the tool. Becomes ``wrapper.__name__``
            and therefore the name advertised over MCP.

    Returns:
        A callable Gradio can introspect, invokable as
        ``bound(*remaining_args, **kwargs)``.
    """
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    if not params:
        fn_name = getattr(fn, "__name__", repr(fn))
        raise TypeError(f"{fn_name} has no parameters to bind")
    new_sig = sig.replace(parameters=params[1:])
    annotations = {
        ann_name: ann
        for ann_name, ann in getattr(fn, "__annotations__", {}).items()
        if ann_name != params[0].name
    }

    def wrapper(*args: object, **kwargs: object) -> object:
        """Inner closure that calls ``fn`` with the bound ``session_factory``."""
        return fn(session_factory, *args, **kwargs)

    # Mutate function attributes via ``setattr`` so Gradio's introspection
    # sees the public-facing name and signature. ``setattr`` is used in
    # preference to direct dotted assignment because ``__signature__`` is
    # not declared on plain function objects in static type checkers.
    setattr(wrapper, "__name__", name)
    setattr(wrapper, "__qualname__", name)
    wrapper.__doc__ = fn.__doc__
    setattr(wrapper, "__module__", fn.__module__)
    wrapper.__annotations__ = annotations
    setattr(wrapper, "__signature__", new_sig)
    return wrapper


def build_app(session_factory: sessionmaker[Session]) -> gr.Blocks:
    """Construct the Gradio Blocks app with all 17 tools registered.

    Each tool is exposed via :func:`gradio.api`, which surfaces a
    pure-API endpoint that Gradio's MCP server publishes when launched
    with ``mcp_server=True``. The function signatures come straight
    from :mod:`requirements_mcp.tools.requirements` and
    :mod:`requirements_mcp.tools.issues`, with the leading
    ``session_factory`` argument bound away by :func:`_bind`.

    The UI surface is composed from per-subsystem tab builders in
    :mod:`requirements_mcp.ui`. Tab handlers reuse the same
    :mod:`requirements_mcp.tools` wrappers as the API endpoints, but
    are registered without ``api_name`` so they do not double-publish
    over MCP. The MCP-tool surface is therefore exactly the seventeen
    :func:`gradio.api` registrations declared in this function.

    Args:
        session_factory: Factory bound to the resolved database.

    Returns:
        A :class:`gradio.Blocks` instance ready to ``.launch(...)``.
    """
    with gr.Blocks(title=APP_TITLE) as app:
        gr.Markdown(f"# {APP_TITLE}")
        gr.Markdown(
            "MCP-enabled requirements management. "
            f"{len(REGISTERED_TOOLS)} tools exposed via the API and "
            "MCP-over-SSE endpoint at `/gradio_api/mcp/sse`."
        )

        # MCP / API surface: one registration per tool. Tools are NOT
        # also bound to UI handlers here — UI handlers (created by the
        # tab builders below) call the same `tools/*` wrappers but do
        # not get an `api_name`, so they don't re-appear over MCP.
        for fn, public_name in _TOOL_BINDINGS:
            gr.api(
                _bind(fn, session_factory, name=public_name),
                api_name=public_name,
            )

        with gr.Tabs():
            with gr.Tab("Requirements"):
                build_requirements_tab(session_factory)
            with gr.Tab("Issues"):
                build_issues_tab(session_factory)
            with gr.Tab("Audit"):
                build_audit_tab(session_factory)
            with gr.Tab("Metadata"):
                build_metadata_tab(session_factory)

    # UI button/select handlers default to ``api_visibility="public"`` and
    # would surface in the API and MCP tool list with auto-generated names.
    # Mark every endpoint whose ``api_name`` is not in REGISTERED_TOOLS as
    # private so only the canonical seventeen tools appear in the API
    # surface and over MCP.
    _seal_ui_handlers(app)

    return app


def _seal_ui_handlers(app: gr.Blocks) -> None:
    """Mark every non-canonical event handler as private.

    Gradio assigns ``api_visibility="public"`` to every ``Button.click``
    and ``Component.select`` registration by default. Without this pass,
    the UI handlers built by :mod:`requirements_mcp.ui` would auto-name
    themselves and appear in ``app.get_api_info()["named_endpoints"]``,
    inflating the MCP tool list. We walk the registered dependencies
    and flip everything that doesn't carry one of the canonical tool
    names to ``"private"``, so the MCP surface remains exactly the
    seventeen :func:`gradio.api` registrations.
    """
    canonical = set(REGISTERED_TOOLS)
    for dep in app.fns.values():
        if dep.api_name not in canonical:
            dep.api_visibility = "private"


# Top-level wrappers for each tool. Defined here (rather than directly
# referencing the ``tools/`` module functions) so each one carries an
# application-facing docstring and a clean signature without the
# ``session_factory`` first parameter. Gradio introspects these
# signatures to derive both the JSON schema and the MCP tool
# description.


def _create_requirement(
    session_factory: sessionmaker[Session],
    payload: RequirementCreate,
) -> RequirementOut:
    """Create a new requirement and return its full state."""
    return req_tools.create_requirement(session_factory, payload)


def _update_requirement(
    session_factory: sessionmaker[Session],
    requirement_id: str,
    payload: RequirementUpdate,
) -> RequirementOut:
    """Apply changes to a requirement; logs an audit row when fields change."""
    return req_tools.update_requirement(session_factory, requirement_id, payload)


def _get_requirement(
    session_factory: sessionmaker[Session],
    requirement_id: str,
) -> RequirementOut | None:
    """Return one requirement by id, or null if not found."""
    return req_tools.get_requirement(session_factory, requirement_id)


def _search_requirements(
    session_factory: sessionmaker[Session],
    query: RequirementSearchQuery,
) -> list[RequirementSearchHit]:
    """Search requirements by free text and optional code filters."""
    return req_tools.search_requirements(session_factory, query)


def _list_requirement_changes(
    session_factory: sessionmaker[Session],
    requirement_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[RequirementChangeOut]:
    """Return the audit log for one requirement, oldest first."""
    return req_tools.list_requirement_changes(
        session_factory, requirement_id, limit=limit, offset=offset
    )


def _list_requirement_statuses(
    session_factory: sessionmaker[Session],
) -> list[RequirementStatusOut]:
    """Return every requirement status ordered by sort_order."""
    return req_tools.list_requirement_statuses(session_factory)


def _list_requirement_types(
    session_factory: sessionmaker[Session],
) -> list[RequirementTypeOut]:
    """Return every requirement type ordered by sort_order."""
    return req_tools.list_requirement_types(session_factory)


def _create_issue(
    session_factory: sessionmaker[Session],
    payload: IssueCreate,
) -> IssueOut:
    """Create a new issue and return its full state."""
    return issue_tools.create_issue(session_factory, payload)


def _update_issue(
    session_factory: sessionmaker[Session],
    issue_id: str,
    payload: IssueUpdate,
) -> IssueOut:
    """Apply changes to an issue; logs an audit row when fields change."""
    return issue_tools.update_issue(session_factory, issue_id, payload)


def _get_issue(
    session_factory: sessionmaker[Session],
    issue_id: str,
) -> IssueOut | None:
    """Return one issue by id, or null if not found."""
    return issue_tools.get_issue(session_factory, issue_id)


def _search_issues(
    session_factory: sessionmaker[Session],
    query: IssueSearchQuery,
) -> list[IssueSearchHit]:
    """Search issues by free text and optional code/owner filters."""
    return issue_tools.search_issues(session_factory, query)


def _list_issue_updates(
    session_factory: sessionmaker[Session],
    issue_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[IssueUpdateOut]:
    """Return the audit log for one issue, oldest first."""
    return issue_tools.list_issue_updates(
        session_factory, issue_id, limit=limit, offset=offset
    )


def _list_open_issues(
    session_factory: sessionmaker[Session],
) -> list[IssueOut]:
    """Return every issue in a non-terminal status."""
    return issue_tools.list_open_issues(session_factory)


def _list_blocking_issues(
    session_factory: sessionmaker[Session],
) -> list[IssueOut]:
    """Return every non-terminal blocker (issue type 'BLK')."""
    return issue_tools.list_blocking_issues(session_factory)


def _add_issue_update(
    session_factory: sessionmaker[Session],
    issue_id: str,
    payload: IssueUpdateAdd,
) -> IssueUpdateOut:
    """Append an action-log entry to an issue without mutating its fields."""
    return issue_tools.add_issue_update(session_factory, issue_id, payload)


def _link_issue_to_requirement(
    session_factory: sessionmaker[Session],
    issue_id: str,
    payload: RequirementIssueLinkCreate,
) -> RequirementIssueLinkOut:
    """Create a typed link between an issue and a requirement."""
    return issue_tools.link_issue_to_requirement(session_factory, issue_id, payload)


def _unlink_issue_from_requirement(
    session_factory: sessionmaker[Session],
    issue_id: str,
    requirement_id: str,
    author: str,
    rationale: str = "",
) -> None:
    """Remove the link between an issue and a requirement."""
    issue_tools.unlink_issue_from_requirement(
        session_factory,
        issue_id,
        requirement_id,
        author=author,
        rationale=rationale,
    )


def _list_issue_statuses(
    session_factory: sessionmaker[Session],
) -> list[IssueStatusOut]:
    """Return every issue status ordered by sort_order."""
    return issue_tools.list_issue_statuses(session_factory)


def _list_issue_types(
    session_factory: sessionmaker[Session],
) -> list[IssueTypeOut]:
    """Return every issue type ordered by sort_order."""
    return issue_tools.list_issue_types(session_factory)


def _list_issue_priorities(
    session_factory: sessionmaker[Session],
) -> list[IssuePriorityOut]:
    """Return every issue priority ordered by sort_order."""
    return issue_tools.list_issue_priorities(session_factory)


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the ``requirements-mcp-server`` command.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="requirements-mcp-server",
        description=(
            "Launch the requirements MCP application. Exposes both a "
            "Gradio UI and an MCP-over-SSE endpoint at "
            "/gradio_api/mcp/sse. The same functions back both."
        ),
    )
    parser.add_argument(
        "--db",
        dest="db",
        default=None,
        help=(
            "Path to the SQLite database file. Overrides the "
            "REQUIREMENTS_DB_PATH environment variable. Default: "
            "./data/requirements.db."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Loguru level for stdout and the daily log file. Default: INFO.",
    )
    parser.add_argument(
        "--no-init",
        action="store_true",
        help=(
            "Skip the idempotent init_db call. Use when the database "
            "has already been provisioned by `requirements-db-init`."
        ),
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Address to bind. Default: 127.0.0.1 (loopback).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to listen on. Default: 7860.",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help=(
            "Expose a public Gradio share URL via the Gradio relay. Off "
            "by default; the app is intended to be local."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``requirements-mcp-server`` console script.

    Steps performed at start-up:

    1. Parse arguments.
    2. Configure loguru with stdout + daily file sinks.
    3. Resolve the database path; run :func:`init_db` unless
       ``--no-init`` is passed.
    4. Build the engine and session factory.
    5. Build the Gradio app with all tools registered.
    6. Launch with ``mcp_server=True`` so the MCP-over-SSE endpoint is
       exposed alongside the UI.

    Args:
        argv: Optional argument vector. ``None`` parses ``sys.argv[1:]``.

    Returns:
        ``0`` on a clean shutdown.
    """
    args = _build_parser().parse_args(argv)
    configure_logging(name="requirements_mcp", level=args.log_level)

    resolved = resolve_db_path(args.db)
    if args.no_init:
        logger.info("Skipping init_db (--no-init); using {}", resolved)
    else:
        init_db(resolved)

    engine = make_engine(resolved)
    session_factory = make_session_factory(engine)
    app = build_app(session_factory)
    logger.info(
        "Launching {} at http://{}:{} (MCP at /gradio_api/mcp/sse, db={})",
        APP_TITLE,
        args.host,
        args.port,
        resolved,
    )
    app.launch(
        server_name=args.host,
        server_port=args.port,
        mcp_server=True,
        share=args.share,
        prevent_thread_lock=False,
    )
    return 0


# Tuple of (wrapper function, public MCP/API name) bindings consumed by
# :func:`build_app`. Defined here at the bottom so it can reference all
# the underscore-prefixed wrappers above; ``build_app`` reads it via
# Python's late name resolution at call time.
_TOOL_BINDINGS: tuple[tuple[Callable[..., object], str], ...] = (
    (_create_requirement, "create_requirement"),
    (_update_requirement, "update_requirement"),
    (_get_requirement, "get_requirement"),
    (_search_requirements, "search_requirements"),
    (_list_requirement_changes, "list_requirement_changes"),
    (_list_requirement_statuses, "list_requirement_statuses"),
    (_list_requirement_types, "list_requirement_types"),
    (_create_issue, "create_issue"),
    (_update_issue, "update_issue"),
    (_get_issue, "get_issue"),
    (_search_issues, "search_issues"),
    (_list_issue_updates, "list_issue_updates"),
    (_list_open_issues, "list_open_issues"),
    (_list_blocking_issues, "list_blocking_issues"),
    (_add_issue_update, "add_issue_update"),
    (_link_issue_to_requirement, "link_issue_to_requirement"),
    (_unlink_issue_from_requirement, "unlink_issue_from_requirement"),
)
